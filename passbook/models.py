# -*- coding: utf-8 -*-
import decimal
import hashlib
import json
import zipfile
from io import BytesIO

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7


class Alignment:
    LEFT = 'PKTextAlignmentLeft'
    CENTER = 'PKTextAlignmentCenter'
    RIGHT = 'PKTextAlignmentRight'
    JUSTIFIED = 'PKTextAlignmentJustified'
    NATURAL = 'PKTextAlignmentNatural'


class BarcodeFormat:
    PDF417 = 'PKBarcodeFormatPDF417'
    QR = 'PKBarcodeFormatQR'
    AZTEC = 'PKBarcodeFormatAztec'
    CODE128 = 'PKBarcodeFormatCode128'


class TransitType:
    AIR = 'PKTransitTypeAir'
    TRAIN = 'PKTransitTypeTrain'
    BUS = 'PKTransitTypeBus'
    BOAT = 'PKTransitTypeBoat'
    GENERIC = 'PKTransitTypeGeneric'


class DateStyle:
    NONE = 'PKDateStyleNone'
    SHORT = 'PKDateStyleShort'
    MEDIUM = 'PKDateStyleMedium'
    LONG = 'PKDateStyleLong'
    FULL = 'PKDateStyleFull'


class NumberStyle:
    DECIMAL = 'PKNumberStyleDecimal'
    PERCENT = 'PKNumberStylePercent'
    SCIENTIFIC = 'PKNumberStyleScientific'
    SPELLOUT = 'PKNumberStyleSpellOut'


class Field(object):

    def __init__(self, key, value, label=''):

        self.key = key  # Required. The key must be unique within the scope
        self.value = value  # Required. Value of the field. For example, 42
        self.label = label  # Optional. Label text for the field.
        self.changeMessage = ''  # Optional. Format string for the alert text that is displayed when the pass is updated
        self.textAlignment = Alignment.LEFT

    def json_dict(self):
        return self.__dict__


class DateField(Field):

    def __init__(self, key, value, label='', dateStyle=DateStyle.SHORT,
                 timeStyle=DateStyle.SHORT, ignoresTimeZone=False):
        super().__init__(key, value, label)
        self.dateStyle = dateStyle  # Style of date to display
        self.timeStyle = timeStyle  # Style of time to display
        self.isRelative = False  # If true, the labels value is displayed as a relative date
        if ignoresTimeZone:
            self.ignoresTimeZone = ignoresTimeZone

    def json_dict(self):
        return self.__dict__


class NumberField(Field):

    def __init__(self, key, value, label=''):
        super().__init__(key, value, label)
        self.numberStyle = NumberStyle.DECIMAL  # Style of date to display

    def json_dict(self):
        return self.__dict__


class CurrencyField(Field):

    def __init__(self, key, value, label='', currencyCode=''):
        super().__init__(key, value, label)
        self.currencyCode = currencyCode  # ISO 4217 currency code

    def json_dict(self):
        return self.__dict__


class Barcode(object):

    def __init__(self, message, format=BarcodeFormat.PDF417, altText='', messageEncoding='iso-8859-1'):
        self.format = format
        self.message = message  # Required. Message or payload to be displayed as a barcode
        self.messageEncoding = messageEncoding  # Required. Text encoding that is used to convert the message
        if altText:
            self.altText = altText  # Optional. Text displayed near the barcode

    def json_dict(self):
        return self.__dict__


class Location(object):

    def __init__(self, latitude, longitude, altitude=0.0):
        # Required. Latitude, in degrees, of the location.
        try:
            self.latitude = float(latitude)
        except (ValueError, TypeError):
            self.latitude = 0.0
        # Required. Longitude, in degrees, of the location.
        try:
            self.longitude = float(longitude)
        except (ValueError, TypeError):
            self.longitude = 0.0
        # Optional. Altitude, in meters, of the location.
        try:
            self.altitude = float(altitude)
        except (ValueError, TypeError):
            self.altitude = 0.0
        # Optional. Notification distance
        self.distance = None
        # Optional. Text displayed on the lock screen when
        # the pass is currently near the location
        self.relevantText = ''

    def json_dict(self):
        return self.__dict__


class IBeacon(object):
    def __init__(self, proximityuuid, major, minor):
        # IBeacon data
        self.proximityUUID = proximityuuid
        self.major = major
        self.minor = minor

        # Optional. Text message where near the ibeacon
        self.relevantText = ''

    def json_dict(self):
        return self.__dict__


