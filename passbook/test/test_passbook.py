"""
Test some basic pass file generation
"""

try:
    import json
except ImportError:
    import simplejson as json
import pytest
from M2Crypto import BIO
from M2Crypto import SMIME
from M2Crypto import X509
from M2Crypto import m2
from path import Path

from passbook.models import Barcode, BarcodeFormat, CurrencyField, Pass, StoreCard

cwd = Path(__file__).parent

wwdr_certificate = cwd / 'certificates/wwdr_certificate.pem'
certificate = cwd / 'certificates/certificate.pem'
key = cwd / 'certificates/key.pem'
password_file = cwd / 'certificates/password.txt'


def _certificates_mising():
    return not wwdr_certificate.exists() or not certificate.exists() or not key.exists()


def create_shell_pass(barcodeFormat=BarcodeFormat.CODE128):
    cardInfo = StoreCard()
    cardInfo.addPrimaryField('name', 'John Doe', 'Name')
    stdBarcode = Barcode('test barcode', barcodeFormat, 'alternate text')
    passfile = Pass(cardInfo, organizationName='Org Name', passTypeIdentifier='Pass Type ID', teamIdentifier='Team Identifier')
    passfile.barcode = stdBarcode
    passfile.serialNumber = '1234567'
    passfile.description = 'A Sample Pass'
    return passfile


def test_basic_pass():
    passfile = create_shell_pass()
    assert passfile.formatVersion == 1
    assert passfile.barcode.format == BarcodeFormat.CODE128
    assert len(passfile._files) == 0

    passfile_json = passfile.json_dict()
    assert passfile_json is not None
    assert passfile_json['suppressStripShine'] == False
    assert passfile_json['formatVersion'] == 1
    assert passfile_json['passTypeIdentifier'] == 'Pass Type ID'
    assert passfile_json['serialNumber'] == '1234567'
    assert passfile_json['teamIdentifier'] == 'Team Identifier'
    assert passfile_json['organizationName'] == 'Org Name'
    assert passfile_json['description'] == 'A Sample Pass'


def test_manifest_creation():
    passfile = create_shell_pass()
    manifest_json = passfile._createManifest(passfile._createPassJson())
    manifest = json.loads(manifest_json)
    assert 'pass.json' in manifest


def test_header_fields():
    passfile = create_shell_pass()
    passfile.passInformation.addHeaderField('header', 'VIP Store Card', 'Famous Inc.')
    pass_json = passfile.json_dict()
    assert pass_json['storeCard']['headerFields'][0]['key'] == 'header'
    assert pass_json['storeCard']['headerFields'][0]['value'] == 'VIP Store Card'
    assert pass_json['storeCard']['headerFields'][0]['label'] == 'Famous Inc.'


def test_secondary_fields():
    passfile = create_shell_pass()
    passfile.passInformation.addSecondaryField('secondary', 'VIP Store Card', 'Famous Inc.')
    pass_json = passfile.json_dict()
    assert pass_json['storeCard']['secondaryFields'][0]['key'] == 'secondary'
    assert pass_json['storeCard']['secondaryFields'][0]['value'] == 'VIP Store Card'
    assert pass_json['storeCard']['secondaryFields'][0]['label'] == 'Famous Inc.'


def test_back_fields():
    passfile = create_shell_pass()
    passfile.passInformation.addBackField('back1', 'VIP Store Card', 'Famous Inc.')
    pass_json = passfile.json_dict()
    assert pass_json['storeCard']['backFields'][0]['key'] == 'back1'
    assert pass_json['storeCard']['backFields'][0]['value'] == 'VIP Store Card'
    assert pass_json['storeCard']['backFields'][0]['label'] == 'Famous Inc.'


def test_auxiliary_fields():
    passfile = create_shell_pass()
    passfile.passInformation.addAuxiliaryField('aux1', 'VIP Store Card', 'Famous Inc.')
    pass_json = passfile.json_dict()
    assert pass_json['storeCard']['auxiliaryFields'][0]['key'] == 'aux1'
    assert pass_json['storeCard']['auxiliaryFields'][0]['value'] == 'VIP Store Card'
    assert pass_json['storeCard']['auxiliaryFields'][0]['label'] == 'Famous Inc.'


def test_with_currency_field():
    passfile = create_shell_pass()
    balance_field = CurrencyField(
        'balance',
        float(22.00),
        'test label',
        'USD',
    )
    balance_field.changeMessage = 'Balance changed to %@.'
    passfile.passInformation.headerFields.append(balance_field)
    passfile.passInformation.addAuxiliaryField('aux1', 'VIP Store Card', 'Famous Inc.')
    pass_json = passfile.json_dict()
    assert 'numberStyle' not in pass_json['storeCard']['headerFields'][0]
    assert 'currencyCode' in pass_json['storeCard']['headerFields'][0]


