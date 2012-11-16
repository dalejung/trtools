from rpy.robjects import r

def traceback():
    r['traceback'](max_lines=10)

def func_lineno(func_name):
    cmd = 'as.list(body({0}))'.format(func_name)
    lines = str(r(cmd))
    return lines

def trace(what, tracer, at):
    cmd = 'trace("{0}",{1}, at={2})'.format(what, tracer, at)
    r(cmd)

def untrace(what):
    cmd = 'untrace("{0}")'.format(what)
    r(cmd)
