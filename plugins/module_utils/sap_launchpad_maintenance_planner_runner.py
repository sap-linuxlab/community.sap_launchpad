#!/user/bin/env python3
# coding: utf-8

import os
import pathlib
import re
import time
from html import unescape
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from lxml import etree
from requests.auth import HTTPBasicAuth
from requests.sessions import session

from . import constants as C
from .sap_api_common import _request, https_session
from .sap_id_sso import _get_sso_endpoint_meta, sap_sso_login

_MP_XSRF_TOKEN = None
_MP_TRANSACTIONS = None


def auth_maintenance_planner():
    # Clear mp relevant cookies for avoiding unexpected responses.
    _clear_mp_cookies('maintenanceplanner')
    res = _request(C.URL_MAINTAINANCE_PLANNER)
    sig_re = re.compile('signature=(.*?);path=\/";location="(.*)"')
    signature, redirect = re.search(sig_re, res.text).groups()

    # Essential cookies for the final callback
    mp_cookies = {
        'signature': signature,
        'fragmentAfterLogin': '',
        'locationAfterLogin': '%2F'
    }

    MP_DOMAIN = C.URL_MAINTAINANCE_PLANNER.replace('https://', '')
    for k, v in mp_cookies.items():
        https_session.cookies.set(k, v, domain=MP_DOMAIN, path='/')

    res = _request(redirect)
    meta_re = re.compile('<meta name="redirect" content="(.*)">')
    raw_redirect = re.search(meta_re, res.text).group(1)

    endpoint = urljoin(res.url, unescape(raw_redirect))
    meta = {}
    while 'SAMLResponse' not in meta:
        endpoint, meta = _get_sso_endpoint_meta(endpoint, data=meta)
    _request(endpoint, data=meta)


def auth_userapps():
    """Auth against userapps.support.sap.com
    """
    _clear_mp_cookies('userapps')
    endpoint, meta = _get_sso_endpoint_meta(C.URL_USERAPPS)

    while endpoint != C.URL_USERAPPS:
        endpoint, meta = _get_sso_endpoint_meta(endpoint, data=meta)
    _request(endpoint, data=meta)

    # Reset Cache
    global _MP_XSRF_TOKEN
    global _MP_TRANSACTIONS
    _MP_XSRF_TOKEN = None
    _MP_TRANSACTIONS = None


def get_mp_user_details():
    url = urljoin(C.URL_MAINTAINANCE_PLANNER,
                  '/MCP/MPHomePageController/getUserDetailsDisplay')
    params = {'_': int(time.time() * 1000)}
    user = _request(url, params=params).json()
    return user


def get_transactions():
    global _MP_TRANSACTIONS
    if _MP_TRANSACTIONS is not None:
        return _MP_TRANSACTIONS
    res = _mp_request(params={'action': 'getTransactions'})
    xml = unescape(res.text.replace('\ufeff', ''))
    doc = BeautifulSoup(xml, features='lxml')
    _MP_TRANSACTIONS = [t.attrs for t in doc.find_all('mnp:transaction')]
    return _MP_TRANSACTIONS


def get_transaction_details(trans_id):
    params = {
        'action': 'getMaintCycle',
        'sub_action': 'load',
        'call_from': 'transactions',
        'session_id': trans_id
    }
    res = _mp_request(params=params)
    xml = unescape(res.text.replace('\ufeff', ''))
    return xml


def get_transaction_stack_xml(trans_id, output_dir=None):
    params = {
        'action': 'downloadFiles',
        'sub_action': 'stack-plan',
        'session_id': trans_id,
    }

    # Returns XML file with XML Element values using appropriate special character predefined entities (e.g. &amp; instead of &)
    res = _mp_request(params=params)

    if output_dir is None:
        return res.text

    dest = pathlib.Path(output_dir)
    # content-disposition: attachment; filename=MP_XX_STACK.xml
    _, name = res.headers.get('content-disposition').split('filename=')
    dest = dest.joinpath(name)

    with open(dest, 'w') as f:
        f.write(res.text)


