from strace import SyscallTracer
from db_conn import db_handle
from ptrace.debugger import Application

class Databased_SyscallTracer(SyscallTracer):
    def __init__(self):
        Application.__init__(self)
        # Parse self.options
        self.parseOptions()
        # Setup output (log)
        self.setupLog()
        self.blacklist = [ "setpgid",'rt_sigreturn']

        self.handle = db_handle('sneakypassword', blacklist=self.blacklist)
        conn = self.handle.connect()
        self.handle.get_tables(conn)
        conn.close()

    def displaySyscall(self, syscall):
        name = syscall.name
        text = syscall.format()
        if name in self.blacklist:
            return
        if name == "setuid" or name == "execve" or name == "setpgid":
            print syscall.__dict__['arguments'][0].getText()
        if syscall.result is not None:
            text = "%-40s = %s" % (text, syscall.result_text)
        prefix = []
        if self.options.show_pid:
            prefix.append("[%s]" % syscall.process.pid)
        if self.options.show_ip:
            prefix.append("[%s]" % formatAddress(syscall.instr_pointer))
        if prefix:
            text = ''.join(prefix) + ' ' + text
        conn = self.handle.connect()
        self.handle.insert_syscall(conn, syscall.name, syscall.arguments, syscall.result_text, syscall.process.pid)
        conn.close()

if __name__ == "__main__":
    tracer = Databased_SyscallTracer()
    tracer.main()
