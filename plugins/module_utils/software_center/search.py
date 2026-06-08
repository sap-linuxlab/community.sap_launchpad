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
        # Gather facts about filename for decision making.
        # Check if file format supports alternative search (has dash and extension).
        wildcard_count = name.count('*')
        has_extension = '.' in name
        has_dash = '-' in name

        # More than one wildcards are not allowed.
        if wildcard_count > 1:
            raise FileNotFoundError(
                f'File "{name}" is not available.\n'
                f'Only one wildcard (*) is allowed in the search query.'
            )

        # No wildcards were detected.
        if wildcard_count == 0:
            # File format doesn't support fuzzy search.
            # No reason to offer search_alternatives or wildcard suggestions.
            if not (has_dash and has_extension):
                raise FileNotFoundError(
                    f'File "{name}" is not available.'
                )

            # File format supports fuzzy, suggest search_alternatives if disabled.
            if not search_alternatives:
                raise FileNotFoundError(
                    f'File "{name}" is not available.\n'
                    f'To search for different versions, '
                    f'enable "search_alternatives" and use wildcard format.\n'
                    f'Format: "PREFIX*-ID.EXT"\n'
                    f'Example: "SAPEXE_1*-80002630.SAR"'
                )

        # Wildcard detected, but search_alternatives is disabled.
        if not search_alternatives:
            raise FileNotFoundError(
                f'File "{name}" is not available.\n'
                f'Wildcard search requires search_alternatives to be enabled.'
            )

        # One wildcard was detected, validate wildcard position and format.
        if wildcard_count > 0:
            # We have to ensure that only correct pattern is accepted: PREFIX*-ID.EXT
            # Having wildcard in other places would result in API timeouts
            # or files for different components and platforms.
            # [^-]+ = one or more non-dash characters
            # \* = wildcard character
            # - = single dash separator
            # \d{8} = exactly 8 digits (SAP file IDs are always 8 digits)
            # \. = dot character
            # [a-zA-Z]+ = file extension (SAR, EXE, rpm, sar, etc.)
            wildcard_pattern = r'^[^-]+\*-\d{8}\.[a-zA-Z]+$'
            if not re.match(wildcard_pattern, name):
                raise FileNotFoundError(
                    f'File "{name}" is not available.\n'
                    f'Wildcard queries must follow specific format.\n'
                    f'Format: "PREFIX*-ID.EXT" where:\n'
                    f' - PREFIX must have at least one character before wildcard\n'
                    f' - Wildcard (*) must be in PREFIX position only\n'
                    f' - Single dash (-) separates prefix and ID\n'
                    f' - ID must be exactly 8 digits\n'
                    f'Valid: "SAPEXE_1*-80002630.SAR"\n'
                    f'Invalid: "*-80002630.SAR" (no prefix - too broad)\n'
                    f'Invalid: "SAPEXE_1-*.SAR" (wildcard in ID position)\n'
                    f'Invalid: "igsexe_*-7000.sar" (ID must be 8 digits, not 4)'
                )

        try:
            software_fuzzy_found = _search_software_fuzzy(client, name)
        except Exception as e:
            # Handle cases where API returns errors due to overly broad queries
            if 'RetryError' in str(type(e).__name__) or '500 error' in str(e):
                if wildcard_count > 0:
                    raise FileNotFoundError(
                        f'File "{name}" is not available.\n'
                        f'The search query may be too broad, or SAP API is experiencing issues.\n'
                        f'Options:\n'
                        f' - Use a more specific wildcard pattern\n'
                        f'   Example: Instead of "SAPEXE_9*-80002630.SAR", use "SAPEXE_900*-80002630.SAR"\n'
                        f' - Wait and retry later when SAP API is available again'
                    )
            # Re-raise other exceptions
            raise

        software_fuzzy_filtered, suggested_filename = _filter_fuzzy_search(software_fuzzy_found, name)
        if len(software_fuzzy_filtered) == 0:
            raise FileNotFoundError(
                f'File "{name}" is not available '
                f'and no alternatives could be found.'
            )

        # Fuzzy search already filtered by prefix and ID.
        # Now filter by extension to handle different file types (.SAR vs .rpm)
        # Extract extension from original query
        file_right_side = name.split('-')[-1]  # 80004822.SAR
        file_id = file_right_side.split('.')[0]  # 80004822
        file_extension = file_right_side[len(file_id):]  # .SAR

        software_search_alternatives_filtered = [
            file for file in software_fuzzy_filtered
            if file.get('Title', '').upper().endswith(file_extension.upper())
        ]

        alternatives_count = len(software_search_alternatives_filtered)
        if alternatives_count == 0:
            raise FileNotFoundError(f'File "{name}" is not available and no alternatives could be found.')
        elif alternatives_count > 1 and deduplicate == '':
            names = [s['Title'] for s in software_search_alternatives_filtered]

            first_option = software_search_alternatives_filtered[0]['Title']
            last_option = software_search_alternatives_filtered[-1]['Title']

            raise FileNotFoundError(
                f'More than one alternative was found: '
                f'{", ".join(names)}.\n'
                f'Please use a more specific filename '
                f'or set deduplicate parameter.\n'
                f'Options for deduplicate:\n'
                f' - "first" returns oldest version ({first_option})\n'
                f' - "last" returns newest version ({last_option})'
            )
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

    # There should never be case when exact file is found with more than one match,
    # but handle it just in case.
    elif files_count > 1 and deduplicate == '':
        # Handle cases where the direct search returns multiple exact matches.
        names = [s['Title'] for s in software_filtered]

        first_option = software_filtered[0]['Title']
        last_option = software_filtered[-1]['Title']

        raise FileNotFoundError(
            f'More than one result was found: {", ".join(names)}.\n'
            f'Please use the correct full filename '
            f'or set deduplicate parameter.\n'
            f'Options for deduplicate:\n'
            f' - "first" returns oldest version ({first_option})\n'
            f' - "last" returns newest version ({last_option})'
        )
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
    # Executes a fuzzy search to find alternative versions.
    # Strategy: Try prefix search first (more specific), fallback to ID search if needed.
    filename_base = os.path.splitext(query)[0]

    # This excludes unique files without ID like: S4CORE105_INST_EXPORT_1.zip
    if '-' not in filename_base:
        return []

    # Extract ID and prepare suggested filename prefix
    filename_id = filename_base.split('-')[-1]
    suggested_filename, suggested_filename_next = _prepare_search_filename(query)
    has_wildcard = '*' in query

    fuzzy_results = []

    # For exact filenames, try prefix search first (more targeted, avoids API limits)
    if not has_wildcard:
        # Search by suggested prefix
        results = _search_software(client, suggested_filename)

        # Filter results by ID to ensure correct platform
        for r in results:
            if f'-{filename_id}' in r.get('Title', ''):
                fuzzy_results.append(_remove_useless_keys(r))

        # If empty and suggested_filename_next exists, try incremented version
        if len(fuzzy_results) == 0 and suggested_filename_next:
            results = _search_software(client, suggested_filename_next)
            for r in results:
                if f'-{filename_id}' in r.get('Title', ''):
                    fuzzy_results.append(_remove_useless_keys(r))

    # For wildcards or if prefix search found nothing, use ID-based search
    if has_wildcard or len(fuzzy_results) == 0:
        results = _search_software(client, filename_id)
        num = 0

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
        suggested_filename, suggested_filename_next = _prepare_search_filename(filename)

        # Create result list with same version if available.
        fuzzy_results_filtered = [
            file for file in fuzzy_results
            if file.get('Title', '').startswith(suggested_filename)
        ]

        # Attempt to create result list with incremented version.
        if len(fuzzy_results_filtered) == 0 and suggested_filename_next:
            fuzzy_results_filtered = [
                file for file in fuzzy_results
                if file.get('Title', '').startswith(suggested_filename_next)
            ]
            # Update return suggested filename to incremented version if alternatives are found with it.
            if len(fuzzy_results_filtered) > 0:
                suggested_filename = suggested_filename_next

    fuzzy_results_sorted = _sort_fuzzy_results(fuzzy_results_filtered)
    return fuzzy_results_sorted, suggested_filename