def get_stack_files_xml(trans_id):
    trans_name = _get_transaction_name(trans_id)
    request_xml = _build_mnp_xml(action='getStackFiles',
                                 call_for='download_stack_xml',
                                 sessionid=trans_id,
                                 trans_name=trans_name)

    res = _mp_request(data=request_xml)
    xml = unescape(res.text.replace('\ufeff', ''))
    return xml


def get_download_files_xml(trans_id):
    trans_name = _get_transaction_name(trans_id)
    request_xml = _build_mnp_xml(action='postProcessStack',
                                 call_for='download_stack_xml',
                                 sessionid=trans_id,
                                 trans_name=trans_name)
    res = _mp_request(data=request_xml)
    xml = unescape(res.text.replace('\ufeff', ''))
    return xml


def get_download_basket_files(trans_id):
    params = {
        'action': 'getDownloadBasketFiles',
        'session_id': trans_id,
    }
    res = _mp_request(params=params)
    xml = unescape(res.text.replace('\ufeff', ''))
    return xml


def add_stack_download_files_to_basket(trans_id):
    '''
    POST data formart:

    <mnp:request action="push2Db" navigation="" sub_action="" trans_name="" xmlns:mnp="http://xml.sap.com/2012/01/mnp">
    <mnp:entity call_for="download_stack_xml" sessionid="901B0ED2ECCE1EDC8A8092845A86CA0E">
        <mnp:entity id="stack_files" label="List of files selected for download" type="Download Stack Independent Files">
            <mnp:entity id="0010000000262512021" label="SAPFRA14S.SAR" type="STL"></mnp:entity>
            <mnp:entity id="0010000000335052021" label="K-30006INUITRV001.SAR" type="STL"></mnp:entity>
        </mnp:entity>
    </mnp:entity>
    </mnp:request>
    '''
    params = {
        'action': 'push2Db',
        'session_id': trans_id,
    }
    xml = get_download_files_xml(trans_id)
    doc = etree.fromstring(xml.encode('utf-16'))
    stack_files = doc.xpath(
        '//mnp:entity[@id="stack_files"]',
        namespaces={'mnp': 'http://xml.sap.com/2012/01/mnp'})
    if not stack_files:
        raise ValueError('stack files not found')

    request_xml = _build_mnp_xml(action='push2Db',
                                 call_for='download_stack_xml',
                                 sessionid=trans_id,
                                 entities=stack_files[0])
    res = _mp_request(params=params, data=request_xml)
    xml = unescape(res.text.replace('\ufeff', ''))
    return xml


def get_download_basket_url_filename():
    download_items = get_download_basket_json()
    return [(i['DirectDownloadUrl'], i['ObjectName']) for i in download_items]


def get_download_basket_json():
    url = C.URL_SOFTWARE_CENTER_SERVICE + '/DownloadBasketItemSet'
    headers = {'Accept': 'application/json'}
    j = _request(url, headers=headers).json()

    results = j['d']['results']
    for r in results:
        r.pop('__metadata', None)
    return results


def get_transaction_id_by_name(name):
    transaction = _get_transaction('trans_name', name)
    return transaction['trans_id']


def get_transaction_id_by_display_id(display_id):
    transaction = _get_transaction('trans_display_id', display_id)
    return transaction['trans_id']

def get_transaction_filename_url(trans_id):
    xml = get_download_files_xml(trans_id)
    e = etree.fromstring(xml.encode('utf-16'))
    stack_files = e.xpath(
        '//mnp:entity[@id="stack_files"]/mnp:entity',
        namespaces={'mnp': 'http://xml.sap.com/2012/01/mnp'})
    files = []
    for f in stack_files:
        file_id = C.URL_SOFTWARE_DOWNLOAD + '/file/' + f.get('id')
        file_name = f.get('label')
        files.append((file_id, file_name))
    return files

def fetch_download_files(display_id):
    params = {
        'action': 'fetchFile',
        'sub_action': 'download_xml',
        'display_id': display_id,
    }

    res = _mp_request(params=params)
    xml = unescape(res.text.replace('\ufeff', ''))
    e = etree.fromstring(xml.encode('utf-8'))
    files = e.xpath('./download/files/file')
    url_filename_list = [(f.find('url').text, f.find('name').text)
                         for f in files]

    return url_filename_list


