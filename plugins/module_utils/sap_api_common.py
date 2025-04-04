import logging
import re
from urllib.parse import urlparse

import requests
import urllib3
from requests.adapters import HTTPAdapter

from .constants import COMMON_HEADERS


# By default, the `Authorization` header for Basic Auth will be removed
# if the redirect is to a different host.
# In our case, the DirectDownloadLink with `softwaredownloads.sap.com` domain
# will be redirected to `origin.softwaredownloads.sap.com`,
# so we need to override `rebuild_auth` to perseve the Authorization header
# for sap.com domains.
# This is only required for legacy API.
class SessionAllowBasicAuthRedirects(requests.Session):
    def rebuild_auth(self, prepared_request, response):
        if 'Authorization' in prepared_request.headers:
            request_hostname = urlparse(prepared_request.url).hostname
            if not re.match(r'.*sap.com$', request_hostname):
                del prepared_request.headers['Authorization']


def _request(url, **kwargs):
    global https_session
    if 'headers' not in kwargs:
        kwargs['headers'] = COMMON_HEADERS
    else:
        kwargs['headers'].update(COMMON_HEADERS)

    if 'allow_redirects' not in kwargs:
        kwargs['allow_redirects'] = True

    method = 'POST' if kwargs.get('data') or kwargs.get('json') else 'GET'
    res = https_session.request(method, url, **kwargs)

    # Validating against `res.text` can cause long execution time, because fuzzy search result can contain large `res.text`.
    # This can be prevented by validating `res.status_code` check before `res.text`.
    # Example: 'Two-Factor Authentication' is only in `res.text`, which can lead to long execution.

    if res.status_code == 403:
        if 'You are not authorized to download this file' in res.text:
            raise Exception(f'You are not authorized to download this file.')
        elif 'Account Temporarily Locked Out' in res.text:
            raise Exception(f'Account Temporarily Locked Out. Please reset password to regain access and try again.')
        else:
            res.raise_for_status()

    if res.status_code == 404:
        if 'The file you have requested cannot be found' in res.text:
            raise Exception(f'The file you have requested cannot be found.')
        else:
            res.raise_for_status()

    res.raise_for_status()

    return res


def debug_https_session():
    return https_session


def debug_https():
    from http.client import HTTPConnection
    HTTPConnection.debuglevel = 1
    logging.basicConfig(level=logging.DEBUG)
    logging.debug('Debug is enabled')


def debug_get_session_cookie(session):
    return '; '.join(f'{k}={v}' for k, v in session.cookies.items())


def flag_is_login():
    return 'IDP_SESSION_MARKER_accounts' in https_session.cookies.keys()


def flag_is_gigya():
    return 'gmid' in https_session.cookies.keys()


def is_updated_urllib3():
    # `method_whitelist` argument for Retry is deprecated since 1.26.0,
    # and will be removed in v2.0.0.
    # Typically, the default version on RedHat 8.2 is 1.24.2,
    # so we need to check the version of urllib3 to see if it's updated.
    urllib3_version = urllib3.__version__.split('.')
    if len(urllib3_version) == 2:
        urllib3_version.append('0')
    major, minor, patch = urllib3_version
    major, minor, patch = int(major), int(minor), int(patch)
    if (major, minor, patch) >= (1, 26, 0):
        return True
    return False


https_session = SessionAllowBasicAuthRedirects()
retries = urllib3.Retry(connect=3,
                        read=3,
                        status=3,
                        status_forcelist=[413, 429, 500, 502, 503, 504, 509],
                        backoff_factor=1)
allowed_methods = frozenset(
    ['HEAD', 'GET', 'PUT', 'POST', 'DELETE', 'OPTIONS', 'TRACE'])
if is_updated_urllib3():
    retries.allowed_methods = allowed_methods
else:
    retries.method_whitelist = allowed_methods
https_session.mount('https://', HTTPAdapter(max_retries=retries))
https_session.mount('http://', HTTPAdapter(max_retries=retries))
