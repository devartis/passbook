VERSION = ('1', '0', '0')

def get_version(*args, **kwargs):
    return '.'.join(VERSION)

__version__ = get_version()
