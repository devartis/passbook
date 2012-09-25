========
Passbook
========

Python library to read/write Apple Passbook (.pkpass) files

Typical usage often looks like this::

    #!/usr/bin/env python

    from passbook.models import Pass, Barcode, BoardingPass

    cardInfo = BoardingPass()
    cardInfo.addPrimaryField('origin', 'EZE', 'Buenos Aires')
    cardInfo.addPrimaryField('destination', 'MDQ', 'Mar del Plata')
    cardInfo.addSecondaryField('gate', 'F12', 'Gate')
    cardInfo.addSecondaryField('date', '08/11/2012 10:22', 'Departure date')
    cardInfo.addBackField('passenger-name', 'Fernando Aramendi', 'Passenger')
    
    passfile = Pass(cardInfo)
    passfile.description = 'Demo pass' 
    passfile.organizationName = 'devartis' 
    passfile.passTypeIdentifier = 'pass.com.devartis.test' 
    passfile.serialNumber = '12345678' 
    passfile.teamIdentifier = 'AGK5BZEN3E'
    passfile.backgroundColor = 'rgb(107,156,196)', 
    passfile.logoText = 'devartis', 
    passfile.locations.append(Location(-34.602569, -58.436011))
    passfile.barcode = Barcode(message = 'Flight-GateF12-ID6643679AH7B')    
    
    passfile.addFile('images/icon.png')
    passfile.addFile('images/icon@2x.png')
    passfile.addFile('images/logo.png')
    passfile.create('certificate.pem', 'key.pem', 'wwdr.pem', '123456') # Create and output the Passbook file (.pkpass) 


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
