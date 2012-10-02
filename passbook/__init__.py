from models import *

VERSION = ('0', '3', '0dev')

def get_version(*args, **kwargs):
    return '.'.join(VERSION)

__version__ = get_version()
