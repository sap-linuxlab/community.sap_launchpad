#!/user/bin/env python3
# coding: utf-8

from . import constants as C
from .sap_api_common import _request
from .sap_id_sso import sap_sso_login


def get_software_catalog():
    res = _request(C.URL_SOFTWARE_CENTER_VERSION).json()
    revision = res['revision']

    res = _request(C.URL_SOFTWARE_CATALOG.format(v=revision)).json()
    catalog = res['SoftwareCatalog']

    return catalog
