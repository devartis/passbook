========
Passbook
========

Python library to read/write Apple Passbook (.pkpass) files

Typical usage often looks like this::

    #!/usr/bin/env python

    from passbook.models import Pass

    passfile = Pass()
    passfile.certificate = 'Certificates.p12' # Path to your Pass Certificate (.p12 file)
    passfile.password = '******' # Password for certificate
    passfile.JSON = '{...}' # pass.json contents
    passfile.addFile('images/icon.png') # attached images
    passfile.create() # Create and output the Passbook file (.pkpass) 


Creating Pass Certificates
==========================

TO-DO:

1. First

2. Second. 

Developed by `devartis <http://www.devartis.com>`.
