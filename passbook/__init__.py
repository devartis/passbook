VERSION = ('0', '1', '0', 'dev')

def get_version(*args, **kwargs):
    return '.'.join(VERSION)

__version__ = get_version()
