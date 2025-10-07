from __future__ import absolute_import, division, print_function
__metaclass__ = type

import glob
import hashlib
import os
import time
from functools import wraps

from .. import auth
from .. import constants as C
from .. import exceptions
from . import search

try:
    from requests.exceptions import ConnectionError, HTTPError
except ImportError:
    HAS_REQUESTS = False
    ConnectionError, HTTPError = None, None
else:
    HAS_REQUESTS = True

_HAS_DOWNLOAD_AUTHORIZATION = None


def require_requests(func):
    # A decorator to check for the 'requests' library before executing a function.
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not HAS_REQUESTS:
            raise ImportError("The 'requests' library is required but was not found.")
        return func(*args, **kwargs)
    return wrapper


@require_requests
def validate_local_file_checksum(client, local_filepath, query=None, download_link=None, deduplicate=None, search_alternatives=False):
    # Validates a local file against the remote checksum from the server.
    # Returns a dictionary with the validation status and additional context.
    result = {
        'validated': None,
        'message': '',
        'remote_filename': os.path.basename(local_filepath),
        'alternative_found': False
    }
    try:
        if query:
            file_details = search.find_file(client, query, deduplicate, search_alternatives=search_alternatives)
            download_link = file_details['download_link']
            result['remote_filename'] = file_details['filename']
            result['alternative_found'] = file_details['alternative_found']

        download_link_final = _resolve_download_link(client, download_link)

        try:
            # A HEAD request is not always supported; a streaming GET is more reliable.
            res = client.get(download_link_final, stream=True)
            headers = res.headers
            res.close()  # We only need the headers, so close the connection.
        finally:
            clear_download_key_cookie(client)

        remote_etag = headers.get('ETag')

        if not remote_etag:
            result['message'] = ("Checksum validation skipped: ETag header not found for URL '{0}'. Headers received: {1}"
                                 .format(download_link_final, headers))
            return result

        if _is_checksum_matched(local_filepath, remote_etag):
            result['validated'] = True
            result['message'] = 'Local file checksum is valid.'
        else:
            result['validated'] = False
            result['message'] = 'Local file checksum is invalid.'

    except exceptions.SapLaunchpadError as e:
        result['message'] = 'Checksum validation skipped: {0}'.format(e)
    return result


def check_similar_files(dest, filename):
    # Checks for similar files in the download path based on the given filename.
    if os.path.splitext(filename)[1]:
        filename_base = os.path.splitext(filename)[0]
        filename_pattern = os.path.join(dest, "**", filename_base + ".*")
    else:
        filename_pattern = os.path.join(dest, "**", filename + ".*")

    filename_similar = glob.glob(filename_pattern, recursive=True)

    if filename_similar:
        filename_similar_names = [os.path.basename(f) for f in filename_similar]
        return True, filename_similar_names
    else:
        return False, []


@require_requests
def _check_download_authorization(client):
    # Verifies that the authenticated user has the "Software Download" authorization.
    # Caches the result to avoid repeated API calls.
    global _HAS_DOWNLOAD_AUTHORIZATION
    if _HAS_DOWNLOAD_AUTHORIZATION is None:
        try:
            user_attributes = client.get(C.URL_ACCOUNT_ATTRIBUTES).json()
            sid = user_attributes['uid']

            url = C.URL_SERVICE_USER_ADMIN + f"/UserSet('{sid}')/UserExistingAuthorizationsSet"
            auth_response = client.get(url, headers={'Accept': 'application/json'}).json()

            authorization_objs = [r['ObjectId'] for r in auth_response['d']['results']]
            authorization_descs = [r['ObjectDesc'] for r in auth_response['d']['results']]

            _HAS_DOWNLOAD_AUTHORIZATION = "Software Download" in authorization_descs or any(
                x in authorization_objs for x in ["SWDOWNLOAD", "G_SOFTDOWN"]
            )
        except Exception as e:
            _HAS_DOWNLOAD_AUTHORIZATION = False

    if not _HAS_DOWNLOAD_AUTHORIZATION:
        raise exceptions.AuthorizationError(
            'User does not have proper authorization to download software. '
            'Please check authorizations at: https://launchpad.support.sap.com/#/user/authorizations'
        )


