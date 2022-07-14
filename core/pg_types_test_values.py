# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io

# keep integer low to avoidf pg_sleep() blockage
PG_TYPES_TEST_VALUES = {
    # bool: boolean, "true"/"false"
    16: "true",
    1000: "array [true, false]",

    # bytea: variable-length string, binary values escaped
    17: "'randstr'",
    1001: "array ['randstr','randstr']",

    # char: single character
    18: "'r'",
    1002: "array ['r','r']",

    # name: 63-byte type for storing system identifiers
    19: "'randstr'",
    1003: "array ['randstr','randstr']",

    # int8: ~18 digit integer, 8-byte storage
    20: "1",
    1016: "array [1, 1]",

    # int2: -32 thousand to 32 thousand, 2-byte storage
    21: "1",
    1005: "array [1, 2]",

    # int2vector: array of int2, used in system tables, @TODO check
    22: "1",
    1006: "1",

    # int4: -2 billion to 2 billion integer, 4-byte storage
    23: "1",
    1007: "array [1, 2]",

    # regproc: registered procedure, @TODO check
    24: "1",
    1008: "array [1, 2]",

    # text: variable-length string, no limit specified
    25: "'randstr'",
    1009: "array ['randstr','randstr']",

    # oid: object identifier(oid), maximum 4 billion
    26: "1",
    1028: "array [1, 2]",

    # tid: (block, offset), physical location of tuple, @TODO check
    27: "'randstr'",
    1010: "array ['randstr','randstr']",

    # xid: transaction id, @TODO check
    28: "'randstr'",
    1011: "array ['randstr','randstr']",

    # cid: command identifier type, sequence in transaction id, @TODO check
    29: "'randstr'",
    1012: "array ['randstr','randstr']",

    # oidvector: array of oids, used in system tables, @TODO check
    30: "1",
    1013: "1",

    # pg_type, @TODO check
    71: "1",
    210: "1",

    # pg_attribute, @TODO check
    75: "1",
    270: "1",

    # pg_proc, @TODO check
    81: "1",
    272: "1",

    # pg_class, @TODO check
    83: "1",
    273: "1",

    # json: JSON stored as text
    114: "'[true]'",
    199: "array ['[true]','[false]']",

    # xml: XML content
    142: "'<foo />'",
    143: "array ['<foo />','<bar />']",

    # pg_node_tree: string representing an internal node tree, @TODO check
    194: "'randstr'",

    # pg_ndistinct: multivariate ndistinct coefficients, @TODO check
    3361: "'randstr'",

    # pg_dependencies: multivariate dependencies, @TODO check
    3402: "'randstr'",

    # pg_mcv_list: multivariate MCV list, @TODO check
    5017: "'randstr'",

    # pg_ddl_command: internal type for passing CollectedCommand, @TODO check
    32: "1",

    # xid8: full transaction id, @TODO check
    5069: "'randstr'",
    271: "array ['randstr','randstr']",

    # point: geometric point "(x, y)", @TODO check
    600: "1",
    1017: "1",

    # lseg: geometric line segment "(pt1,pt2)", @TODO check
    601: "1",
    1018: "1",

    # path: geometric path "(pt1,...)", @TODO check
    602: "1",
    1019: "1",

    # box: geometric box "(lower left,upper right)", @TODO check
    603: "1",
    1020: "1",

    # polygon: geometric polygon "(pt1,...)", @TODO check
    604: "1",
    1027: "1",

    # line: geometric line, @TODO check
    628: "1",
    629: "1",

    # float4: single-precision floating point number, 4-byte storage
    700: "1.1",
    1021: "array [1.1, 1.2]",

    # float8: double-precision floating point number, 8-byte storage
    701: "1.1",
    1022: "array [1.1, 1.2]",

    # unknown: pseudo-type representing an undetermined type, @TODO check
    705: "1",

    # circle: geometric circle "(center,radius)", @TODO check
    718: "1",
    719: "array [1, 2]",

    # money: monetary amounts, $d,ddd.cc, @TODO check
    790: "1.1",
    791: "array [1.1, 1.2]",

    # macaddr: XX:XX:XX:XX:XX:XX, MAC address
    829: "'01:01:01:02:02:02'",
    1040: "array ['01:01:01:02:02:02','01:01:01:02:02:02']",

    # inet: IP address/netmask, host address, netmask optional
    869: "'10.0.0.1'",
    1041: "array ['10.0.0.1', '10.0.0.2']",

    # cidr: network IP address/netmask, network address
    650: "'10.0.0.1/24'",
    651: "array ['10.0.0.1/24', '10.0.0.1/24']",

    # macaddr8: XX:XX:XX:XX:XX:XX:XX:XX, MAC address
    774: "''01:01:01:02:02:02:03:03''",
    775: "array [''01:01:01:02:02:02:03:03'',''01:01:01:02:02:02:03:03'']",

    # aclitem: access control list, @TODO check
    1033: "'randstr'",
    1034: "array ['randstr','randstr']",

    # bpchar: char(length), blank-padded string, fixed storage length
    1042: "'randstr'",
    1014: "array ['randstr','randstr']",

    # varchar: varchar(length), non-blank-padded string, variable storage length
    1043: "'randstr'",
    1015: "array ['randstr','randstr']",

    # date: date
    1082: "'2022-07-12'",
    1182: "array ['2022-07-12', '2022-07-12']",

    # time: time of day
    1083: "'00:00:00'",
    1183: "array ['00:00:00', '00:00:00']",

    # timestamp: date and time
    1114: "'2022-07-12 00:00:00'",
    1115: "array ['2022-07-12 00:00:00', '2022-07-12 00:00:00']",

    # timestamptz: date and time with time zone
    1184: "'2022-07-12 00:00:00+00'",
    1185: "array ['2022-07-12 00:00:00+00', '2022-07-12 00:00:00+00']",

    # interval: @ <number> <units>, time interval, @TODO check
    1186: "1",
    1187: "1",

    # timetz: time of day with time zone
    1266: "'00:00:00+00'",
    1270: "array ['00:00:00+00', '00:00:00+00']",

    # bit: fixed-length bit string, @TODO check
    1560: "1",
    1561: "1",

    # varbit: variable-length bit string, @TODO check
    1562: "1",
    1563: "1",

    # numeric: numeric(precision, decimal), arbitrary precision number
    1700: "1",
    1231: "array [1, 2]",

    # refcursor: reference to cursor (portal name), @TODO check
    1790: "'randstr'",
    2201: "array ['randstr','randstr']",

    # regprocedure: registered procedure (with args), @TODO check
    2202: "1",
    2207: "array [1, 2]",

    # regoper: registered operator, @TODO check
    2203: "1",
    2208: "array [1, 2]",

    # regoperator: registered operator (with args), @TODO check
    2204: "1",
    2209: "array [1, 2]",

    # regclass: registered class, @TODO check
    2205: "1",
    2210: "array [1, 2]",

    # regcollation: registered collation, @TODO check
    4191: "1",
    4192: "array [1, 2]",

    # regtype: registered type, @TODO check
    2206: "1",
    2211: "array [1, 2]",

    # regrole: registered role, @TODO check
    4096: "1",
    4097: "array [1, 2]",

    # regnamespace: registered namespace, @TODO check
    4089: "1",
    4090: "array [1, 2]",

    # uuid: UUID datatype, @TODO check
    2950: "'randstr'",
    2951: "array ['randstr','randstr']",

    # pg_lsn: PostgreSQL LSN datatype, @TODO check
    3220: "'randstr'",
    3221: "array ['randstr','randstr']",

    # tsvector: text representation for text search, @TODO check
    3614: "'randstr'",
    3643: "array ['randstr','randstr']",

    # gtsvector: GiST index internal text representation for text search, @TODO check
    3642: "'randstr'",
    3644: "array ['randstr','randstr']",

    # tsquery: query representation for text search, @TODO check
    3615: "'randstr'",
    3645: "array ['randstr','randstr']",

    # regconfig: registered text search configuration, @TODO check
    3734: "1",
    3735: "array [1, 2]",

    # regdictionary: registered text search dictionary, @TODO check
    3769: "1",
    3770: "array [1, 2]",

    # jsonb: Binary JSON, @TODO check
    3802: "'randstr'",
    3807: "array ['randstr','randstr']",

    # jsonpath: JSON path, @TODO check
    4072: "'randstr'",
    4073: "array ['randstr','randstr']",

    # txid_snapshot: txid snapshot, @TODO check
    2970: "'randstr'",
    2949: "array ['randstr','randstr']",

    # pg_snapshot: snapshot, @TODO check
    5038: "'randstr'",
    5039: "array ['randstr','randstr']",

    # int4range: range of integers, @TODO check
    3904: "1",
    3905: "1",

    # numrange: range of numerics, @TODO check
    3906: "1",
    3907: "1",

    # tsrange: range of timestamps without time zone, @TODO check
    3908: "1",
    3909: "1",

    # tstzrange: range of timestamps with time zone, @TODO check
    3910: "1",
    3911: "1",

    # daterange: range of dates, @TODO check
    3912: "1",
    3913: "1",

    # int8range: range of bigints, @TODO check
    3926: "1",
    3927: "1",

    # int4multirange: multirange of integers, @TODO check
    4451: "1",
    6150: "1",

    # nummultirange: multirange of numerics, @TODO check
    4532: "1",
    6151: "1",

    # tsmultirange: multirange of timestamps without time zone, @TODO check
    4533: "1",
    6152: "1",

    # tstzmultirange: multirange of timestamps with time zone, @TODO check
    4534: "1",
    6153: "1",

    # datemultirange: multirange of dates, @TODO check
    4535: "1",
    6155: "1",

    # int8multirange: multirange of bigints, @TODO check
    4536: "1",
    6157: "1",

    # record: pseudo-type representing any composite type, @TODO check
    2249: "1",

    # _record, @TODO check
    2287: "1",

    # cstring: C-style string, @TODO check
    2275: "1",
    1263: "1",

    # any: pseudo-type representing any type, @TODO check
    2276: "1",

    # anyarray: pseudo-type representing a polymorphic array type
    2277: "array [1, 2]",

    # void: pseudo-type for the result of a function with no real result, @TODO check
    2278: "1",

    # trigger: pseudo-type for the result of a trigger function, @TODO check
    2279: "1",

    # event_trigger: pseudo-type for the result of an event trigger function, @TODO check
    3838: "1",

    # language_handler: pseudo-type for the result of a language handler function, @TODO check
    2280: "1",

    # internal: pseudo-type representing an internal data structure, @TODO check
    2281: "1",

    # anyelement: pseudo-type representing a polymorphic base type, @TODO check
    2283: "1",

    # anynonarray: pseudo-type representing a polymorphic base type that is not an array, @TODO check
    2776: "1",

    # anyenum: pseudo-type representing a polymorphic base type that is an enum, @TODO check
    3500: "1",

    # fdw_handler: pseudo-type for the result of an FDW handler function, @TODO check
    3115: "1",

    # index_am_handler: pseudo-type for the result of an index AM handler function, @TODO check
    325: "1",

    # tsm_handler: pseudo-type for the result of a tablesample method function, @TODO check
    3310: "1",

    # table_am_handler, @TODO check
    269: "1",

    # anyrange: pseudo-type representing a range over a polymorphic base type, @TODO check
    3831: "1",

    # anycompatible: pseudo-type representing a polymorphic common type, @TODO check
    5077: "1",

    # anycompatiblearray: pseudo-type representing an array of polymorphic common type elements
    5078: "array [1, 2]",

    # anycompatiblenonarray: pseudo-type representing a polymorphic common type that is not an array, @TODO check
    5079: "1",

    # anycompatiblerange: pseudo-type representing a range over a polymorphic common type, @TODO check
    5080: "1",

    # anymultirange: pseudo-type representing a polymorphic base type that is a multirange, @TODO check
    4537: "1",

    # anycompatiblemultirange: pseudo-type representing a multirange over a polymorphic common type, @TODO check
    4538: "1",

    # pg_brin_bloom_summary: BRIN bloom summary, @TODO check
    4600: "'randstr'",

    # pg_brin_minmax_multi_summary: BRIN minmax-multi summary, @TODO check
    4601: "'randstr'"
}
