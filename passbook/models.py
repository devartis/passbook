#:coding=utf8:

try:
    import json
except ImportError:
    import simplejson as json

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import hashlib
import zipfile
import decimal
from M2Crypto import SMIME
from M2Crypto import X509
from M2Crypto.X509 import X509_Stack

class Alignment:
    LEFT = 'PKTextAlignmentLeft'
    CENTER = 'PKTextAlignmentCenter'
    RIGHT = 'PKTextAlignmentRight'
    JUSTIFIED = 'PKTextAlignmentJustified'
    NATURAL = 'PKTextAlignment-Natural'

class BarcodeFormat:
    PDF417 = 'PKBarcodeFormatPDF417'
    QR = 'PKBarcodeFormatQR'
    AZTEC = 'PKBarcodeFormatAztec'

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

    def __init__(self, key, value, label = ''):

        self.key = key # Required. The key must be unique within the scope        
        self.value = value # Required. Value of the field. For example, 42
        self.label = label # Optional. Label text for the field.
        self.changeMessage = '' # Optional. Format string for the alert text that is displayed when the pass is updated
        self.textAlignment = Alignment.LEFT

    def json_dict(self):
        return self.__dict__
        

class DateField(Field):

    def __init__(self, key, value, label = ''):
        super(DateField, self).__init__(key, value, label)
        self.dateStyle = DateStyle.SHORT # Style of date to display
        self.timeStyle = DateStyle.SHORT # Style of time to display
        self.isRelative = False # If true, the labels value is displayed as a relative date

    def json_dict(self):
        return self.__dict__


class NumberField(Field):

    def __init__(self, key, value, label = ''):
        super(NumberField, self).__init__(key, value, label)
        self.numberStyle = NumberStyle.DECIMAL # Style of date to display

    def json_dict(self):
        return self.__dict__


class Barcode(object):

    def __init__(self, message):

        self.format = BarcodeFormat.PDF417
        self.message = message # Required. Message or payload to be displayed as a barcode
        self.messageEncoding = 'iso-8859-1' # Required. Text encoding that is used to convert the message
        self.altText = '' # Optional. Text displayed near the barcode

    def json_dict(self):
        return self.__dict__
        

class Location(object):

    def __init__(self, latitude, longitude):

        self.latitude = latitude # Required. Latitude, in degrees, of the location.
        self.longitude = longitude # Required. Longitude, in degrees, of the location.
        self.altitude = 0 # Optional. Altitude, in meters, of the location.
        self.relevantText = '' # Optional. Text displayed on the lock screen when the pass is currently

    def json_dict(self):
        return self.__dict__


class PassInformation(object):
    
    def __init__(self):
        self.headerFields = []
        self.primaryFields = []
        self.secondaryFields = []
        self.backFields = []
        self.auxiliaryFields = []

    def addPrimaryField(self, key, value, label):
        self.primaryFields.append(Field(key, value, label))

    def addSecondaryField(self, key, value, label):
        self.secondaryFields.append(Field(key, value, label))

    def addBackField(self, key, value, label):
        self.backFields.append(Field(key, value, label))
        
    def json_dict(self):
        return {
            'headerFields' : [f.json_dict() for f in self.headerFields],
            'primaryFields' : [f.json_dict() for f in self.primaryFields],
            'secondaryFields' : [f.json_dict() for f in self.secondaryFields],
            'backFields' : [f.json_dict() for f in self.backFields],
            'auxiliaryFields' : [f.json_dict() for f in self.auxiliaryFields],
        }
        
        
class BoardingPass(PassInformation):

    def __init__(self, transitType = TransitType.AIR):
        super(BoardingPass, self).__init__()
        self.transitType = transitType 
        self.jsonname = 'boardingPass'

    def json_dict(self):
        d = super(BoardingPass, self).json_dict()
        d.update({'transitType': self.transitType})
        return d
        
        
class Coupon(PassInformation):

    def __init__(self):
        super(Coupon, self).__init__()
        self.jsonname = 'coupon'

    
class EventTicket(PassInformation):

    def __init__(self):
        super(EventTicket, self).__init__()
        self.jsonname = 'eventTicket'

    
class Generic(PassInformation):

    def __init__(self):
        super(Generic, self).__init__()
        self.jsonname = 'generic'

    
class StoreCard(PassInformation):

    def __init__(self):
        super(StoreCard, self).__init__()
        self.jsonname = 'storeCard'

    