@require_requests
def is_download_link_available(client, url, retry=0):
    # Verifies if a download link is active and returns the final, resolved URL.
    # Returns None if the link is not available.
    # IMPORTANT: This function leaves download cookies in the session on success.
    try:
        final_url = _resolve_download_link(client, url)
        # A HEAD request is not always supported; a streaming GET is more reliable.
        res = client.get(final_url, stream=True)
        res.close()  # We only need the headers, so close the connection.
        content_header = res.headers.get('Content-Disposition')
        if content_header and 'attachment;' in content_header:
            return final_url
        return None
    except exceptions.DownloadError:
        return None


@require_requests
def _resolve_download_link(client, url, retry=0):
    # Resolves a tokengen URL to the final, direct download URL.
    # This encapsulates the SAML token exchange logic and includes retries.
    _check_download_authorization(client)
    endpoint = url

    # If a session for the download domain doesn't exist, we need to go through
    # the SAML SSO flow to get a download token.
    if not client.session.cookies.get('SESSIONID', domain='.softwaredownloads.sap.com'):
        try:
            meta = {}
            while 'SAMLResponse' not in meta:
                endpoint, meta = auth.get_sso_endpoint_meta(client, endpoint, data=meta)

            # This POST will result in a redirect to the actual file URL.
            res = client.post(endpoint, data=meta, stream=True)
            res.close()  # We don't need the content, just the redirect URL and cookies.
            return res.url
        except (HTTPError, ConnectionError) as e:
            client.session.cookies.clear(domain='.softwaredownloads.sap.com')
            # Retry on 403 (Forbidden) as it can be a temporary token issue.
            if (isinstance(e, HTTPError) and e.response.status_code != 403) or retry >= C.MAX_RETRY_TIMES:
                raise exceptions.DownloadError("Could not resolve download URL after {0} retries: {1}".format(C.MAX_RETRY_TIMES, e))

            time.sleep(60 * (retry + 1))
            return _resolve_download_link(client, url, retry + 1)

    # If a session already exists, the provided URL can be used directly.
    return endpoint


@require_requests
def stream_file_to_disk(client, url, filepath, retry=0, **kwargs):
    # Streams a large file to disk and verifies its checksum.
    kwargs.update({'stream': True})
    try:
        res = client.get(url, **kwargs)
        with open(filepath, 'wb') as f:
            for chunk in res.iter_content(chunk_size=1024 * 1024):  # 1MiB chunks
                f.write(chunk)
    except ConnectionError as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        if retry >= C.MAX_RETRY_TIMES:
            raise exceptions.DownloadError("Connection failed after {0} retries: {1}".format(C.MAX_RETRY_TIMES, e))
        time.sleep(60 * (retry + 1))
        return stream_file_to_disk(client, url, filepath, retry + 1, **kwargs)

    res.close()
    clear_download_key_cookie(client)

    checksum = res.headers.get('ETag', '').replace('"', '')
    if not checksum or _is_checksum_matched(filepath, checksum):
        return

    if os.path.exists(filepath):
        os.remove(filepath)

    if retry >= C.MAX_RETRY_TIMES:
        raise exceptions.DownloadError('Failed to download {0}: checksum mismatch after {1} retries'.format(url, C.MAX_RETRY_TIMES))
    return stream_file_to_disk(client, url, filepath, retry + 1, **kwargs)


def clear_download_key_cookie(client):
    # Clears download-specific cookies to prevent the cookie header from becoming too large.
    # The software download server generates a cookie for every single file.
    # If we don't clear it after download, the cookie header will become too long and the server will reject the request.
    for c in list(client.session.cookies):
        if c.domain == '.softwaredownloads.sap.com' and c.name != 'SESSIONID':
            client.session.cookies.clear(name=c.name, domain=c.domain, path='/')


def _is_checksum_matched(filepath, etag):
    # Verifies a file's checksum against an ETag, supporting MD5 and SHA256.
    # ETag values are often enclosed in double quotes, which must be removed.
    clean_etag = etag.strip('"')
    checksum = clean_etag.split(":")[0]
    hash_algo = hashlib.md5() if len(checksum) == 32 else hashlib.sha256()

    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096 * hash_algo.block_size), b""):
            hash_algo.update(chunk)
    return hash_algo.hexdigest() == checksum
