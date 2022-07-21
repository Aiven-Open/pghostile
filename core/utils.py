# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io

from core.pg_types import PG_TYPES
from core.pg_types_test_values import PG_TYPES_TEST_VALUES
from core.constants import Constants
from core.dbfunction import DBFunction


def print_ok(s):
    print(f"\x1b[1;32m{s}\x1b[0m")


def print_err(s):
    print(f"\x1b[1;31m{s}\x1b[0m")


def print_warn(s):
    print(f"\x1b[1;33m{s}\x1b[0m")


def convert_types(types):
    typesarr = [int(i) for i in types]
    cmatrix = {
        # the followings are not for hacking but just to make things work
        # (ie 'internal' cannot be used as input for user-defined func)
        2281: [21],  # internal -> int4
        2275: [25],  # cstring -> text
    }
    cmatrix.update(get_convertion_matrix())
    conv_types = []
    for t in typesarr:
        conv_types.append(cmatrix[t] if t in cmatrix else [t])

    return expand_matrix([conv_types])


def convert_rettype(t):
    t = int(t)
    cmatrix = {
        2281: 21,  # internal -> int4
        2275: 25,  # cstring -> text,
        2283: 25,   # anyelement -> text
        2277: 1009,  # anyarray -> array of text
    }

    return cmatrix[t] if t in cmatrix else t


def get_convertion_matrix():
    return {
        701: [1700, 23],  # float8 -> numeric and int
        1700: [23],  # numeric -> int4
        2276: [23, 700, 25],  # any -> integer or float or text
        2283: [23, 700, 25],  # anyelement -> integer or float or text
        5077: [23, 700, 25],  # anycompatible -> integer or float or text
        2277: [1007, 1021, 1009],  # anyarray -> int or float or or text array
        26: 23,  # oid -> int4
        27: 25,  # tid -> text
        28: 25,  # xid -> text
        29: 25,  # cid -> text
        2950: 25,  # UID -> text
        3614: 25,  # tsvector -> text
        3642: 25,  # gtsvector -> text
        3615: 25,  # tsquery -> text
        3734: 25,  # regconfig -> text
        3769: 25,  # regdictionary -> text
        1043: 25,  # varchar -> text
        1042: 25,  # char(n) -> text
        18: 25,  # "char" (with quotes) -> text
        17: 25,  # bytea -> text,
        19: 25,  # name -> text,
        1082: 25,  # date -> text (yes, text has precedence over date ;))
        1114: 25,  # timestamp -> text
        1184: 25,  # timestamptz -> text
        1083: 25,  # time -> text
        1266: 25,  # timetz -> text
        114: 25,  # json -> text,
        142: 25,  # xml -> text
        3802: 25,  # jsonb -> text,
        4072: 25,  # jsonpath -> text,
        # @TODO add more text types (ie pg_node_tree etc)
        829: 25,  # macaddr -> text
        869: 25,  # inet -> text
        650: 25,  # cidr -> text
        774: 25,  # macaddr8 -> text
    }


def get_test_value_for_type(oid):
    return PG_TYPES_TEST_VALUES[int(oid)]


def get_pg_type(oid):
    for t in PG_TYPES:
        if t['oid'] == str(oid):
            return t


def get_pg_types_by_category(cat):
    ret = []
    for t in PG_TYPES:
        if t['typcategory'] == cat:
            ret.append([t['oid'], t['typname'], t['descr']])

    return ret


def pgtype_get_names_map():
    pg_type_names = {int(t['oid']): t['typname'] for t in PG_TYPES}
    for t in PG_TYPES:
        if 'array_type_oid' in t:
            pg_type_names[int(t['array_type_oid'])] = f"{t['typname']} ARRAY"

    return pg_type_names


def get_candidate_functions(db):
    defined_functions = []

    argtypes_filter = [f"{oid} = any(p.proargtypes)" for oid in get_convertion_matrix().keys()]
    qry = """
        SELECT p.oid as oid, n.nspname as ns, p.proname as name, p.pronargs as nargs, p.proargtypes as argtypes, p.prorettype as rettype
        FROM pg_catalog.pg_namespace n JOIN pg_catalog.pg_proc p ON p.pronamespace = n.oid
        WHERE p.prokind = 'f' and p.pronargs > 0 and n.nspname = '%s' and (
            %s
        )
    """ % (Constants.SOURCE_SCHEMA, " or ".join(argtypes_filter))

    res = db.query(qry)

    for row in res.fetchall():
        initial_types = [int(i) for i in row['argtypes'].split()]
        df = DBFunction(db, row['oid'], row['name'], initial_types, row['rettype'])
        defined_functions.append(df)
    return defined_functions


def expand_matrix(arr):
    """
        takes an array like:
        [
            [1, [2,3], 4, [5,6,7]]
        ]
        and returns all the combinations:
        [
            [1, 2, 4, 5]
            [1, 2, 4, 6]
            [1, 2, 4, 7]
            [1, 3, 4, 5]
            [1, 3, 4, 6]
            [1, 3, 4, 7]
        ]
    """
    ret = []
    for el in arr:
        expanded = []
        for i in range(0, len(el)):
            if isinstance(el[i], list):
                for e in el[i]:
                    expanded.append(el[:i] + [e] + el[i + 1:])
                break
        if len(expanded) == 0:
            ret.append(el)
        else:
            ret.extend(expand_matrix(expanded))
    return ret
