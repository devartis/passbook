from distutils.core import setup

version = __import__('passbook').__version__
install_requires = open('requirements.txt').readlines(),

setup(
    name='Passbook',
    version=version,
    author='Fernando Aramendi',
    author_email='fernando@devartis.com',
    packages=['passbook', 'passbook.test'],
    url='http://github.com/devartis/passbook/',
    license=open('LICENSE.txt').read(),
    description='Passbook file generator',
    long_description=open('README.md').read(),

    download_url='http://pypi.python.org/packages/source/P/Passbook/Passbook-%s.tar.gz' % version,

    install_requires=install_requires,

    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
