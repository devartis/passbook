# Passbook

[![Build Status](https://travis-ci.org/devartis/passbook.svg?branch=master)](https://travis-ci.org/devartis/passbook)

Python library to create Apple Wallet (.pkpass) files (Apple Wallet 
has previously been known as Passbook in iOS 6 to iOS 8).

See the [Wallet Topic Page](https://developer.apple.com/wallet/) and the
[Wallet Developer Guide](https://developer.apple.com/library/ios/documentation/UserExperience/Conceptual/PassKit_PG/index.html#//apple_ref/doc/uid/TP40012195) for more information about Apple Wallet.

> If you need the server side implementation (API / WebServices) in django you should check http://github.com/devartis/django-passbook.


## Getting Started

1) Get a Pass Type Id

* Visit the iOS Provisioning Portal -> Pass Type IDs -> New Pass Type ID
* Select pass type id -> Configure (Follow steps and download generated pass.cer file)
* Use Keychain tool to export a Certificates.p12 file (need Apple Root Certificate installed)

2) Generate the necessary certificate

```shell
    $ openssl pkcs12 -in "Certificates.p12" -clcerts -nokeys -out certificate.pem   
```
3) Generate the key.pem

```shell
    $ openssl pkcs12 -in "Certificates.p12" -nocerts -out private.key
```

You will be asked for an export password (or export phrase). In this example it will be `123456`, the script will use this as an argument to output the desired `.pkpass`

4) Ensure you have M2Crypto installed

    sudo easy_install M2Crypto

## Typical Usage

```python
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

# Including the icon and logo is necessary for the passbook to be valid.
passfile.addFile('icon.png', open('images/icon.png', 'rb'))
passfile.addFile('logo.png', open('images/logo.png', 'rb'))

# Create and output the Passbook file (.pkpass)
password = '123456'
passfile.create('certificate.pem', 'private.key', 'wwdr.pem', password , 'test.pkpass')
```

## Note: Getting WWDR Certificate

Certificate is available @ http://developer.apple.com/certificationauthority/AppleWWDRCA.cer

It can be exported from KeyChain into a .pem (e.g. wwdr.pem).

## Testing

You can run the tests with `py.test` or optionally with coverage support 
(install `pytest-cov` first): 

    py.test --cov
    
You can also generate a HTML report of the coverage:

    py.test --cov-report html

You can run the tests against multiple versions of Python by running `tox` 
which you need to install first.

## Credits

Developed by [devartis](http://www.devartis.com).

## Contributors

Martin Bächtold
