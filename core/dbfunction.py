# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io


class DBFunction:
    def __init__(self, db, oid, name, params_type, rettype):
        self.oid = oid
        self.db = db
        self.name = name
        self.params_type = params_type
        self.nparams = len(self.params_type)
        self.rettype = rettype
