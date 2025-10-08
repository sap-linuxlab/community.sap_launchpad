from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import re
from functools import wraps

from urllib.parse import parse_qs, quote_plus, urljoin

from . import constants as C
from . import exceptions

try:
    from bs4 import BeautifulSoup
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None
else:
    HAS_BS4 = True

try:
    from requests.models import HTTPError
except ImportError:
    HAS_REQUESTS = False
    HTTPError = None
else:
    HAS_REQUESTS = True

_GIGYA_SDK_BUILD_NUMBER = None


def require_bs4(func):
    # A decorator to check for the 'beautifulsoup4' library before executing a function.
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not HAS_BS4:
            raise ImportError("The 'beautifulsoup4' library is required but was not found.")
        return func(*args, **kwargs)
    return wrapper


def require_requests(func):
    # A decorator to check for the 'requests' library before executing a function.
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not HAS_REQUESTS:
            raise ImportError("The 'requests' library is required but was not found.")
        return func(*args, **kwargs)
    return wrapper


@require_requests
@require_bs4
def login(client, username, password):
    # Main authentication function.
    #
    # This function orchestrates the entire SAP SSO and Gigya authentication
    # flow. It accepts an ApiClient instance, which it populates with the
    # necessary session cookies upon successful authentication.
    client.session.cookies.clear()

    # Ensure usage of SAP User ID even when SAP Universal ID is used,
    # login with email address of SAP Universal ID will otherwise
    # incorrectly default to the last used SAP User ID
    if not re.match(r'^[sS]\d+$', username):
        raise ValueError('Please login with SAP User ID (like `S1234567890`)')

    endpoint = C.URL_LAUNCHPAD
    meta = {}

    while ('SAMLResponse' not in meta and 'login_hint' not in meta):
        endpoint, meta = get_sso_endpoint_meta(client, endpoint, data=meta)
        if 'j_username' in meta:
            meta['j_username'] = username
            meta['j_password'] = password
        if 'changePassword' in endpoint:
            raise ValueError('SAP ID Service has requested `Change Your Password`, possibly the password is too old. Please reset manually and try again.')

    if 'authn' in endpoint:
        support_endpoint, support_meta = get_sso_endpoint_meta(client, endpoint, data=meta)
        client.post(support_endpoint, data=support_meta)

    if 'gigya' in endpoint:
        params = _get_gigya_login_params(client, endpoint, data=meta)
        _gigya_websdk_bootstrap(client, params)
        login_token = _gigya_login(client, username, password, params['apiKey'])

        uid = _get_uid(client, params, login_token)
        id_token = _get_id_token(client, params, login_token)
        uid_details = _get_uid_details(client, uid, id_token)
        if _is_uid_linked_multiple_sids(uid_details):
            _select_account(client, uid, username, id_token)

        idp_endpoint = C.URL_ACCOUNT_SSO_IDP.format(k=params['apiKey'])
        context = {
            'loginToken': login_token,
            'samlContext': params['samlContext']
        }
        endpoint, meta = get_sso_endpoint_meta(client, idp_endpoint,
                                               params=context,
                                               allow_redirects=False)

        while (endpoint != C.URL_LAUNCHPAD + '/'):
            endpoint, meta = get_sso_endpoint_meta(client, endpoint,
                                                   data=meta,
                                                   headers=C.GIGYA_HEADERS,
                                                   allow_redirects=False)

        client.post(endpoint, data=meta, headers=C.GIGYA_HEADERS)


@require_requests
@require_bs4
def get_sso_endpoint_meta(client, url, **kwargs):
    # Scrapes an HTML page to find the next SSO form action URL and its input fields.
    method = 'POST' if kwargs.get('data') or kwargs.get('json') else 'GET'
    res = client.request(method, url, **kwargs)
    soup = BeautifulSoup(res.content, features='lxml')

    # SSO returns 200 OK even when the crendential is wrong, so we need to
    # detect the HTTP body for auth error message. This is only necessary
    # for non-universal SID. For universal SID, the client will raise 401
    # during Gygia auth.
    error_message = soup.find('div', {'id': 'globalMessages'})
    if error_message and 'we could not authenticate you' in error_message.text:
        res.status_code = 401
        res.reason = 'Unauthorized'
        res.raise_for_status()

    form = soup.find('form')
    if not form:
        raise ValueError(
            f'Unable to find form: {res.url}\nContent:\n{res.text}')
    inputs = form.find_all('input')

    endpoint = urljoin(res.url, form['action'])
    metadata = {
        i.get('name'): i.get('value')
        for i in inputs if i.get('type') != 'submit' and i.get('name')
    }

    return (endpoint, metadata)


@require_requests
def _get_gigya_login_params(client, url, data):
    # Follows a redirect and extracts parameters from the resulting URL's query string.
    gigya_idp_res = client.post(url, data=data)

    extracted_url_params = re.sub(r'^.*?\?', '', gigya_idp_res.url)
    params = {k: v[0] for k, v in parse_qs(extracted_url_params).items()}
    return params


