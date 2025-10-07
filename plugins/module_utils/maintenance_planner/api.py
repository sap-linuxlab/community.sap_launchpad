import re
import time
import traceback
from html import unescape
from functools import wraps
from urllib.parse import urljoin

from .. import constants as C
from .. import exceptions
from ..auth import get_sso_endpoint_meta

try:
    from bs4 import BeautifulSoup
except ImportError:
    HAS_BS4 = False
    BS4_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_BS4 = True
    BS4_IMPORT_ERROR = None

try:
    from lxml import etree
except ImportError:
    HAS_LXML = False
    LXML_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_LXML = True
    LXML_IMPORT_ERROR = None

# Module-level cache
_MP_XSRF_TOKEN = None
_MP_TRANSACTIONS = None
_MP_NAMESPACE = 'http://xml.sap.com/2012/01/mnp'


def require_bs4(func):
    # A decorator to check for the 'beautifulsoup4' library before executing a function.
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not HAS_BS4:
            raise exceptions.SapLaunchpadError(f"The 'beautifulsoup4' library is required. Error: {BS4_IMPORT_ERROR}")
        return func(*args, **kwargs)
    return wrapper


def require_lxml(func):
    # A decorator to check for the 'lxml' library before executing a function.
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not HAS_LXML:
            raise exceptions.SapLaunchpadError(f"The 'lxml' library is required. Error: {LXML_IMPORT_ERROR}")
        return func(*args, **kwargs)
    return wrapper


def auth_userapps(client):
    # Authenticates against userapps.support.sap.com to establish a session.
    _clear_mp_cookies(client, 'userapps')

    # Reset cache on re-authentication
    global _MP_XSRF_TOKEN, _MP_TRANSACTIONS
    _MP_XSRF_TOKEN = None
    _MP_TRANSACTIONS = None

    endpoint, meta = get_sso_endpoint_meta(client, C.URL_USERAPPS)

    while endpoint != C.URL_USERAPPS:
        endpoint, meta = get_sso_endpoint_meta(client, endpoint, data=meta)

    client.post(endpoint, data=meta)


@require_bs4
def get_transactions(client):
    # Retrieves a list of all available Maintenance Planner transactions.
    global _MP_TRANSACTIONS
    if _MP_TRANSACTIONS is not None:
        return _MP_TRANSACTIONS

    res = _mp_request(client, params={'action': 'getTransactions'})
    xml = unescape(res.text.replace('\ufeff', ''))
    doc = BeautifulSoup(xml, features='lxml')
    transactions = [t.attrs for t in doc.find_all('mnp:transaction')]

    if not transactions:
        raise exceptions.FileNotFoundError("No Maintenance Planner transactions found for this user.")

    _MP_TRANSACTIONS = transactions
    return _MP_TRANSACTIONS


def get_transaction_id(client, name):
    # Finds a transaction ID by its name or display ID.
    transactions = get_transactions(client)

    # Search by transaction name
    for t in transactions:
        if t.get('trans_name') == name:
            return t['trans_id']

    # If not found, search by display ID
    for t in transactions:
        if t.get('trans_display_id') == name:
            return t['trans_id']

    raise exceptions.FileNotFoundError(f"Transaction '{name}' not found by name or display ID.")


@require_lxml
def get_transaction_filename_url(client, trans_id):
    # Parses the files XML to get a list of (URL, Filename) tuples.
    xml = _get_download_files_xml(client, trans_id)
    e = etree.fromstring(xml.encode('utf-16'))
    stack_files = e.xpath(
        '//mnp:entity[@id="stack_files"]/mnp:entity',
        namespaces={'mnp': _MP_NAMESPACE}
    )
    if not stack_files:
        raise exceptions.FileNotFoundError(f"No stack files found in transaction ID {trans_id}.")

    files = []
    for f in stack_files:
        file_id = urljoin(C.URL_SOFTWARE_DOWNLOAD, '/file/' + f.get('id'))
        file_name = f.get('label')
        files.append((file_id, file_name))
    return files