def _prepare_search_filename(filename):
    # Prepares a suggested search keyword for known products specific to SPS version.
    # Filename without extension.
    filename_base = os.path.splitext(filename)[0]

    # Filename before first '-' character.
    filename_main = filename_base.split('-')[0]

    # Filename split into individual components: ['IMDB', 'AFL100', '102P', '41']
    filename_parts = filename_main.split('_')

    # Example: SWPM20SP23_4-70003174.SAR returns SWPM20SP23
    for swpm_version in ("70SWPM1", "70SWPM2", "SWPM1", "SWPM2"):
        if filename_base.startswith(swpm_version):
            suggested = filename_parts[0]
            return suggested, _increment_last_digits(suggested)

    # Example: SUM11SP04_2-80006858.SAR returns SUM11SP04
    # Example: DBATL740O11_48-80002605.SAR returns DBATL740O11
    if filename_base.startswith(('SUM', 'DBATL')):
        suggested = filename_parts[0]
        return suggested, _increment_last_digits(suggested)

    # Revision version will be kept to ensure correct component versions.
    # Example: IMDB_SERVER20_067_4-80002046.SAR returns IMDB_SERVER20_067 (Rev 67)
    # Example: IMDB_AFL20_077_0-80002045.SAR returns IMDB_AFL20_077 (Rev 77)
    # Example: IMDB_AFL100_102P_41-10012328.SAR returns MDB_AFL100_102 (Rev 102)
    # Example: IMDB_LCAPPS_122P_3300-20010426.SAR returns IMDB_LCAPPS_122 (Rev 122)
    # Example: IMDB_LCAPPS_2067P_400-80002183.SAR returns IMDB_LCAPPS_2067 (Rev 67)
    elif filename_base.startswith(('IMDB_SERVER', 'IMDB_AFL', 'IMDB_LCAPPS_1', 'IMDB_LCAPPS_2')):
        # Remove P from the 3rd element (index 2) to improve fuzzy search.
        if len(filename_parts) > 2:
            filename_parts[2] = filename_parts[2].rstrip('Pp')
        # Re-join the first three elements -> "IMDB_AFL100_102"
        suggested = "_".join(filename_parts[:3])
        return suggested, None

    # Example: IMDB_CLIENT20_021_31-80002082.SAR returns IMDB_CLIENT20_021
    elif filename_base.startswith('IMDB_CLIENT'):
        if len(filename_parts) > 2:
            filename_parts[2] = filename_parts[2].rstrip('Pp')
        suggested = "_".join(filename_parts[:3])
        return suggested, _increment_last_digits(suggested)

    # Example: SAPEXE_100-80005374.SAR returns SAPEXE_100
    elif filename_base.startswith('SAPEXE'):
        suggested = filename_main
        return suggested, _increment_last_digits(suggested)

    # Example: SAPHANACOCKPIT02_0-70002300.SAR returns SAPHANACOCKPIT02 (SPS02)
    # Example: SAPHOSTAGENT61_61-80004831.SAR returns SAPHOSTAGENT61
    elif filename_base.startswith(('SAPHANACOCKPIT', 'SAPHOSTAGENT')):
        suggested = filename_main.rsplit('_', 1)[0]
        return suggested, _increment_last_digits(suggested)

    else:
        return filename_main, None


