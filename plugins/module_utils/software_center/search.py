from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import os
import re

from .. import constants as C
from ..exceptions import FileNotFoundError


def find_file(client, name, deduplicate, search_alternatives):
    # Main search function to find a software file.
    # It performs a direct search and, if requested, a fuzzy search for alternatives.
    # Returns a dictionary with file details.
    alternative_found = False

    # First, attempt a direct search for the exact filename.
    software_search = _search_software(client, name)
    software_filtered = [r for r in software_search if r['Title'] == name or r['Description'] == name]

    files_count = len(software_filtered)
    if files_count == 0:
        # If no exact match is found, and alternatives are requested, perform a fuzzy search.
        if not search_alternatives:
            raise FileNotFoundError('File "{0}" is not available. To find a replacement, enable "search_alternatives".'.format(name))

        software_fuzzy_found = _search_software_fuzzy(client, name)
        software_fuzzy_filtered, suggested_filename = _filter_fuzzy_search(software_fuzzy_found, name)
        if len(software_fuzzy_filtered) == 0:
            raise FileNotFoundError('File "{0}" is not available and no alternatives could be found.'.format(name))

        software_fuzzy_alternatives = software_fuzzy_filtered[0].get('Title')

        # The fuzzy search can return duplicates (e.g., .sar and .SAR).
        # We must perform another direct search on the best alternative and filter it.
        # duplicates like 70SWPM10SP43_2-20009701.sar for SWPM10SP43_2-20009701.SAR
        software_search_alternatives = _search_software(client, software_fuzzy_alternatives)
        software_search_alternatives_filtered = [
            file for file in software_search_alternatives
            if file.get('Title', '').startswith(suggested_filename)
        ]

        alternatives_count = len(software_search_alternatives_filtered)
        if alternatives_count == 0:
            raise FileNotFoundError('File "{0}" is not available and no alternatives could be found.'.format(name))
        elif alternatives_count > 1 and deduplicate == '':
            names = [s['Title'] for s in software_search_alternatives_filtered]
            raise FileNotFoundError('More than one alternative was found: {0}. Please use a more specific filename.'.format(", ".join(names)))
        elif alternatives_count > 1 and deduplicate == 'first':
            software_found = software_search_alternatives_filtered[0]
            alternative_found = True
        elif alternatives_count > 1 and deduplicate == 'last':
            software_found = software_search_alternatives_filtered[alternatives_count - 1]
            alternative_found = True
        else:
            # Default to the first alternative found.
            software_found = software_search_alternatives_filtered[0]
            alternative_found = True

    elif files_count > 1 and deduplicate == '':
        # Handle cases where the direct search returns multiple exact matches.
        names = [s['Title'] for s in software_filtered]
        raise FileNotFoundError('More than one result was found: {0}. Please use the correct full filename.'.format(", ".join(names)))
    elif files_count > 1 and deduplicate == 'first':
        software_found = software_filtered[0]
    elif files_count > 1 and deduplicate == 'last':
        software_found = software_filtered[files_count - 1]
    else:
        # The ideal case: exactly one result was found.
        software_found = software_filtered[0]

    return {
        'download_link': software_found['DownloadDirectLink'],
        'filename': _get_valid_filename(software_found),
        'alternative_found': alternative_found
    }


def _search_software(client, keyword):
    # Performs a direct search for a software file by keyword.
    url = C.URL_SOFTWARE_CENTER_SERVICE + '/SearchResultSet'
    params = {
        'SEARCH_MAX_RESULT': 500,
        'RESULT_PER_PAGE': 500,
        'SEARCH_STRING': keyword,
    }
    headers = {'User-Agent': C.USER_AGENT_CHROME, 'Accept': 'application/json'}
    results = []
    try:
        res = client.get(url, params=params, headers=headers, allow_redirects=False)
        json_data = res.json()
        results = json_data.get('d', {}).get('results', [])
    except json.JSONDecodeError:
        # This can happen if the user lacks authorization for a specific file.
        # The API returns non-JSON, so we return an empty list.
        pass

    return results