def get_transaction_stack_xml_content(client, trans_id):
    # Downloads the stack XML file content for a transaction.
    # The response contains an XML file with XML Element values using appropriate special character predefined entities (e.g. &amp; instead of &).
    params = {
        'action': 'downloadFiles',
        'sub_action': 'stack-plan',
        'session_id': trans_id,
    }
    res = _mp_request(client, params=params)

    filename = None
    content_disposition = res.headers.get('content-disposition')
    if content_disposition:
        match = re.search(r'filename="?([^"]+)"?', content_disposition)
        if match:
            filename = match.group(1)

    return res.text, filename


def _mp_request(client, **kwargs):
    # A wrapper for making requests to the MP service, handling timestamps,
    # XSRF tokens, and re-authentication.
    params = kwargs.get('params', {}).copy()
    params['_'] = int(time.time() * 1000)
    kwargs['params'] = params

    method = 'POST' if 'data' in kwargs or 'json' in kwargs else 'GET'

    headers = kwargs.get('headers', {}).copy()
    if params.get('action') != 'getInitialData':
        headers['xsrf-token'] = _get_xsrf_token(client)
    kwargs['headers'] = headers

    if 'allow_redirects' not in kwargs:
        kwargs['allow_redirects'] = False

    def do_request():
        return client.request(method, C.URL_USERAPP_MP_SERVICE, **kwargs)

    res = do_request()

    if (res.status_code == 302 and res.headers.get('location', '').startswith(C.URL_ACCOUNT)):
        # Session for userapps has expired, re-authenticate and retry.
        auth_userapps(client)
        res = do_request()

    return res


def _get_xsrf_token(client):
    # Fetches and caches the XSRF token required for MP requests.
    global _MP_XSRF_TOKEN
    if _MP_XSRF_TOKEN:
        return _MP_XSRF_TOKEN

    res = _mp_request(client, params={'action': 'getInitialData'})

    token = res.headers.get('xsrf-token')
    if not token:
        raise exceptions.SapLaunchpadError("Failed to get XSRF token for Maintenance Planner.")

    _MP_XSRF_TOKEN = token
    return _MP_XSRF_TOKEN


def _get_download_files_xml(client, trans_id):
    # Fetches the XML defining the files for a given transaction.
    trans_name = _get_transaction(client, 'trans_id', trans_id)['trans_name']
    request_xml = _build_mnp_xml(
        action='postProcessStack',
        call_for='download_stack_xml',
        sessionid=trans_id,
        trans_name=trans_name
    )
    res = _mp_request(client, data=request_xml)
    xml = unescape(res.text.replace('\ufeff', ''))
    return xml


def _get_transaction(client, key, value):
    # Helper to find a single transaction by a specific key-value pair.
    transactions = get_transactions(client)
    for t in transactions:
        if t.get(key) == value:
            return t
    raise exceptions.FileNotFoundError(f"Transaction with {key}='{value}' not found.")


@require_lxml
def _build_mnp_xml(**params):
    # Constructs the MNP XML payload for API requests.
    mnp = f'{{{_MP_NAMESPACE}}}'

    request_keys = ['action', 'trans_name', 'sub_action', 'navigation']
    request_attrs = {k: params.get(k, '') for k in request_keys}

    entity_keys = ['call_for', 'sessionid']
    entity_attrs = {k: params.get(k, '') for k in entity_keys}

    request = etree.Element(f'{mnp}request', nsmap={"mnp": _MP_NAMESPACE}, attrib=request_attrs)
    entity = etree.SubElement(request, f'{mnp}entity', attrib=entity_attrs)
    entity.text = ''

    if 'entities' in params and isinstance(params['entities'], etree._Element):
        entity.append(params['entities'])

    return etree.tostring(request, pretty_print=False)


def _clear_mp_cookies(client, startswith):
    # Clears cookies for a specific domain prefix from the client session.
    for cookie in client.session.cookies:
        if cookie.domain.startswith(startswith):
            client.session.cookies.clear(domain=cookie.domain)