class PassInformation(object):

    def __init__(self):
        self.headerFields = []
        self.primaryFields = []
        self.secondaryFields = []
        self.backFields = []
        self.auxiliaryFields = []

    def addHeaderField(self, key, value, label):
        self.headerFields.append(Field(key, value, label))

    def addPrimaryField(self, key, value, label):
        self.primaryFields.append(Field(key, value, label))

    def addSecondaryField(self, key, value, label):
        self.secondaryFields.append(Field(key, value, label))

    def addBackField(self, key, value, label):
        self.backFields.append(Field(key, value, label))

    def addAuxiliaryField(self, key, value, label):
        self.auxiliaryFields.append(Field(key, value, label))

    def json_dict(self):
        d = {}
        if self.headerFields:
            d.update({'headerFields': [f.json_dict() for f in self.headerFields]})
        if self.primaryFields:
            d.update({'primaryFields': [f.json_dict() for f in self.primaryFields]})
        if self.secondaryFields:
            d.update({'secondaryFields': [f.json_dict() for f in self.secondaryFields]})
        if self.backFields:
            d.update({'backFields': [f.json_dict() for f in self.backFields]})
        if self.auxiliaryFields:
            d.update({'auxiliaryFields': [f.json_dict() for f in self.auxiliaryFields]})
        return d


class BoardingPass(PassInformation):

    def __init__(self, transitType=TransitType.AIR):
        super().__init__()
        self.transitType = transitType
        self.jsonname = 'boardingPass'

    def json_dict(self):
        d = super().json_dict()
        d.update({'transitType': self.transitType})
        return d


class Coupon(PassInformation):

    def __init__(self):
        super().__init__()
        self.jsonname = 'coupon'


class EventTicket(PassInformation):

    def __init__(self):
        super().__init__()
        self.jsonname = 'eventTicket'


class Generic(PassInformation):

    def __init__(self):
        super().__init__()
        self.jsonname = 'generic'


class StoreCard(PassInformation):

    def __init__(self):
        super().__init__()
        self.jsonname = 'storeCard'