class Pass(object):
    
    def __init__(self, passInformation, json = '', passTypeIdentifier = '', organizationName = '', teamIdentifier = ''):

        self._files = {} # Holds the files to include in the .pkpass    
        self._hashes = {} # Holds the SHAs of the files array        
        
        # Standard Keys
        self.teamIdentifier = teamIdentifier # Required. Team identifier of the organization that originated and signed the pass, as issued by Apple.
        self.passTypeIdentifier = passTypeIdentifier # Required. Pass type identifier, as issued by Apple. The value must correspond with your signing certificate. Used for grouping.       
        self.organizationName = organizationName # Required. Display name of the organization that originated and signed the pass.
        self.serialNumber = '' # Required. Serial number that uniquely identifies the pass. 
        self.description = '' # Required. Brief description of the pass, used by the iOS accessibility technologies.   
        self.formatVersion = 1 # Required. Version of the file format. The value must be 1.

        # Visual Appearance Keys
        self.backgroundColor = 'rgb(255,255,255)' # Optional. Background color of the pass
        self.foregroundColor = 'rgb(0,0,0)' # Optional. Foreground color of the pass,
        self.labelColor = 'rgb(0,0,0)' # Optional. Color of the label tex
        self.logoText = '' # Optional. Text displayed next to the logo
        self.barcode = None # Optional. Information specific to barcodes.
        self.suppressStripShine = False # Optional. If true, the strip image is displayed

        # Web Service Keys
        self.webServiceURL = None
        self.authenticationToken = None # The authentication token to use with the web service

        # Relevance Keys
        self.locations = [] # Optional. Locations where the pass is relevant. For example, the location of your store.
        self.relevantDate = None # Optional. Date and time when the pass becomes relevant
        
        self.passInformation = passInformation
        
        
    # Adds file to the file array
    def addFile(self, name, fd):
        self._files[name] = fd.read()
    
    # Creates the actual .pkpass file
    def create(self, certificate, key, wwdr_certificate, password, zip_file=None):
        pass_json = self._createPassJson()
        manifest = self._createManifest(pass_json)
        signature = self._createSignature(manifest, certificate, key, wwdr_certificate, password)
        if not zip_file:
            zip_file = StringIO()
        self.zip_file = self._createZip(pass_json, manifest, signature, zip_file=zip_file)
        return zip_file
    
    def _createPassJson(self):
        return json.dumps(self, default=PassHandler)
    
    # creates the hashes for the files and adds them into a json string.
    def _createManifest(self, pass_json):
        # Creates SHA hashes for all files in package
        self._hashes['pass.json'] = hashlib.sha1(pass_json).hexdigest()
        for filename, filedata in self._files.items():
            self._hashes[filename] = hashlib.sha1(filedata).hexdigest()
        return json.dumps(self._hashes)
    
    # Creates a signature and saves it
    def _createSignature(self, manifest, certificate, key, wwdr_certificate, password):
        def passwordCallback(*args, **kwds):
            return password

        smime = SMIME.SMIME()
        #we need to attach wwdr cert as X509
        wwdrcert = X509.load_cert(wwdr_certificate)
        stack = X509_Stack()
        stack.push(wwdrcert)
        smime.set_x509_stack(stack)

        smime.load_key(key, certificate, callback=passwordCallback)
        pk7 = smime.sign(SMIME.BIO.MemoryBuffer(manifest), flags=SMIME.PKCS7_DETACHED | SMIME.PKCS7_BINARY)                

        pem = SMIME.BIO.MemoryBuffer()
        pk7.write(pem)
        # convert pem to der
        der = ''.join(l.strip() for l in pem.read().split('-----')[2].splitlines()).decode('base64')        

        return der
    
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
        return {
            'description': self.description,
            'formatVersion': self.formatVersion,
            'organizationName': self.organizationName,
            'passTypeIdentifier': self.passTypeIdentifier,
            'serialNumber': self.serialNumber,
            'teamIdentifier': self.teamIdentifier,
            'backgroundColor': self.backgroundColor,
            'foregroundColor': self.foregroundColor,
            'labelColor': self.labelColor,
            'logoText': self.logoText,
            'suppressStripShine': self.suppressStripShine,
            'locations': self.locations,
            'barcode': self.barcode.json_dict(),
            self.passInformation.jsonname: self.passInformation.json_dict()
        }


def PassHandler(obj):
    if hasattr(obj, 'json_dict'):
        return obj.json_dict()
    else:
        # For Decimal latitude and logitude etc.
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        else:
            return obj
