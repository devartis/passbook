from distutils.core import setup

setup(
    name='Passbook',
    version='0.1.0',
    author='Fernando Aramendi',
    author_email='fernando@devartis.com',
    packages=['passbook', 'passbook.test'],
    url='http://github.com/devartis/passbook/',
    license='LICENSE.txt',
    description='Passbook file generator.',
    long_description=open('README.md').read(),
    install_requires=[
        "M2Crypto >= 0.21.1",
    ],
)
