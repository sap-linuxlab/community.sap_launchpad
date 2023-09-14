#!/usr/bin/env python3
# coding: utf-8

import json
import logging
import re
from urllib.parse import parse_qs, quote_plus, urljoin

from bs4 import BeautifulSoup
from requests.models import HTTPError

from . import constants as C
from .sap_api_common import _request, https_session

logger = logging.getLogger(__name__)

GIGYA_SDK_BUILD_NUMBER = None


def _get_sso_endpoint_meta(url, **kwargs):
    res = _request(url, **kwargs)
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


def sap_sso_login(username, password):
    https_session.cookies.clear()
    if not re.match(r'^[sS]\d+$', username):
        raise ValueError('Please login with SID (like `S1234567890`)')

    endpoint = C.URL_LAUNCHPAD
    meta = {}

    while ('SAMLResponse' not in meta and 'login_hint' not in meta):
        endpoint, meta = _get_sso_endpoint_meta(endpoint, data=meta)
        if 'j_username' in meta:
            meta['j_username'] = username
            meta['j_password'] = password
        if 'changePassword' in endpoint:
            raise ValueError('SAP ID Service has requested `Change Your Password`, possibly the password is too old. Please reset manually and try again.')

    if 'authn' in endpoint:
        support_endpoint, support_meta = _get_sso_endpoint_meta(endpoint,
                                                                data=meta)
        _request(support_endpoint, data=support_meta)

    if 'gigya' in endpoint:
        params = _get_gigya_login_params(endpoint, data=meta)
        _gigya_websdk_bootstrap(params)
        auth_code = _get_gigya_auth_code(username, password)
        login_token = _get_gigya_login_token(params, auth_code)

        uid = _get_uid(params, login_token)
        id_token = _get_id_token(params, login_token)
        uid_details = _get_uid_details(uid, id_token)
        if _is_uid_linked_multiple_sids(uid_details):
            _select_account(uid, username, id_token)

        idp_endpoint = C.URL_ACCOUNT_SSO_IDP.format(k=params['apiKey'])
        context = {
            'loginToken': login_token,
            'samlContext': params['samlContext']
        }
        endpoint, meta = _get_sso_endpoint_meta(idp_endpoint,
                                                params=context,
                                                allow_redirects=False)

        while (endpoint != C.URL_LAUNCHPAD + '/'):
            endpoint, meta = _get_sso_endpoint_meta(endpoint,
                                                    data=meta,
                                                    headers=C.GIGYA_HEADERS,
                                                    allow_redirects=False)

        _request(endpoint, data=meta, headers=C.GIGYA_HEADERS)


def _get_gigya_login_params(url, data):
    gigya_idp_res = _request(url, data=data)

    extracted_url_params = re.sub(r'^.*?\?', '', gigya_idp_res.url)
    params = {k: v[0] for k, v in parse_qs(extracted_url_params).items()}
    return params


def _gigya_websdk_bootstrap(params):
    page_url = f'{C.URL_ACCOUNT_SAML_PROXY}?apiKey=' + params['apiKey'],
    params.update({
        'pageURL': page_url,
        'sdk': 'js_latest',
        'sdkBuild': '12426',
        'format': 'json',
    })

    _request(C.URL_ACCOUNT_CDC_API + '/accounts.webSdkBootstrap',
             params=params,
             headers=C.GIGYA_HEADERS)


def _get_gigya_auth_code(username, password):

    auth = {'login': username, 'password': password}

    headers = C.GIGYA_HEADERS.copy()
    headers['Content-Type'] = 'application/json;charset=utf-8'

    res = _request(
        C.URL_ACCOUNT_CORE_API + '/authenticate',
        params={'reqId': C.URL_SUPPORT_PORTAL},
        data=json.dumps(auth),
        headers=headers,
    )
    j = res.json()

    auth_code = j.get('cookieValue')
    return auth_code


def _get_gigya_login_token(saml_params, auth_code):
    query_params = {
        'sessionExpiration': '0',
        'authCode': auth_code,
    }
    j = _cdc_api_request('socialize.notifyLogin', saml_params, query_params)
    token = j.get('login_token')
    logger.debug(f'loging_token: {token}')
    return token


def _get_id_token(saml_params, login_token):
    query_params = {
        'expiration': '180',
        'login_token': login_token,
    }

    j = _cdc_api_request('accounts.getJWT', saml_params, query_params)
    token = j.get('id_token')
    logger.debug(f'id_token: {token}')
    return token


def _get_uid(saml_params, login_token):
    query_params = {
        'include': 'profile,data',
        'login_token': login_token,
    }
    j = _cdc_api_request('accounts.getAccountInfo', saml_params, query_params)
    uid = j.get('UID')
    logger.debug(f'UID: {uid}')
    return uid


def _get_uid_details(uid, id_token):
    url = f'{C.URL_ACCOUNT_CORE_API}/accounts/{uid}'
    headers = C.GIGYA_HEADERS.copy()
    headers['Authorization'] = f'Bearer {id_token}'

    j = _request(url, headers=headers).json()
    return j


def _is_uid_linked_multiple_sids(uid_details):
    accounts = uid_details['accounts']
    linked = []
    for _, v in accounts.items():
        linked.extend(v['linkedAccounts'])

    logger.debug(f'linked account: \n {linked}')
    return len(linked) > 1


def _select_account(uid, sid, id_token):
    url = f'{C.URL_ACCOUNT_CORE_API}/accounts/{uid}/selectedAccount'
    data = {'idsName': sid, 'automatic': 'false'}

    headers = C.GIGYA_HEADERS.copy()
    headers['Authorization'] = f'Bearer {id_token}'
    return https_session.put(url, headers=headers, json=data)


def _get_sdk_build_number(api_key):
    global GIGYA_SDK_BUILD_NUMBER
    if GIGYA_SDK_BUILD_NUMBER is not None:
        return GIGYA_SDK_BUILD_NUMBER

    res = _request('https://cdns.gigya.com/js/gigya.js',
                   params={'apiKey': api_key})
    js = res.text
    match = re.search(r'gigya.build\s*=\s*{[\s\S]+"number"\s*:\s*(\d+),', js)
    if not match:
        raise HTTPError("unable to find gigya sdk build number", res.response)

    build_number = match.group(1)
    logger.debug(f'gigya sdk build number: {build_number}')
    return build_number


def _cdc_api_request(endpoint, saml_params, query_params):
    url = '/'.join((C.URL_ACCOUNT_CDC_API, endpoint))

    query = '&'.join([f'{k}={v}' for k, v in saml_params.items()])
    page_url = quote_plus('?'.join((C.URL_ACCOUNT_SAML_PROXY, query)))

    api_key = saml_params['apiKey']
    sdk_build = _get_sdk_build_number(api_key)

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

    res = _request(url, params=params, headers=C.GIGYA_HEADERS)
    j = json.loads(res.text)
    logging.debug(f'cdc API response: \n {res.text}')

    error_code = j['errorCode']
    if error_code != 0:
        http_error_msg = '{} Error: {} for url: {}'.format(
            j['statusCode'], j['errorMessage'], res.url)
        raise HTTPError(http_error_msg, response=res)
    return j
