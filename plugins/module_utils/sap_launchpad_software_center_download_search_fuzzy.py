import csv
import logging

import requests

from . import constants as C
from .sap_api_common import _request
from .sap_id_sso import sap_sso_login


def search_software_fuzzy(query, max=None, csv_filename=None):
    """Returns a list of dict for the software results.
    """
    results = _search_software(query)
    num = 0

    softwares = []
    while True:
        for r in results:
            r = _remove_useless_keys(r)
            softwares.append(r)
        num += len(results)
        # quit if no results or results number reach the max
        if num == 0 or (max and num >= max):
            break
        query_string = _get_next_page_query(results[-1]['SearchResultDescr'])
        if not query_string:
            break
        try:
            results = _get_software_search_results(query_string)
        # Sometimes it responds 50x http error for some keywords,
        # but it's not the client's fault.
        except requests.exceptions.HTTPError as e:
            logging.warning(f'{e.response.status_code} HTTP Error occurred '
                            f'during pagination: {e.response.url}')
            break

    if csv_filename:
        _write_software_results(softwares, csv_filename)
        return
    return softwares


def _search_software(keyword, remove_useless_keys=False):
    params = {
        'SEARCH_MAX_RESULT': 500,
        'RESULT_PER_PAGE': 500,
        'SEARCH_STRING': keyword,
    }
    query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    results = _get_software_search_results(query_string)
    if remove_useless_keys:
        results = [_remove_useless_keys(r) for r in results]
    return results


def _get_software_search_results(query_string):
    url = C.URL_SOFTWARE_CENTER_SERVICE + '/SearchResultSet'
    query_url = '?'.join((url, query_string))

    headers = {'User-Agent': C.USER_AGENT_CHROME, 'Accept': 'application/json'}
    res = _request(query_url, headers=headers, allow_redirects=False).json()

    results = res['d']['results']
    return results


def _remove_useless_keys(result):
    keys = [
        'Title', 'Description', 'Infotype', 'Fastkey', 'DownloadDirectLink',
        'ContentInfoLink'
    ]
    return {k: result[k] for k in keys}


def _get_next_page_query(desc):
    if '|' not in desc:
        return None

    _, url = desc.split('|')
    return url.strip()


def _write_software_results(results, output):
    with open(output, 'w', newline='') as f:
        fieldsnames = [
            'Title', 'Description', 'Infotype', 'Fastkey',
            'DownloadDirectLink', 'ContentInfoLink'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldsnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
