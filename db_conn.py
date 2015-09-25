import psycopg2
from psycopg2.extensions import QuotedString

from os import readlink, stat
from psycopg2 import ProgrammingError

class db_handle(object):
    def __init__(self, password, username='postgres', host='127.0.0.1', port=5432, dbname='process_db', blacklist=[]):
        self.username = username
        self.host = host
        self.password = password
        self.port = port
        self.dbname = dbname
        self.tablenames = []
        self.keywords = set(["offset", ])
        self.blacklist = blacklist


    def connect(self):
        conn = None
        while not conn:
            try:
                conn = psycopg2.connect(database=self.dbname, user=self.username, password=self.password, host=self.host, port=self.port)
            except psycopg2.OperationalError as e:
                if raw_input("DB: %s doesn't exist.  Create it?(y/n) " % self.dbname).lower() == "y":
                    self.create_db()
                else:
                    exit()
        return conn

    def build_db(self):
        conn = self.connect()
        self.exec_query(conn, "CREATE TABLE user_maps (uid integer PRIMARY KEY, username varchar, groups varchar)", tuple())
        self.exec_query(conn, "CREATE TABLE group_maps (gid integer PRIMARY KEY, gname varchar)", tuple())
        conn.close()

    def get_tables(self, conn):
        cur = conn.cursor()
        cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'""")
        for table in cur.fetchall():
            self.tablenames.append(table[0])

    def create_db(self):
        try:
            conn = psycopg2.connect(database='postgres', user=self.username, password=self.password, host=self.host, port=self.port)
        except psycopg2.OperationalError as e:
            print "Failed to connect to default db 'postgres'.\nCheck config!!\n%s" % str(e)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("CREATE DATABASE " + self.dbname )
        conn.commit()
        cur.close()
        conn.close()

    def exec_query(self, conn, string, arg_tuple):
        if not type(arg_tuple) == tuple:
            raise RuntimeError('Invalid Args for postgres query')
        cur = conn.cursor()
        try:
            cur.execute(string % arg_tuple)
        except ProgrammingError as e:
            if e.message == 'column "none" specified more than once\n':
                print "Unable to database %s. Missing prototype." % arg_tuple[0]
                self.blacklist.append(arg_tuple[0])
                print self.blacklist
                return False
            import pdb; pdb.set_trace()
            return False
        conn.commit()
        cur.close()
        return True

    def check_escape(self, string):
        string = str(string)
        if string.startswith("'") and string.endswith("'"):
            return string
        string = QuotedString(string)
        return string.getquoted()

    def check_keywords(self, query_list):
        matches = self.keywords & set(query_list)
        for match in matches:
            query_list = ["_" + i if i == match else i for i in query_list]
        return query_list


    def insert_syscall(self, conn, call_name, call_arguments, result, pid):
        res = self.create_syscall_table(conn, call_name, call_arguments)
        if not res:
            return
        #print "Inserting ", call_name
        try:
            procname = readlink('/proc/%s/exe' % pid)
            owner = stat('/proc/%s' % pid).st_uid
        except OSError as e:
            procname = "None"
            owner = "None"
        keys   = self.check_keywords ([arg.name for arg in call_arguments]) + ['res', 'procname', 'owner']
        values = [ self.check_escape(arg.text) for arg in call_arguments] + [self.check_escape(result), self.check_escape(procname), self.check_escape(owner)]
        repstr = ", ".join(["%s" for i in range(len(call_arguments) + 3)])
        self.exec_query(conn, "INSERT INTO %s ( " + repstr + " ) VALUES ( " + repstr + " )", tuple( [call_name, ] + keys + values ))

    def create_syscall_table(self, conn, call_name, call_arguments):
        if call_name in self.tablenames:
            return True
        #print "Creating ", call_name
        argnames = [arg.name for arg in call_arguments]
        argnames = self.check_keywords(argnames)
        call_args_names = tuple([call_name,] + argnames + ['res', 'procname', 'owner'] )
        query = ("CREATE TABLE %s (" + "%s varchar, " * (len(call_args_names) -1))[:-2] + ")"
        res = self.exec_query(conn, query, call_args_names )
        #print "Insert of %s %s" % (call_name, res)
        if res:
            self.tablenames.append(call_name)
            return True
        return False