def _search_software_fuzzy(client, query):
    # Executes a fuzzy search using the unique software ID from the filename.
    filename_base = os.path.splitext(query)[0]

    # This excludes unique files without ID like: S4CORE105_INST_EXPORT_1.zip
    if '-' not in filename_base:
        return []

    filename_id = filename_base.split('-')[-1]
    results = _search_software(client, filename_id)
    num = 0

    fuzzy_results = []
    while True:
        for r in results:
            r = _remove_useless_keys(r)
            fuzzy_results.append(r)
        num += len(results)

        if not results:
            break

        query_string = _get_next_page_query(results[-1]['SearchResultDescr'])
        if not query_string:
            break

        url = C.URL_SOFTWARE_CENTER_SERVICE + '/SearchResultSet'
        query_url = '?'.join((url, query_string))
        headers = {'User-Agent': C.USER_AGENT_CHROME, 'Accept': 'application/json'}
        results = client.get(query_url, headers=headers, allow_redirects=False).json().get('d', {}).get('results', [])

    return fuzzy_results


def _filter_fuzzy_search(fuzzy_results, filename):
    # Filters fuzzy search output using the original filename.
    if '*' in filename:
        prefix, suffix = filename.split('*')
        suffix_base = os.path.splitext(suffix)[0]
        fuzzy_results_filtered = [
            file for file in fuzzy_results
            if file.get('Title', '').startswith(prefix) and os.path.splitext(file.get('Title', ''))[0].endswith(suffix_base)
        ]
        suggested_filename = prefix
    else:
        suggested_filename = _prepare_search_filename_specific(filename)
        fuzzy_results_filtered = [
            file for file in fuzzy_results
            if file.get('Title', '').startswith(suggested_filename)
        ]

        if len(fuzzy_results_filtered) == 0:
            suggested_filename = _prepare_search_filename_nonspecific(filename)
            fuzzy_results_filtered = [
                file for file in fuzzy_results
                if file.get('Title', '').startswith(suggested_filename)
            ]

    fuzzy_results_sorted = _sort_fuzzy_results(fuzzy_results_filtered, filename)
    return fuzzy_results_sorted, suggested_filename


def _prepare_search_filename_specific(filename):
    # Prepares a suggested search keyword for known products specific to SPS version.
    filename_base = os.path.splitext(filename)[0]
    filename_name = filename_base.rsplit('_', 1)[0]

    for swpm_version in ("70SWPM1", "70SWPM2", "SWPM1", "SWPM2"):
        if filename_base.startswith(swpm_version):
            return swpm_version

    # Example: SUM11SP04_2-80006858.SAR returns SUM11SP04
    if filename_base.startswith('SUM'):
        return filename.split('-')[0].split('_')[0]

    # Example: DBATL740O11_48-80002605.SAR returns DBATL740O11
    elif filename_base.startswith('DBATL'):
        return filename.split('-')[0].split('_')[0]

    # Example: IMDB_AFL20_077_0-80002045.SAR returns IMDB_AFL20_077
    # Example: IMDB_AFL100_102P_41-10012328.SAR returns MDB_AFL100_102P
    elif filename_base.startswith('IMDB_AFL'):
        return "_".join(filename.split('-')[0].split('_')[:3])

    # Example: IMDB_CLIENT20_021_31-80002082.SAR returns IMDB_CLIENT20_021
    elif filename_base.startswith('IMDB_CLIENT'):
        return "_".join(filename.split('-')[0].split('_')[:3])

    # Example: IMDB_LCAPPS_122P_3300-20010426.SAR returns IMDB_LCAPPS_122
    elif filename_base.startswith('IMDB_LCAPPS_1'):
        filename_parts = filename.split('-')[0].rsplit('_', 2)
        return "{0}_{1}".format(filename_parts[0], filename_parts[1][:3])

    # Example: IMDB_LCAPPS_2067P_400-80002183.SAR returns IMDB_LCAPPS_206
    elif filename_base.startswith('IMDB_LCAPPS_2'):
        filename_parts = filename.split('-')[0].rsplit('_', 2)
        return "{0}_{1}".format(filename_parts[0], filename_parts[1][:3])

    # Example: IMDB_SERVER20_067_4-80002046.SAR returns IMDB_SERVER20_06 (SPS06)
    elif filename_base.startswith('IMDB_SERVER'):
        filename_parts = filename.split('-')[0].rsplit('_', 2)
        return "{0}_{1}".format(filename_parts[0], filename_parts[1][:2])

    # Example: SAPEXE_100-80005374.SAR returns SAPEXE_100
    elif filename_base.startswith('SAPEXE'):
        return filename_base.split('-')[0]

    # Example: SAPHANACOCKPIT02_0-70002300.SAR returns SAPHANACOCKPIT02 (SPS02)
    elif filename_base.startswith('SAPHANACOCKPIT'):
        return filename_base.split('-')[0].rsplit('_', 1)[0]
    else:
        return filename_name


