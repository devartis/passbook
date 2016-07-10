"""
Test some basic pass file generation
"""

try:
    import json
except ImportError:
    import simplejson as json
from passbook.models import Barcode, BarcodeFormat, Pass, StoreCard


def create_shell_pass(barcodeFormat=BarcodeFormat.CODE128):
    cardInfo = StoreCard()
    stdBarcode = Barcode('test barcode', barcodeFormat, 'alternate text')
    passfile = Pass(cardInfo, organizationName='Org Name', passTypeIdentifier='Pass Type ID', teamIdentifier='Team Identifier')
    passfile.barcode = stdBarcode
    return passfile


def test_basic_pass():
    passfile = create_shell_pass()
    assert passfile.formatVersion == 1
    assert passfile.barcode.format == BarcodeFormat.CODE128


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