@require_requests
def _gigya_websdk_bootstrap(client, params):
    # Performs the initial bootstrap call to the Gigya WebSDK.
    page_url = f'{C.URL_ACCOUNT_SAML_PROXY}?apiKey=' + params['apiKey']
    params.update({
        'pageURL': page_url,
        'sdk': 'js_latest',
        'sdkBuild': '12426',
        'format': 'json',
    })

    client.get(C.URL_ACCOUNT_CDC_API + '/accounts.webSdkBootstrap',
               params=params,
               headers=C.GIGYA_HEADERS)


@require_requests
def _gigya_login(client, username, password, api_key):
    # Performs a login using the standard Gigya accounts.login API.
    # This avoids a custom SAP endpoint that triggers password change notifications.
    login_payload = {
        'loginID': username,
        'password': password,
        'apiKey': api_key,
        'sessionExpiration': 0,
        'include': 'login_token'
    }

    login_url = f"{C.URL_ACCOUNT_CDC_API}/accounts.login"
    res = client.post(login_url, data=login_payload)
    login_response = res.json()

    # Explicitly check for API errors, especially for password-related issues.
    error_code = login_response.get('errorCode', 0)
    if error_code != 0:
        # Error 206002 indicates that the account is pending a password reset.
        if error_code == 206002:
            raise exceptions.AuthenticationError(
                'The password for this account has expired or must be changed. '
                'Please log in to https://account.sap.com manually to reset it.'
            )
        error_message = login_response.get('errorDetails', 'Unknown authentication error')
        raise exceptions.AuthenticationError(f"Gigya authentication failed: {error_message} (errorCode: {error_code})")

    return login_response.get('login_token')


@require_requests
def _get_id_token(client, saml_params, login_token):
    # Exchanges a Gigya login token for a JWT ID token.
    query_params = {
        'expiration': '180',
        'login_token': login_token,
    }

    jwt_response = _cdc_api_request(client, 'accounts.getJWT', saml_params, query_params)
    token = jwt_response.get('id_token')
    return token


@require_requests
def _get_uid(client, saml_params, login_token):
    # Retrieves the user's unique ID (UID) using the login token.
    query_params = {
        'include': 'profile,data',
        'login_token': login_token,
    }
    account_info_response = _cdc_api_request(client, 'accounts.getAccountInfo', saml_params, query_params)
    uid = account_info_response.get('UID')
    return uid


@require_requests
def _get_uid_details(client, uid, id_token):
    # Fetches detailed account information for a given UID.
    url = f'{C.URL_ACCOUNT_CORE_API}/accounts/{uid}'
    headers = C.GIGYA_HEADERS.copy()
    headers['Authorization'] = f'Bearer {id_token}'

    uid_details_response = client.get(url, headers=headers).json()
    return uid_details_response


@require_requests
def _is_uid_linked_multiple_sids(uid_details):
    # Checks if a Universal ID (UID) is linked to more than one S-User ID.
    accounts = uid_details['accounts']
    linked = []
    for _account_type, v in accounts.items():
        linked.extend(v['linkedAccounts'])

    return len(linked) > 1


@require_requests
def _select_account(client, uid, sid, id_token):
    # Selects a specific S-User ID when a Universal ID is linked to multiple accounts.
    url = f'{C.URL_ACCOUNT_CORE_API}/accounts/{uid}/selectedAccount'
    data = {'idsName': sid, 'automatic': 'false'}

    headers = C.GIGYA_HEADERS.copy()
    headers['Authorization'] = f'Bearer {id_token}'
    return client.request('PUT', url, headers=headers, json=data)


@require_requests
def _get_sdk_build_number(client, api_key):
    # Fetches the gigya.js file to extract and cache the SDK build number.
    global _GIGYA_SDK_BUILD_NUMBER
    if _GIGYA_SDK_BUILD_NUMBER is not None:
        return _GIGYA_SDK_BUILD_NUMBER

    res = client.get(C.URL_GIGYA_JS, params={'apiKey': api_key})
    gigya_js_content = res.text
    match = re.search(r'gigya.build\s*=\s*{[\s\S]+"number"\s*:\s*(\d+),', gigya_js_content)
    if not match:
        raise HTTPError("unable to find gigya sdk build number", res.response)

    build_number = match.group(1)
    _GIGYA_SDK_BUILD_NUMBER = build_number
    return build_number


@require_requests
def _cdc_api_request(client, endpoint, saml_params, query_params):
    # Helper to make requests to the Gigya/CDC API, handling common parameters and errors.
    url = '/'.join((C.URL_ACCOUNT_CDC_API, endpoint))

    query = '&'.join([f'{k}={v}' for k, v in saml_params.items()])
    page_url = quote_plus('?'.join((C.URL_ACCOUNT_SAML_PROXY, query)))

    api_key = saml_params['apiKey']
    sdk_build = _get_sdk_build_number(client, api_key)

    params = {
        'sdk': 'js_latest',
        'APIKey': api_key,
        'authMode': 'cookie',
        'pageURL': page_url,
        'sdkBuild': sdk_build,
        'format': 'json'
    }

    if query_params:
        params.update(query_params)

    res = client.get(url, params=params, headers=C.GIGYA_HEADERS)
    json_response = json.loads(res.text)

    error_code = json_response['errorCode']
    if error_code != 0:
        http_error_msg = '{} Error: {} for url: {}'.format(
            json_response['statusCode'], json_response['errorMessage'], res.url)
        raise HTTPError(http_error_msg, response=res)
    return json_response