class Pass(object):

    def __init__(self, passInformation, json='', passTypeIdentifier='',
                 organizationName='', teamIdentifier=''):

        self._files = {}  # Holds the files to include in the .pkpass
        self._hashes = {}  # Holds the SHAs of the files array

        # Standard Keys

        # Required. Team identifier of the organization that originated and
        # signed the pass, as issued by Apple.
        self.teamIdentifier = teamIdentifier
        # Required. Pass type identifier, as issued by Apple. The value must
        # correspond with your signing certificate. Used for grouping.
        self.passTypeIdentifier = passTypeIdentifier
        # Required. Display name of the organization that originated and
        # signed the pass.
        self.organizationName = organizationName
        # Required. Serial number that uniquely identifies the pass.
        self.serialNumber = ''
        # Required. Brief description of the pass, used by the iOS
        # accessibility technologies.
        self.description = ''
        # Required. Version of the file format. The value must be 1.
        self.formatVersion = 1

        # Visual Appearance Keys
        self.backgroundColor = None  # Optional. Background color of the pass
        self.foregroundColor = None  # Optional. Foreground color of the pass,
        self.labelColor = None  # Optional. Color of the label text
        self.logoText = None  # Optional. Text displayed next to the logo
        self.barcode = None  # Optional. Information specific to barcodes.  This is deprecated and can only be set to original barcode formats.
        self.barcodes = None #Optional.  All supported barcodes
        # Optional. If true, the strip image is displayed
        self.suppressStripShine = False

        # Web Service Keys

        # Optional. If present, authenticationToken must be supplied
        self.webServiceURL = None
        # The authentication token to use with the web service
        self.authenticationToken = None

        # Relevance Keys

        # Optional. Locations where the pass is relevant.
        # For example, the location of your store.
        self.locations = None
        # Optional. IBeacons data
        self.ibeacons = None
        # Optional. Date and time when the pass becomes relevant
        self.relevantDate = None

        # Optional. A list of iTunes Store item identifiers for
        # the associated apps.
        self.associatedStoreIdentifiers = None
        self.appLaunchURL = None
        # Optional. Additional hidden data in json for the passbook
        self.userInfo = None

        self.expirationDate = None
        self.voided = None

        self.passInformation = passInformation

    # Adds file to the file array
    def addFile(self, name, fd):
        self._files[name] = fd.read()

    # Creates the actual .pkpass file
    def create(self, certificate, key, wwdr_certificate, password, zip_file=None):
        pass_json = self._createPassJson()
        manifest = self._createManifest(pass_json)
        signature = self._createSignatureCrypto(manifest, certificate, key, wwdr_certificate, password)
        # signature = self._createSignature(manifest, certificate, key, wwdr_certificate, password)
        if not zip_file:
            zip_file = BytesIO()
        self._createZip(pass_json, manifest, signature, zip_file=zip_file)
        return zip_file

    def _createPassJson(self):
        return json.dumps(self, default=PassHandler)

    def _createManifest(self, pass_json):
        """
        Creates the hashes for all the files included in the pass file.
        """
        self._hashes['pass.json'] = hashlib.sha1(pass_json.encode('utf-8')).hexdigest()
        for filename, filedata in self._files.items():
            self._hashes[filename] = hashlib.sha1(filedata).hexdigest()
        return json.dumps(self._hashes)

    # def _get_smime(self, certificate, key, wwdr_certificate, password):
    #     """
    #     :return: M2Crypto.SMIME.SMIME
    #     """
    #     def passwordCallback(*args, **kwds):
    #         return bytes(password, encoding='ascii')

    #     smime = SMIME.SMIME()

    #     wwdrcert = X509.load_cert(wwdr_certificate)
    #     stack = X509_Stack()
    #     stack.push(wwdrcert)
    #     smime.set_x509_stack(stack)

    #     smime.load_key(key, certfile=certificate, callback=passwordCallback)
    #     return smime

    # def _sign_manifest(self, manifest, certificate, key, wwdr_certificate, password):
    #     """
    #     :return: M2Crypto.SMIME.PKCS7
    #     """
    #     smime = self._get_smime(certificate, key, wwdr_certificate, password)
    #     pkcs7 = smime.sign(
    #         SMIME.BIO.MemoryBuffer(bytes(manifest, encoding='utf8')),
    #         flags=SMIME.PKCS7_DETACHED | SMIME.PKCS7_BINARY
    #     )
    #     return pkcs7

    # def _createSignature(self, manifest, certificate, key,
    #                      wwdr_certificate, password):
    #     """
    #     Creates a signature (DER encoded) of the manifest. The manifest is the file
    #     containing a list of files included in the pass file (and their hashes).
    #     """
    #     pk7 = self._sign_manifest(manifest, certificate, key, wwdr_certificate, password)
    #     der = SMIME.BIO.MemoryBuffer()
    #     pk7.write_der(der)
    #     return der.read()
    
    def _readFileBytes(self, path):
        """
        Utility function to read files as byte data
        :param path: file path
        :returns bytes
        """
        file = open(path)
        return file.read().encode('UTF-8')

    def _createSignatureCrypto(self, manifest, certificate, key,
                         wwdr_certificate, password):
        """
        Creates a signature (DER encoded) of the manifest.
        Rewritten to use cryptography library instead of M2Crypto 
        The manifest is the file
        containing a list of files included in the pass file (and their hashes).
        """
        cert = x509.load_pem_x509_certificate(self._readFileBytes(certificate))
        priv_key = serialization.load_pem_private_key(self._readFileBytes(key), password=password.encode('UTF-8'))
        wwdr_cert = x509.load_pem_x509_certificate(self._readFileBytes(wwdr_certificate))
        
        options = [pkcs7.PKCS7Options.DetachedSignature]
        return pkcs7.PKCS7SignatureBuilder()\
                .set_data(manifest.encode('UTF-8'))\
                .add_signer(cert, priv_key, hashes.SHA1())\
                .add_certificate(wwdr_cert)\
                .sign(serialization.Encoding.DER, options)

    # Creates .pkpass (zip archive)
    def _createZip(self, pass_json, manifest, signature, zip_file=None):
        zf = zipfile.ZipFile(zip_file or 'pass.pkpass', 'w')
        zf.writestr('signature', signature)
        zf.writestr('manifest.json', manifest)
        zf.writestr('pass.json', pass_json)
        for filename, filedata in self._files.items():
            zf.writestr(filename, filedata)
        zf.close()

    def json_dict(self):
        d = {
            'description': self.description,
            'formatVersion': self.formatVersion,
            'organizationName': self.organizationName,
            'passTypeIdentifier': self.passTypeIdentifier,
            'serialNumber': self.serialNumber,
            'teamIdentifier': self.teamIdentifier,
            'suppressStripShine': self.suppressStripShine,
            self.passInformation.jsonname: self.passInformation.json_dict()
        }
        #barcodes have 2 fields, 'barcode' is legacy so limit it to the legacy formats, 'barcodes' supports all
        if self.barcode:
            original_formats = [BarcodeFormat.PDF417, BarcodeFormat.QR, BarcodeFormat.AZTEC]
            legacyBarcode = self.barcode
            newBarcodes = [self.barcode.json_dict()]
            if self.barcode.format not in original_formats:
                legacyBarcode = Barcode(self.barcode.message, BarcodeFormat.PDF417, self.barcode.altText)
            d.update({'barcodes': newBarcodes})
            d.update({'barcode': legacyBarcode})

        if self.relevantDate:
            d.update({'relevantDate': self.relevantDate})
        if self.backgroundColor:
            d.update({'backgroundColor': self.backgroundColor})
        if self.foregroundColor:
            d.update({'foregroundColor': self.foregroundColor})
        if self.labelColor:
            d.update({'labelColor': self.labelColor})
        if self.logoText:
            d.update({'logoText': self.logoText})
        if self.locations:
            d.update({'locations': self.locations})
        if self.ibeacons:
            d.update({'beacons': self.ibeacons})
        if self.userInfo:
            d.update({'userInfo': self.userInfo})
        if self.associatedStoreIdentifiers:
            d.update(
                {'associatedStoreIdentifiers': self.associatedStoreIdentifiers}
            )
        if self.appLaunchURL:
            d.update({'appLaunchURL': self.appLaunchURL})
        if self.expirationDate:
            d.update({'expirationDate': self.expirationDate})
        if self.voided:
            d.update({'voided': True})
        if self.webServiceURL:
            d.update({'webServiceURL': self.webServiceURL,
                      'authenticationToken': self.authenticationToken})
        return d


def PassHandler(obj):
    if hasattr(obj, 'json_dict'):
        return obj.json_dict()
    else:
        # For Decimal latitude and logitude etc.
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        else:
            return obj
