import csv
import logging
import os
import re

import requests

from . import constants as C
from .sap_api_common import _request


def search_software_fuzzy(query, max=None, csv_filename=None):
    """
    Execute fuzzy search using Unique Software ID instead of name.
    ID is unique to Product and Platform combination. 
    Example of shared ID 80002616:
    - SYBCTRL_1440-80002616.SAR
    - SYBCTRL_1436-80002616.SAR
    
    Args:
        query: The filename name to check (e.g. 'SYBCTRL_1440-80002616.SAR').

    Returns:
        The list of dict for the software results.
        Empty list is returned if query does not contain ID.
    """
    # Format query to split filename.
    filename_base = os.path.splitext(query)[0]  # Remove extension

    # Ensure that fuzzy search is run only for valid IDs.
    # This excludes unique files without ID like: S4CORE105_INST_EXPORT_1.zip
    if '-' in filename_base:
        filename_id = filename_base.split('-')[-1]  # Split id from filename
    else:
        return []

    results = _search_software(filename_id)
    num = 0

    fuzzy_results = []
    while True:
        for r in results:
            r = _remove_useless_keys(r)
            fuzzy_results.append(r)
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
        _write_software_results(fuzzy_results, csv_filename)
        return
    return fuzzy_results


def filter_fuzzy_search(fuzzy_results, filename):
    """
    Filter fuzzy search output using filename.
    
    Args:
        fuzzy_results: Output of search_software_fuzzy.
        filename: The filename name to check

    Returns:
        fuzzy_results_sorted: The list of files that match the filter criteria, sorted by 'Title' in descending order.
        suggested_filename: Return generated keyword for further reuse after API call.
    """

    # Prepare filtered list for specific SPS
    suggested_filename = _prepare_search_filename_specific(filename)

    fuzzy_results_filtered = [
        file for file in fuzzy_results
        if file.get('Title', '').startswith(suggested_filename)
    ]

    # Repeat filtering without specific SPS
    if len(fuzzy_results_filtered) == 0:
        suggested_filename = _prepare_search_filename_nonspecific(filename)

        fuzzy_results_filtered = [
            file for file in fuzzy_results
            if file.get('Title', '').startswith(suggested_filename)
        ]

    # fuzzy_results_sorted = sorted(fuzzy_results_filtered, key=lambda item: item.get('Title', ''), reverse=True)
    fuzzy_results_sorted =_sort_fuzzy_results(fuzzy_results_filtered, filename)

    return fuzzy_results_sorted, suggested_filename


def _prepare_search_filename_specific(filename):
    """   
    Prepare suggested search keyword for known products specific to SPS version.

    Args:
        filename: The filename name to check

    Returns:
        Suggested filename to filter fuzzy search.
    """

    # Format query to split filename.
    filename_base = os.path.splitext(filename)[0]  # Remove extension
    filename_name = filename_base.rsplit('_', 1)[0]  # Split software name from version
    # Following filenames will be processed using default filename_name split.
    # Return SYBCTRL for SYBCTRL_1436-80002616.SAR
    # Return SMDA720 for SMDA720_SP11_22-80003641.SAR


    for swpm_version in ("70SWPM1", "70SWPM2", "SWPM1", "SWPM2"):
        if filename_base.startswith(swpm_version):
            return swpm_version

    # Return SUM11SP04 for SUM11SP04_2-80006858.SAR
    if filename_base.startswith('SUM'):
        return filename.split('-')[0].split('_')[0]

    # Return DBATL740O11 for DBATL740O11_48-80002605.SAR
    elif filename_base.startswith('DBATL'):
        return filename.split('-')[0].split('_')[0]

    # Return IMDB_AFL20_077 for IMDB_AFL20_077_0-80002045.SAR
    # Return IMDB_AFL100_102P for IMDB_AFL100_102P_41-10012328.SAR
    elif filename_base.startswith('IMDB_AFL'):
        return "_".join(filename.split('-')[0].split('_')[:3])

    # Return IMDB_CLIENT20_021 for IMDB_CLIENT20_021_31-80002082.SAR
    elif filename_base.startswith('IMDB_CLIENT'):
        return "_".join(filename.split('-')[0].split('_')[:3])

    # IMDB_LCAPPS for SAP HANA 1.0
    # Return IMDB_LCAPPS_122 for IMDB_LCAPPS_122P_3300-20010426.SAR
    elif filename_base.startswith('IMDB_LCAPPS_1'):
        filename_parts = filename.split('-')[0].rsplit('_', 2)
        return f"{filename_parts[0]}_{filename_parts[1][:3]}"

    # IMDB_LCAPPS for SAP HANA 2.0
    # Return IMDB_LCAPPS_206 for IMDB_LCAPPS_2067P_400-80002183.SAR
    elif filename_base.startswith('IMDB_LCAPPS_2'):
        filename_parts = filename.split('-')[0].rsplit('_', 2)
        return f"{filename_parts[0]}_{filename_parts[1][:3]}"

    # Return IMDB_SERVER20_06 (SPS06) for IMDB_SERVER20_067_4-80002046.SAR
    elif filename_base.startswith('IMDB_SERVER'):
        filename_parts = filename.split('-')[0].rsplit('_', 2)
        return f"{filename_parts[0]}_{filename_parts[1][:2]}"

    # Return SAPEXE_100 for SAPEXE_100-80005374.SAR
    elif filename_base.startswith('SAPEXE'):
        return filename_base.split('-')[0]

    # Return SAPHANACOCKPIT02 (SPS02) for SAPHANACOCKPIT02_0-70002300.SAR
    elif filename_base.startswith('SAPHANACOCKPIT'):
        return filename_base.split('-')[0].rsplit('_', 1)[0]

    # Return unchanged filename_name
    else:
        return filename_name


