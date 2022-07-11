from core.pg_types import PG_TYPES


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
        18: [25],  # char -> text
        17: [25],  # bytea -> text
    }


def get_test_value_for_type(oid):
    # keep integer low to avoidf pg_sleep() blockage
    test_bool = "true"
    test_int = "1"
    test_float = "1.1"
    test_string = "'a'"
    test_bool_array = "array [true, false]"
    test_int_array = "array [1, 2]"
    test_float_array = "array [1.1, 1.2]"
    test_string_array = "array ['a','a']"

    # ['B', 'bool']
    # ['U', 'bytea']
    # ['Z', 'char']
    # ['S', 'name']
    # ['N', 'int8']
    # ['A', 'int2vector']
    # ['C', 'pg_type']
    # ['P', 'pg_ddl_command']
    # ['G', 'point']
    # ['X', 'unknown']
    # ['I', 'inet']
    # ['D', 'date']
    # ['T', 'interval']
    # ['V', 'bit']
    # ['R', 'int4range']
    soid = str(oid)
    for t in PG_TYPES:
        tparr = t['array_type_oid'] if 'array_type_oid' in t else None
        if soid in {t['oid'], tparr}:
            if t['typcategory'] == 'B':
                return test_bool_array if soid == tparr else test_bool
            elif t['typcategory'] in {'U', 'Z', 'S'}:
                return test_string_array if soid == tparr else test_string
            elif t['typcategory'] in {'N'}:
                if 'typbyval' in t and t['typbyval'] == "FLOAT8PASSBYVAL":
                    return test_float_array if soid == tparr else test_float
                else:
                    return test_int_array if soid == tparr else test_int

    return test_int


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

