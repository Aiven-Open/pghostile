# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io
from core.constants import Constants


class DBFunction:
    def __init__(self, db, oid, name, params_type, rettype):
        self.db = db
        self.oid = oid
        self.name = name
        self.params_type = params_type
        self.nparams = len(self.params_type)
        self.rettype = rettype
        self.operator = None

    def get_operator(self):
        if self.nparams != 2:
            return None
        qry = f"""
            select * from pg_operator o inner join pg_namespace ns on o.oprnamespace = ns.oid
            where ns.nspname = '{Constants.SOURCE_SCHEMA}'
            and o.oprleft = %s
            and o.oprright = %s
            and o.oprcode = %s
        """

        res = self.db.query(qry, (self.params_type[0], self.params_type[1], self.oid))

        rows = res.fetchall()
        if len(rows) == 0:
            return None

        # @TODO skip for now, there are few cases when a function is mapped to
        # more than one operator. It's the case of '@@' and '@@@' that differ from the commutator
        if len(rows) > 1:
            return None

        self.operator = rows[0]['oprname']
        return rows[0]
