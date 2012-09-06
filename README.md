========
Passbook
========

Python library to read/write Apple Passbook (.pkpass) files

Typical usage often looks like this::

    #!/usr/bin/env python

    from passbook import PKPass

    pkfile = PKPass()
    pkfile.certPath = 'Certificates.p12' # Path to your Pass Certificate (.p12 file)
    pkfile.certPass = '******' # Password for certificate
    pkfile.JSON = '{...}' # pass.json contents
    pkfile.addFile('images/icon.png') # attached images
    pkfile.create() # Create and output the PKPass


Creating Pass Certificates
==========================

TO-DO:

1. First

2. Second. 

Developed by `devartis <http://www.devartis.com>`.