def _prepare_search_filename_nonspecific(filename):
    # Prepares a suggested search keyword for known products non-specific to SPS version.
    filename_base = os.path.splitext(filename)[0]
    filename_name = filename_base.rsplit('_', 1)[0]

    # Example: SUM11SP04_2-80006858.SAR returns SUM11
    if filename_base.startswith('SUM'):
        if filename_base.startswith('SUMHANA'):
            return 'SUMHANA'
        elif filename_base[3:5].isdigit():
            return filename_base[:5]

    # Example: DBATL740O11_48-80002605.SAR returns DBATL740O11
    elif filename_base.startswith('DBATL'):
        return filename.split('-')[0].split('_')[0]

    # Example: IMDB_AFL20_077_0-80002045.SAR returns IMDB_AFL20
    # Example: IMDB_AFL100_102P_41-10012328.SAR returns IMDB_AFL100
    elif filename_base.startswith('IMDB_AFL'):
        return "_".join(filename.split('-')[0].split('_')[:2])

    # Example: IMDB_CLIENT20_021_31-80002082.SAR returns IMDB_CLIENT
    elif filename_base.startswith('IMDB_CLIENT'):
        return 'IMDB_CLIENT'

    # Example: IMDB_LCAPPS_122P_3300-20010426.SAR returns IMDB_LCAPPS
    elif filename_base.startswith('IMDB_LCAPPS'):
        return "_".join(filename.split('-')[0].split('_')[:2])

    # Example: IMDB_SERVER20_067_4-80002046.SAR returns IMDB_SERVER20
    elif filename_base.startswith('IMDB_SERVER'):
        return "_".join(filename.split('-')[0].split('_')[:2])

    # Example: SAPHANACOCKPIT02_0-70002300.SAR returns SAPHANACOCKPIT
    elif filename_base.startswith('SAPHANACOCKPIT'):
        return 'SAPHANACOCKPIT'

    # Example: SAPHOSTAGENT61_61-80004831.SAR returns SAPHOSTAGENT
    elif filename_base.startswith('SAPHOSTAGENT'):
        return 'SAPHOSTAGENT'

    return filename


def _sort_fuzzy_results(fuzzy_results_filtered, filename):
    # Sorts results of fuzzy search for known nonstandard versions.
    if _get_numeric_search_keyword(filename):
        software_fuzzy_sorted = sorted(
            fuzzy_results_filtered,
            key=lambda item: _get_numeric_search_keyword(item.get('Title', '')),
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
    # Extracts integer value of version from filename.
    match = re.search(r'_(\d+)-', filename)
    if match:
        return int(match.group(1))
    else:
        return None


def _remove_useless_keys(result):
    # Filters a result dictionary to keep only essential keys.
    keys = [
        'Title', 'Description', 'Infotype', 'Fastkey', 'DownloadDirectLink',
        'ContentInfoLink'
    ]
    return {k: result[k] for k in keys}


def _get_next_page_query(desc):
    # Extracts the next page query URL for paginated search results.
    if '|' not in desc:
        return None
    _prefix, url = desc.split('|')
    return url.strip()


def _get_valid_filename(software_found):
    # Ensures that CD Media have correct filenames from description.
    # The API sometimes returns a numeric ID as the 'Title' for CD Media, while the actual filename is in the 'Description'.
    # Example: S4CORE105_INST_EXPORT_1.zip downloads as 19118000000000004323
    if re.match(r'^\d+$', software_found['Title']):
        if software_found['Description'] and ' ' not in software_found['Description']:
            return software_found['Description']
        else:
            return software_found['Title']
    else:
        return software_found['Title']
