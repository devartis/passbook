import json
import hashlib
import zipfile
import base64
import os.path
from M2Crypto import SMIME

class PKPass :
    
    certPath = '' # Holds the path to the certificate    
    certPass = '' # Holds the password to the certificate    
    files = [] # Holds the files to include in the .pkpass    
    JSON = '' # Holds the json    
    SHAs = {} # Holds the SHAs of the files array

    def __init__(self, certPath = '', certPass = '', JSON = ''):

        self.cert = certPath
        self.certPass = certPass
        self.JSON = JSON
    
        
    # Adds file to the file array
    def addFile(self, path):

        if os.path.exists(path):
            self.files.append(path)

    
    # Creates the actual .pkpass file
    def create(self):

        manifest = self.createManifest()
        self.createSignature(manifest)
        self.createZip(manifest)
        
    
    # creates the hashes for the files and adds them into a json string.
    def createManifest(self):

        # Creates SHA hashes for all files in package
        self.SHAs['pass.json'] = hashlib.sha1(self.JSON).hexdigest()
        for filename in self.files :
            self.SHAs[os.path.basename(filename)] = hashlib.sha1(open(filename).read()).hexdigest()
        
        manifest = json.dumps(self.SHAs)
        
        return manifest
    
    
    # Creates a signature and saves it
    def createSignature(self, manifest):

        open('manifest.json', 'w').write(manifest)        

        def passwordCallback(*args, **kwds):
            return self.certPass

        smime = SMIME.SMIME()
        smime.load_key('key.pem', 'certificate.pem', callback=passwordCallback)        
        pk7 = smime.sign(SMIME.BIO.MemoryBuffer(manifest), flags=SMIME.PKCS7_BINARY)                
        pem = SMIME.BIO.MemoryBuffer()
        pk7.write(pem)
        # convert pem to der
        der = ''.join(l.strip() for l in pem.read().split('-----')[2].splitlines()).decode('base64')        

        open('signature', 'w').write(der)
        
    
    # Creates .pkpass (zip archive)
    def createZip(self, manifest):

        # Package file in Zip (as .pkpass)
        with zipfile.ZipFile('pass.pkpass', 'w') as zf:
            zf.write('signature', 'signature')
            zf.writestr('manifest.json', manifest)
            zf.writestr('pass.json', self.JSON)
            for filename in self.files:
                zf.write(filename, os.path.basename(filename))
    
    
def main():

    pkfile = PKPass()
    pkfile.certPath = 'Certificates.p12' # Set the path to your Pass Certificate (.p12 file)
    pkfile.certPass = '123456' # Set password for certificate
    pkfile.JSON = '{ \
        "passTypeIdentifier": "pass.com.devartis.test", \
        "formatVersion": 1, \
        "organizationName": "devartis", \
        "serialNumber": "123456", \
        "teamIdentifier": "AGK5BZEN3E", \
        "backgroundColor": "rgb(107,156,196)", \
        "logoText": "devartis", \
        "description": "Demo pass", \
    	"boardingPass": { \
            "primaryFields": [ \
                { \
                    "key" : "origin", \
                	"label" : "Buenos Aires", \
                	"value" : "EZE" \
                }, \
                { \
                	"key" : "destination", \
                	"label" : "Mar del plata", \
                	"value" : "MDQ" \
                } \
            ], \
            "secondaryFields": [ \
                { \
                    "key": "gate", \
                    "label": "Gate", \
                    "value": "F12" \
                }, \
                { \
                    "key": "date", \
                    "label": "Departure date", \
                    "value": "08/11/2012 10:22" \
                } \
             ], \
            "backFields": [ \
                { \
                    "key": "passenger-name", \
                    "label": "Passenger", \
                    "value": "Fernando Aramendi" \
                } \
            ], \
            "transitType" : "PKTransitTypeAir" \
        }, \
        "barcode": { \
            "format": "PKBarcodeFormatQR", \
            "message": "Flight-GateF12-ID6643679AH7B", \
            "messageEncoding": "iso-8859-1" \
        } \
    }'

    # add files to the PKPass package
    pkfile.addFile('images/icon.png')
    pkfile.addFile('images/icon@2x.png')
    pkfile.addFile('images/logo.png')
    pkfile.create() # Create and output the PKPass

if __name__ == "__main__":
    main()