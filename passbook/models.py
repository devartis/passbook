import json
import simplejson
import hashlib
import zipfile
import base64
import os.path
from M2Crypto import SMIME
from M2Crypto import X509
from M2Crypto.X509 import X509_Stack


class Field:

    def __init__(self, key, value, label = ''):

        self.key = key # Required. The key must be unique within the scope
        self.label = label # Optional. Label text for the field.
        self.value = value # Required. Value of the field. For example, 42
        #self.changeMessage = None # Optional. Format string for the alert text that is displayed when the pass is updated
        #self.textAlignment = None #PKTextAlignmentLeft,PKTextAlignmentCenter, PKTextAlignmentRight,PKTextAlignmentJustified, PKTextAlignment-Natural
        # TODO: Date Style Keys, Number Style Keys

    def json_dict(self):
        return self.__dict__
        
        
class Barcode:

    def __init__(self, message):

        self.format = 'PKBarcodeFormatPDF417' # PKBarcodeFormatQR, PKBarcodeFormatPDF417, PKBarcodeFormatAztec.
        self.message = message # Required. Message or payload to be displayed as a barcode
        self.messageEncoding = 'iso-8859-1' # Required. Text encoding that is used to convert the message
        #self.altText = None # Optional. Text displayed near the barcode

    def json_dict(self):
        return self.__dict__
        

class Location:

    def __init__(self, latitude, longitude):

        #self.altitude = None # Optional. Altitude, in meters, of the location.
        self.latitude = latitude # Required. Latitude, in degrees, of the location.
        self.longitude = longitude # Required. Longitude, in degrees, of the location.
        #self.relevantText = None # Optional. Text displayed on the lock screen when the pass is currently

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
                'primaryFields' : [f.json_dict() for f in self.primaryFields],
                'secondaryFields' : [f.json_dict() for f in self.secondaryFields],
                'backFields' : [f.json_dict() for f in self.backFields],
               }
        
        
class BoardingPass(PassInformation):

    def __init__(self, transitType = 'PKTransitTypeAir'):
        super(BoardingPass, self).__init__()
        self.transitType = transitType # PKTransitTypeAir, PKTransitTypeTrain, PKTransitTypeBus, PKTransitTypeBoat, PKTransitTypeGeneric.
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
        super(Generic, self).__init__()
        self.jsonname = 'generic'

    
class StoreCard(PassInformation):

    def __init__(self):
        super(StoreCard, self).__init__()
        self.jsonname = 'storeCard'

    
class Pass :
    
    def __init__(self, passInformation, json = ''):

        self._json = json
        self._files = [] # Holds the files to include in the .pkpass    
        self._json = '' # Holds the json    
        self._hashes = {} # Holds the SHAs of the files array        
        
        # Standard Keys
        self.teamIdentifier = '' # Required. Team identifier of the organization that originated and signed the pass, as issued by Apple.
        self.passTypeIdentifier = '' # Required. Pass type identifier, as issued by Apple. The value must correspond with your signing certificate. Used for grouping.       
        self.serialNumber = '' # Required. Serial number that uniquely identifies the pass. 
        self.description = '' # Required. Brief description of the pass, used by the iOS accessibility technologies.   
        self.formatVersion = 1 # Required. Version of the file format. The value must be 1.
        self.organizationName = '' # Required. Display name of the organization that originated and signed the pass.

        # Visual Appearance Keys
        self.backgroundColor = 'rgb(255,255,255)' # Optional. Background color of the pass
        self.foregroundColor = 'rgb(0,0,0)' # Optional. Foreground color of the pass,
        self.labelColor = 'rgb(0,0,0)' # Optional. Color of the label tex
        self.logoText = '' # Optional. Text displayed next to the logo
        self.barcode = None # Optional. Information specific to barcodes.
        self.suppressStripShine = None # Optional. If true, the strip image is displayed

        # Web Service Keys
        self.webServiceURL = None
        self.authenticationToken = None # The authentication token to use with the web service

        # Relevance Keys
        self.locations = [] # Optional. Locations where the pass is relevant. For example, the location of your store.
        self.relevantDate = None # Optional. Date and time when the pass becomes relevant
        
        self.passInformation = passInformation        
        
        
    # Adds file to the file array
    def addFile(self, path):

        if os.path.exists(path):
            self._files.append(path)

    
    # Creates the actual .pkpass file
    def create(self, certificate, key, wwdr_certificate, password):

        self._json = self.createPassJson()
        manifest = self.createManifest()
        self.createSignature(manifest, certificate, key, wwdr_certificate, password)
        self.createZip(manifest)
        self.clean()
        
    
    def createPassJson(self):

        return json.dumps(self, default=PassHandler)

    
    # creates the hashes for the files and adds them into a json string.
    def createManifest(self):

        # Creates SHA hashes for all files in package
        self._hashes['pass.json'] = hashlib.sha1(self._json).hexdigest()
        for filename in self._files :
            self._hashes[os.path.basename(filename)] = hashlib.sha1(open(filename).read()).hexdigest()        
        manifest = json.dumps(self._hashes)
        
        return manifest
    
    
    # Creates a signature and saves it
    def createSignature(self, manifest, certificate, key, wwdr_certificate, password):

        open('manifest.json', 'w').write(manifest)        

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

        open('signature', 'w').write(der)
        
    
    # Creates .pkpass (zip archive)
    def createZip(self, manifest):

        # Package file in Zip (as .pkpass)
        zf = zipfile.ZipFile('pass.pkpass', 'w')
        zf.write('signature', 'signature')
        zf.writestr('manifest.json', manifest)
        zf.writestr('pass.json', self._json)
        for filename in self._files:
            zf.write(filename, os.path.basename(filename))
        zf.close()
        
        
    def clean(self):
        os.remove('signature')
        os.remove('manifest.json')
        

    def json_dict(self):

        return {'description': self.description,
                'formatVersion': self.formatVersion,
                'organizationName': self.organizationName,
                'passTypeIdentifier': self.passTypeIdentifier,
                'serialNumber': self.serialNumber,
                'teamIdentifier': self.teamIdentifier,
                'backgroundColor': self.backgroundColor,
                'logoText': self.logoText,
                'locations': self.locations,
                'barcode': self.barcode.json_dict(),
                self.passInformation.jsonname: self.passInformation.json_dict()
               }


def PassHandler(obj):

    if hasattr(obj, 'json_dict'):
        return obj.json_dict()
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

        
