========
Passbook
========

Python library to read/write Apple Passbook (.pkpass) files

Typical usage often looks like this::

    #!/usr/bin/env python

    from passbook.models import Pass, Barcode, StoreCard

    cardInfo = StoreCard()
    cardInfo.addPrimaryField('name', 'John Doe', 'Name')

    organizationName = 'Your organization' 
    passTypeIdentifier = 'pass.com.your.organization' 
    teamIdentifier = 'AGK5BZEN3E'
    
    passfile = Pass(cardInfo, \
        passTypeIdentifier=passTypeIdentifier, \
        organizationName=organizationName, \
        teamIdentifier=teamIdentifier)
    passfile.serialNumber = '1234567' 
    passfile.barcode = Barcode(message = 'Barcode message')    
    passfile.addFile('icon.png', open('images/icon.png', 'r'))
    passfile.addFile('logo.png', open('images/logo.png', 'r'))
    passfile.create('certificate.pem', 'key.pem', 'wwdr.pem', '123456', 'test.pkpass') # Create and output the Passbook file (.pkpass) 


Creating Pass Certificates
==========================

1. First

iOS Provisioning Portal -> Pass Type IDs -> New Pass Type ID
Select pass type id -> Configure (Follow steps and download generated pass.cer file)
Use Keychain tool to export a p12 file (need Apple Root Certificate installed)

2. Second. 

openssl pkcs12 -in "Certificates.p12" -clcerts -nokeys -out certificate.pem 
openssl pkcs12 -in "Certificates.p12" -nocerts -out key.pem 


Developed by `devartis <http://www.devartis.com>`.


Getting WWDR Certificate
==========================

Certificate is available @ http://developer.apple.com/certificationauthority/AppleWWDRCA.cer
It can be easily exported from KeyChain right to .pem
