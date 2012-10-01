from models import *

VERSION = ('0', '2', '0')

def get_version(*args, **kwargs):
    return '.'.join(VERSION)

__version__ = get_version()
