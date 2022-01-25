#!/user/bin/env python3
# coding: utf-8

import json
import logging
import os

from requests.auth import HTTPBasicAuth

from . import constants as C
from .sap_api_common import _request
from .sap_id_sso import _get_sso_endpoint_meta, sap_sso_login

logger = logging.getLogger(__name__)

_HAS_DOWNLOAD_AUTHORIZATION = None

def search_software_filename(name):
    """Return a single software that matched the filename
    """
    search_results = _search_software(name)
    softwares = [r for r in search_results if r['Title'] == name]
    if len(softwares) == 0:
        raise ValueError(f'no result found for {name}')
    if len(softwares) > 1:
        names = [s['Title'] for s in softwares]
        raise ValueError('more than one results were found: %s. '
                         'please use the correct full filename' % names)
    software = softwares[0]
    download_link, filename = software['DownloadDirectLink'], software['Title']
    return (download_link, filename)


def download_software(download_link, filename, output_dir):
    """Download software from DownloadDirectLink and save it as filename
    """
    # User might not have authorization to download software.
    if not _has_download_authorization():
        raise UserWarning(
            'You do not have proper authorization to download software, '
            'please check: '
            'https://launchpad.support.sap.com/#/user/authorizations')

    endpoint = download_link
    meta = {}
    while ('SAMLResponse' not in meta):
        endpoint, meta = _get_sso_endpoint_meta(endpoint, data=meta)

    filepath = os.path.join(output_dir, filename)

    _download_file(endpoint, filepath, data=meta)


def download_software_via_legacy_api(username, password, download_link,
                                     filename, output_dir):
    filepath = os.path.join(output_dir, filename)

    _download_file(download_link,
                   filepath,
                   auth=HTTPBasicAuth(username, password))


def _search_software(keyword):
    url = C.URL_SOFTWARE_CENTER_SERVICE + '/SearchResultSet'
    params = {
        'SEARCH_MAX_RESULT': 500,
        'RESULT_PER_PAGE': 500,
        'SEARCH_STRING': keyword,
    }
    query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    query_url = '?'.join((url, query_string))

    headers = {'User-Agent': C.USER_AGENT_CHROME, 'Accept': 'application/json'}
    results = []
    try:
        res = _request(query_url, headers=headers, allow_redirects=False)
        j = json.loads(res.text)
        results = j['d']['results']
    except json.JSONDecodeError:
        # When use has no authority to search some specified softwares,
        # it will return non-json response, which is actually expected.
        # So just return an empty list.
        logger.warning('Non-JSON response returned for software searching')
        logger.debug(res.text)

    return results


def _download_file(url, filepath, **kwargs):
    # Read response as stream, in case the file is huge.
    kwargs.update({'stream': True})
    with _request(url, **kwargs) as r:
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            # 1MiB Chunk
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)


def _has_download_authorization():
    global _HAS_DOWNLOAD_AUTHORIZATION
    if _HAS_DOWNLOAD_AUTHORIZATION is None:
        user_attributes = _request(C.URL_ACCOUNT_ATTRIBUTES).json()
        sid = user_attributes['uid']

        url = C.URL_SERVICE_USER_ADMIN + f"/UserSet('{sid}')/UserExistingAuthorizationsSet"
        j = _request(url, headers={'Accept': 'application/json'}).json()
        authorization_descs = [r['ObjectDesc'] for r in j['d']['results']]
        _HAS_DOWNLOAD_AUTHORIZATION = "Software Download" in authorization_descs
    return _HAS_DOWNLOAD_AUTHORIZATION
