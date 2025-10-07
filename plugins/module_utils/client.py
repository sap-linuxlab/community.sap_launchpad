import re
import traceback

from urllib.parse import urlparse

from .constants import COMMON_HEADERS
from . import exceptions

try:
    import requests
    from requests.adapters import HTTPAdapter
    _RequestsSession = requests.Session
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    REQUESTS_IMPORT_ERROR = traceback.format_exc()
    # Placeholders to prevent errors on module load
    requests = None
    HTTPAdapter = object
    _RequestsSession = object

try:
    import urllib3
    HAS_URLLIB3 = True
except ImportError:
    HAS_URLLIB3 = False
    URLLIB3_IMPORT_ERROR = traceback.format_exc()
    # Placeholder to prevent errors on module load
    urllib3 = None


class _SessionAllowBasicAuthRedirects(_RequestsSession):
    # By default, the `Authorization` header for Basic Auth will be removed
    # if the redirect is to a different host.
    # In our case, the DirectDownloadLink with `softwaredownloads.sap.com` domain
    # will be redirected to `origin.softwaredownloads.sap.com`,
    # so we need to override `rebuild_auth` to perseve the Authorization header
    # for sap.com domains.
    # This is only required for legacy API.
    def rebuild_auth(self, prepared_request, response):
        # The parent class might not be a real requests.Session if requests is not installed.
        if HAS_REQUESTS and 'Authorization' in prepared_request.headers:
            request_hostname = urlparse(prepared_request.url).hostname
            if not re.match(r'.*sap.com$', request_hostname):
                del prepared_request.headers['Authorization']


def _is_updated_urllib3():
    # `method_whitelist` argument for Retry is deprecated since 1.26.0,
    # and will be removed in v2.0.0.
    # Typically, the default version on RedHat 8.2 is 1.24.2,
    # so we need to check the version of urllib3 to see if it's updated.
    if not HAS_URLLIB3:
        return False

    urllib3_version = urllib3.__version__.split('.')
    if len(urllib3_version) == 2:
        urllib3_version.append('0')
    major, minor, patch = urllib3_version
    major, minor, patch = int(major), int(minor), int(patch)
    return (major, minor, patch) >= (1, 26, 0)


class ApiClient:
    # A client for handling all HTTP communication with SAP APIs.
    #
    # This class encapsulates a requests.Session object, configured with
    # automatic retries and custom header handling. It provides a clean,
    # object-oriented interface for making API requests, replacing the
    # previous global session and request functions.
    def __init__(self):
        if not HAS_REQUESTS:
            raise exceptions.SapLaunchpadError(f"The 'requests' library is required. Error: {REQUESTS_IMPORT_ERROR}")
        if not HAS_URLLIB3:
            raise exceptions.SapLaunchpadError(f"The 'urllib3' library is required. Error: {URLLIB3_IMPORT_ERROR}")

        self.session = _SessionAllowBasicAuthRedirects()

        # Configure retry logic for the session.
        retries = urllib3.Retry(
            connect=3,
            read=3,
            status=3,
            status_forcelist=[413, 429, 500, 502, 503, 504, 509],
            backoff_factor=1
        )

        # Set allowed methods for retries, handling different urllib3 versions.
        allowed_methods = frozenset(
            ['HEAD', 'GET', 'PUT', 'POST', 'DELETE', 'OPTIONS', 'TRACE']
        )
        if _is_updated_urllib3():
            retries.allowed_methods = allowed_methods
        else:
            retries.method_whitelist = allowed_methods

        # Mount the adapter to the session.
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

    def request(self, method, url, **kwargs):
        # Makes an HTTP request.
        #
        # This method is a wrapper around the session's request method,
        # automatically adding common headers and performing generic
        # error handling for SAP API responses.
        headers = COMMON_HEADERS.copy()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers

        if 'allow_redirects' not in kwargs:
            kwargs['allow_redirects'] = True

        res = self.session.request(method, url, **kwargs)

        # Validating against `res.text` can cause long execution time, because fuzzy search result can contain large `res.text`.
        # This can be prevented by validating `res.status_code` check before `res.text`.
        # Example: 'Two-Factor Authentication' is only in `res.text`, which can lead to long execution.
        if res.status_code == 403:
            if 'You are not authorized to download this file' in res.text:
                raise Exception('You are not authorized to download this file.')
            elif 'Account Temporarily Locked Out' in res.text:
                raise Exception('Account Temporarily Locked Out. Please reset password to regain access and try again.')
            else:
                res.raise_for_status()

        if res.status_code == 404:
            if 'The file you have requested cannot be found' in res.text:
                raise Exception('The file you have requested cannot be found.')
            else:
                res.raise_for_status()

        res.raise_for_status()
        return res

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def head(self, url, **kwargs):
        return self.request('HEAD', url, **kwargs)

    def get_cookies(self):
        return self.session.cookies