def test_missing_currency_field():
    passfile = create_shell_pass()
    balance_field = CurrencyField(
        'balance',
        float(22.00),
        'test label',
        None
        )
    del balance_field.currencyCode
    balance_field.changeMessage = 'Balance changed to %@.'
    passfile.passInformation.headerFields.append(balance_field)
    passfile.passInformation.addAuxiliaryField('aux1', 'VIP Store Card', 'Famous Inc.')
    pass_json = passfile.json_dict()
    assert 'numberStyle' in pass_json['storeCard']['headerFields'][0]
    assert 'currencyCode' not in pass_json['storeCard']['headerFields'][0]


def test_code128_pass():
    """
    This test is to create a pass with a new code128 format,
    freezes it to json, then reparses it and validates it defaults
    the legacy barcode correctly
    """
    passfile = create_shell_pass()
    jsonData = passfile._createPassJson()
    thawedJson = json.loads(jsonData)
    assert thawedJson['barcode']['format'] == BarcodeFormat.PDF417
    assert thawedJson['barcodes'][0]['format'] == BarcodeFormat.CODE128


def test_pdf_417_pass():
    """
    This test is to create a pass with a barcode that is valid
    in both past and present versions of IOS
    """
    passfile = create_shell_pass(BarcodeFormat.PDF417)
    jsonData = passfile._createPassJson()
    thawedJson = json.loads(jsonData)
    assert thawedJson['barcode']['format'] == BarcodeFormat.PDF417
    assert thawedJson['barcodes'][0]['format'] == BarcodeFormat.PDF417


def test_files():
    passfile = create_shell_pass()
    passfile.addFile('icon.png', open(cwd / 'static/white_square.png', 'rb'))
    assert len(passfile._files) == 1
    assert 'icon.png' in passfile._files

    manifest_json = passfile._createManifest(passfile._createPassJson())
    manifest = json.loads(manifest_json)
    assert '170eed23019542b0a2890a0bf753effea0db181a' == manifest['icon.png']

    passfile.addFile('logo.png', open(cwd / 'static/white_square.png', 'rb'))
    assert len(passfile._files) == 2
    assert 'logo.png' in passfile._files

    manifest_json = passfile._createManifest(passfile._createPassJson())
    manifest = json.loads(manifest_json)
    assert '170eed23019542b0a2890a0bf753effea0db181a' == manifest['logo.png']


@pytest.mark.skipif(_certificates_mising(), reason='Certificates missing')
def test_signing():
    """
    This test can only run locally if you provide your personal Apple Wallet
    certificates, private key and password. It would not be wise to add
    them to git. Store them in the files indicated below, they are ignored
    by git.
    """
    try:
        with open(password_file) as file_:
            password = file_.read().strip()
    except IOError:
        password = ''

    passfile = create_shell_pass()
    manifest_json = passfile._createManifest(passfile._createPassJson())
    signature = passfile._createSignature(
        manifest_json,
        certificate,
        key,
        wwdr_certificate,
        password,
    )

    smime_obj = SMIME.SMIME()

    store = X509.X509_Store()
    store.load_info(str(wwdr_certificate))
    smime_obj.set_x509_store(store)

    signature_bio = BIO.MemoryBuffer(signature)
    signature_p7 = SMIME.PKCS7(m2.pkcs7_read_bio_der(signature_bio._ptr()), 1)

    stack = signature_p7.get0_signers(X509.X509_Stack())
    smime_obj.set_x509_stack(stack)

    data_bio = BIO.MemoryBuffer(manifest_json)

    # PKCS7_NOVERIFY = do not verify the signers certificate of a signed message.
    assert smime_obj.verify(
        signature_p7, data_bio, flags=SMIME.PKCS7_NOVERIFY
    ) == manifest_json

    tampered_manifest = '{"pass.json": "foobar"}'
    data_bio = BIO.MemoryBuffer(tampered_manifest)
    # Verification MUST fail!
    with pytest.raises(SMIME.PKCS7_Error):
        smime_obj.verify(signature_p7, data_bio, flags=SMIME.PKCS7_NOVERIFY)


@pytest.mark.skipif(_certificates_mising(), reason='Certificates missing')
def test_passbook_creation():
    """
    This test can only run locally if you provide your personal Apple Wallet
    certificates, private key and password. It would not be wise to add
    them to git. Store them in the files indicated below, they are ignored
    by git.
    """
    try:
        with open(password_file) as file_:
            password = file_.read().strip()
    except IOError:
        password = ''

    passfile = create_shell_pass()
    passfile.addFile('icon.png', open(cwd / 'static/white_square.png', 'rb'))
    passfile.create(certificate, key, wwdr_certificate, password)