def _sort_fuzzy_results(fuzzy_results_filtered):
    # Numerical sorts for fuzzy search results.
    # Check if results contain numeric versions.
    # Ascending: first=oldest, last=newest
    has_numeric = (
        fuzzy_results_filtered and
        _get_numeric_search_keyword(
            fuzzy_results_filtered[0].get('Title', '')
        ) is not None
    )
    if has_numeric:
        software_fuzzy_sorted = sorted(
            fuzzy_results_filtered,
            key=lambda item: (
                _get_numeric_search_keyword(item.get('Title', '')) or (0, 0)
            ),
            reverse=False,
        )
    else:
        software_fuzzy_sorted = sorted(
            fuzzy_results_filtered,
            key=lambda item: item.get('Title', ''),
            reverse=False,
        )
    return software_fuzzy_sorted


def _get_numeric_search_keyword(filename):
    # Extracts version tuple from filename for sorting.
    # Returns tuple (major, minor) to handle cases like SP24_0, SP24_1, SP24_10.
    # Priority: extract the most significant version numbers.

    # For SP-based files: extract (SP_version, patch_number)
    # SWPM20SP23_4-ID -> (23, 4), SWPM20SP24_1-ID -> (24, 1)
    sp_match = re.search(r'SP(\d+)_(\d+)-', filename)
    if sp_match:
        return (int(sp_match.group(1)), int(sp_match.group(2)))

    # For HANA files with 3-part versions: extract (revision, patch)
    # IMDB_SERVER20_067_4-ID -> (67, 4), IMDB_LCAPPS_2067P_400-ID -> (2067, 400)
    hana_match = re.search(r'_(\d+)P?_(\d+)-', filename)
    if hana_match:
        return (int(hana_match.group(1)), int(hana_match.group(2)))

    # For all other files: extract version as (version, 0) for consistent tuple sorting
    # SAPEXE_800-ID -> (800, 0), SAPHOSTAGENT61_61-ID -> (61, 0), igsexe_13-ID -> (13, 0)
    match = re.search(r'_(\d+)-', filename)
    if match:
        return (int(match.group(1)), 0)

    return None


def _remove_useless_keys(result):
    # Filters a result dictionary to keep only essential keys.
    keys = [
        'Title', 'Description', 'Infotype', 'Fastkey', 'DownloadDirectLink',
        'ContentInfoLink', 'SearchResultDescr'
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


def _increment_last_digits(suggested_filename):
    """
    Increments the trailing digits of a clean, known filename search term.
    Assumes the string always ends with a numeric character.
    """
    if not suggested_filename:
        return None

    # If the last 2 characters are both digits (e.g., "06", "22", "99")
    if len(suggested_filename) >= 2 and suggested_filename[-2:].isdigit():
        last_digits = suggested_filename[-2:]

        # We cannot increase 99 since we focus on 2 digits only.
        if last_digits == '99':
            return None

        # int() strips zero so zfill creates two 2 digit again.
        new_digits = str(int(last_digits) + 1).zfill(2)
        return suggested_filename[:-2] + new_digits

    # If only the very last character is a digit (e.g., "SPS4", "FILE_1")
    elif suggested_filename[-1].isdigit():
        last_digit = suggested_filename[-1]

        # We cannot increase 9 if we do not have 2 last digits.
        if last_digit == '9':
            return None

        new_digit = str(int(last_digit) + 1)
        return suggested_filename[:-1] + new_digit

    return None
