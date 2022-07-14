# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io

from core.pg_types import PG_TYPES
from core.pg_types_test_values import PG_TYPES_TEST_VALUES


def print_ok(s):
    print(f"\x1b[1;32m{s}\x1b[0m")


def print_err(s):
    print(f"\x1b[1;31m{s}\x1b[0m")


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

    mlen = max([len(i) for i in conv_types])
    ret = []
    for i in range(0, mlen):
        tmp = []
        for ct in conv_types:
            tmp.append(ct[i] if len(ct) > i else ct[0])
        ret.append(tmp)

    return ret


def convert_rettype(t):
    t = int(t)
    cmatrix = {
        2281: 21,  # internal -> int4
        2275: 25,  # cstring -> text,
        2283: 25   # anyelement -> text
    }

    return cmatrix[t] if t in cmatrix else t


def get_convertion_matrix():
    return {
        701: [1700],  # float8 -> numeric   1ok 1.1ok
        1700: [23],  # numeric -> int4     1ok 1.1FAIL
        2276: [23, 700, 25],  # any -> integer or float or text
        2277: [1007, 1021, 1009],  # anyarray -> int or float or or text array
        1043: [25],  # varchar -> text
        1042: [25],  # char(n) -> text
        18: [25],  # "char" -> text
        17: [25],  # bytea -> text,
        1082: [25],  # date -> text (yes, text has precedence over date ;))
        1114: [25],  # timestamp -> text
        1184: [25],  # timestamptz -> text
        1083: [25],  # time -> text
        1266: [25],  # timetz -> text
        # @TODO add more date types
        114: [25],  # json -> text,
        142: [25],  # xml -> text
        3802: [25],  # jsonb -> text,
        4072: [25],  # jsonpath -> text,
        # @TODO add more text types (ie pg_node_tree etc)
        829: [25],  # macaddr -> text
        869: [25],  # inet -> text
        650: [25],  # cidr -> text
        774: [25],  # macaddr8 -> text
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