def _prepare_search_filename_nonspecific(filename):
    """   
    Prepare suggested search keyword for known products nonspecific to SPS version.

    Args:
        filename: The filename name to check

    Returns:
        Suggested filename to filter fuzzy search.
    """

    # Format query to split filename.
    filename_base = os.path.splitext(filename)[0]  # Remove extension
    filename_name = filename_base.rsplit('_', 1)[0]  # Split software name from version

    # Return SUM11 for SUM11SP04_2-80006858.SAR
    if filename_base.startswith('SUM'):
        if filename_base.startswith('SUMHANA'):
            return 'SUMHANA'
        elif filename_base[3:5].isdigit():  # Allow only SUM and 2 digits
            return filename_base[:5]

    # Return DBATL740O11 for DBATL740O11_48-80002605.SAR
    elif filename_base.startswith('DBATL'):
        return filename.split('-')[0].split('_')[0]

    # Return IMDB_AFL20 for IMDB_AFL20_077_0-80002045.SAR
    # Return IMDB_AFL100 for IMDB_AFL100_102P_41-10012328.SAR
    elif filename_base.startswith('IMDB_AFL'):
        return "_".join(filename.split('-')[0].split('_')[:2])

    # Return IMDB_CLIENT for IMDB_CLIENT20_021_31-80002082.SAR
    elif filename_base.startswith('IMDB_CLIENT'):
        return 'IMDB_CLIENT'

    # Return IMDB_LCAPPS for IMDB_LCAPPS_122P_3300-20010426.SAR
    elif filename_base.startswith('IMDB_LCAPPS'):
        return "_".join(filename.split('-')[0].split('_')[:2])

    # Return IMDB_SERVER20 for IMDB_SERVER20_067_4-80002046.SAR
    elif filename_base.startswith('IMDB_SERVER'):
        return "_".join(filename.split('-')[0].split('_')[:2])

    # Return SAPHANACOCKPIT for SAPHANACOCKPIT02_0-70002300.SAR
    elif filename_base.startswith('SAPHANACOCKPIT'):
        return 'SAPHANACOCKPIT'

    # Return SAPHOSTAGENT for SAPHOSTAGENT61_61-80004831.SAR
    elif filename_base.startswith('SAPHOSTAGENT'):
        return 'SAPHOSTAGENT'

    # Return unchanged filename_name
    else:
        return filename_name


def _sort_fuzzy_results(fuzzy_results_filtered, filename):
    """   
    Sort results of fuzzy search for known nonstandard versions.
    Example:
        IMDB_LCAPPS_122P_3500-20010426.SAR, IMDB_LCAPPS_122P_600-70001332.SAR

    Args:
        fuzzy_results_filtered: The list of filtered fuzzy results.
        filename: The filename name to check.

    Returns:
        Ordered list of fuzzy results, based on known nonstandard versions.
    """

    if _get_numeric_search_keyword(filename):
        software_fuzzy_sorted = sorted(
            fuzzy_results_filtered,
            key= lambda item: _get_numeric_search_keyword(item.get('Title', '')),
            reverse=True,
        )
    else:
        software_fuzzy_sorted = sorted(
            fuzzy_results_filtered,
            key=lambda item: item.get('Title', ''),
            reverse=True,
    )

    return software_fuzzy_sorted


def _get_numeric_search_keyword(filename):
    """   
    Extract integer value of version from filename.

    Args:
        filename: The filename name to check.

    """
    match = re.search(r'_(\d+)-', filename)
    if match:
        return int(match.group(1))
    else:
        return None


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
