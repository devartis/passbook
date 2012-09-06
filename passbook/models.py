import json
import hashlib
import zipfile
import base64
import os.path
from M2Crypto import SMIME

class Pass :
    
    files = [] # Holds the files to include in the .pkpass    
    JSON = '' # Holds the json    
    SHAs = {} # Holds the SHAs of the files array

    def __init__(self, JSON = ''):

        self.JSON = JSON
    
        
    # Adds file to the file array
    def addFile(self, path):

        if os.path.exists(path):
            self.files.append(path)

    
    # Creates the actual .pkpass file
    def create(self, certificate, key, password):

        manifest = self.createManifest()
        self.createSignature(manifest, certificate, key, password)
        self.createZip(manifest)
        self.clean()
        
    
    # creates the hashes for the files and adds them into a json string.
    def createManifest(self):

        # Creates SHA hashes for all files in package
        self.SHAs['pass.json'] = hashlib.sha1(self.JSON).hexdigest()
        for filename in self.files :
            self.SHAs[os.path.basename(filename)] = hashlib.sha1(open(filename).read()).hexdigest()
        
        manifest = json.dumps(self.SHAs)
        
        return manifest
    
    
    # Creates a signature and saves it
    def createSignature(self, manifest, certificate, key, password):

        open('manifest.json', 'w').write(manifest)        

        def passwordCallback(*args, **kwds):
            return password

        smime = SMIME.SMIME()
        smime.load_key(key, certificate, callback=passwordCallback)        
        pk7 = smime.sign(SMIME.BIO.MemoryBuffer(manifest), flags=SMIME.PKCS7_BINARY)                
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
        zf.writestr('pass.json', self.JSON)
        for filename in self.files:
            zf.write(filename, os.path.basename(filename))
        zf.close()
        
    def clean(self):
        os.remove('signature')
        os.remove('manifest.json')