def clear_download_basket():
    download_items = get_download_basket_json()
    for item in download_items:
        object_id = item['ObjectKey']
        delete_item_in_download_basket(object_id)


def delete_item_in_download_basket(object_id):
    url = C.URL_SOFTWARE_CENTER_SERVICE + '/DownloadContentSet'
    params = {
        '_MODE': 'OBJDEL',
        'OBJID': object_id,
    }

    _request(url, params=params)


# Getting software download links and filenames via Legacy API,
# which required SID username and password for Basic Authentication.
# Usually we should use `fetch_download_files` instead.
def fetch_download_files_via_legacy_api(username, password, display_id):
    params = {
        'action': 'fetchFile',
        'sub_action': 'download_xml',
        'display_id': display_id,
    }

    res = _request(C.URL_LEGACY_MP_API,
                   params=params,
                   auth=HTTPBasicAuth(username, password))
    xml = unescape(res.text.replace('\ufeff', ''))
    e = etree.fromstring(xml.encode('utf-8'))
    files = e.xpath('./download/files/file')
    url_filename_list = [(f.find('url').text, f.find('name').text)
                         for f in files]

    return url_filename_list


def _get_transaction_name(trans_id):
    transaction = _get_transaction('trans_id', trans_id)
    return transaction['trans_name']


def _get_transaction(key, value):
    transactions = get_transactions()
    trans = [t for t in transactions if t[key] == value]
    if not trans:
        raise KeyError(f'{key}: {value} not found in transactions')
    return trans[0]


def _mp_request(**kwargs):
    params = {
        '_': int(time.time() * 1000),
    }
    if 'params' in kwargs:
        params.update(kwargs['params'])
        kwargs.pop('params')

    if params.get('action') != 'getInitialData':
        kwargs['headers'] = {'xsrf-token': _xsrf_token()}

    kwargs['allow_redirects'] = False

    res = _request(C.URL_USERAPP_MP_SERVICE, params=params, **kwargs)
    if (res.status_code == 302
            and res.headers.get('location').startswith(C.URL_ACCOUNT)):
        if not _is_sso_session_active():
            raise Exception('Not logged in or session expired.'
                            ' Please login with `sap_sso_login`')
        auth_userapps()
        res = _request(C.URL_USERAPP_MP_SERVICE, params=params, **kwargs)

    return res


def _build_mnp_xml(**params):
    namespace = 'http://xml.sap.com/2012/01/mnp'
    mnp = f'{{{namespace}}}'

    request_keys = ['action', 'trans_name', 'sub_action', 'navigation']
    request_attrs = {k: params.get(k, '') for k in request_keys}

    entity_keys = ['call_for', 'sessionid']
    entity_attrs = {k: params.get(k, '') for k in entity_keys}

    request = etree.Element(f'{mnp}request',
                            nsmap={"mnp": namespace},
                            attrib=request_attrs)
    entity = etree.SubElement(request, f'{mnp}entity', attrib=entity_attrs)
    entity.text = ''

    if 'entities' in params and type(params['entities']) is etree._Element:
        entity.append(params['entities'])

    xml_str = etree.tostring(request, pretty_print=True)
    return xml_str


def _xsrf_token():
    global _MP_XSRF_TOKEN
    if _MP_XSRF_TOKEN:
        return _MP_XSRF_TOKEN

    res = _mp_request(params={'action': 'getInitialData'})

    _MP_XSRF_TOKEN = res.headers.get('xsrf-token')
    return _MP_XSRF_TOKEN


def _clear_mp_cookies(startswith):
    for domain in https_session.cookies.list_domains():
        if domain.startswith(startswith):
            https_session.cookies.clear(domain=domain)


def _is_sso_session_active():
    try:
        # Account information
        _request(C.URL_ACCOUNT_ATTRIBUTES).json()
    except Exception as e:
        return False

    return True
