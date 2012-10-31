VERSION = ('0', '2', '3')

def get_version(*args, **kwargs):
    return '.'.join(VERSION)

__version__ = get_version()
