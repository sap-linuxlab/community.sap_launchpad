import os

from .. import auth
from .. import exceptions
from ..client import ApiClient
from . import download
from . import search


def run_software_download(params):
    # The main "runner" function for the software_center_download module.
    # It orchestrates the entire process and returns a result dictionary.

    result = {
        'changed': False,
        'skipped': False,
        'failed': False,
        'msg': '',
        'filename': '',
        'alternative': False,
        'warnings': []
    }

    username = params.get('suser_id')
    password = params.get('suser_password')
    dest = params['dest']
    download_link = params.get('download_link')
    download_filename = params.get('download_filename')
    dry_run = params.get('dry_run')
    deduplicate = params.get('deduplicate')
    search_alternatives = params.get('search_alternatives')
    validate_checksum = params.get('validate_checksum')

    if params['search_query']:
        query = params['search_query']
    elif params['softwarecenter_search_query']:
        query = params['softwarecenter_search_query']
        result['warnings'].append("The 'softwarecenter_search_query' is deprecated. Use 'search_query' instead.")
    else:
        query = None

    if not (query or (download_link and download_filename)):
        result['failed'] = True
        result['msg'] = "Either 'search_query' or both 'download_link' and 'download_filename' must be provided."
        return result

    filename = query if query else download_filename
    result['filename'] = filename

    filepath = os.path.join(dest, filename)

    # --- Pre-authentication checks ---
    # If checksum validation is not requested, we can perform a quick check
    # for the file's existence and skip authentication if it's already there.
    if not validate_checksum:
        if os.path.exists(filepath):
            result['skipped'] = True
            result['msg'] = f"File already exists: {filename}"
            return result

        filename_similar_exists, filename_similar_names = download._check_similar_files(dest, filename)
        if filename_similar_exists:
            result['skipped'] = True
            result['msg'] = f"Similar file(s) already exist: {', '.join(filename_similar_names)}"
            return result

    client = ApiClient()
    try:
        auth.login(client, username, password)

        validation_result = None
        # --- Post-authentication checks ---
        # If checksum validation is requested, we perform the check here,
        # now that we have an authenticated session.
        if validate_checksum and os.path.exists(filepath):
            validation_result = download.validate_local_file_checksum(client, filepath, query=query, download_link=download_link, deduplicate=deduplicate)
            if validation_result['validated'] is True:
                result['skipped'] = True
                result['msg'] = f"File already exists and checksum is valid: {filename}"
                return result
            elif validation_result['validated'] is False:
                # The existing file is invalid, remove it to allow for re-download.
                # The final message will explain why the re-download occurred.
                os.remove(filepath)
            else:  # Validation could not be performed
                result['skipped'] = True
                result['msg'] = f"File already exists: {filename}. {validation_result['message']}"
                return result

        alternative_found = False
        if query:
            file_details = search.find_file(client, query, deduplicate, search_alternatives)
            download_link = file_details['download_link']
            download_filename = file_details['filename']
            alternative_found = file_details['alternative_found']

            result['filename'] = download_filename
            result['alternative'] = alternative_found

            alt_filepath = os.path.join(dest, download_filename)
            if filename != download_filename and os.path.exists(alt_filepath):
                if validate_checksum:
                    # We already have the download_link for the alternative file, so we can validate it directly.
                    validation_result = download.validate_local_file_checksum(client, alt_filepath, download_link=download_link)
                    if validation_result['validated'] is True:
                        result['skipped'] = True
                        result['msg'] = f"Alternative file {download_filename} already exists and checksum is valid."
                        return result
                    elif validation_result['validated'] is False:
                        # The existing alternative file is invalid, remove it to allow for re-download.
                        os.remove(alt_filepath)
                    else:  # Validation could not be performed
                        result['skipped'] = True
                        result['msg'] = f"Alternative file {download_filename} already exists. {validation_result['message']}"
                        return result
                else:
                    result['skipped'] = True
                    result['msg'] = f"File with correct/alternative name already exists: {download_filename}"
                    return result

        final_url = download._is_download_link_available(client, download_link)
        if final_url:
            if dry_run:
                msg = f"SAP Software is available to download: {download_filename}"
                if alternative_found:
                    msg = f"Alternative SAP Software is available to download: {download_filename} - original file {query} is not available"
                result['msg'] = msg
            else:
                # The link is already resolved, just download it.
                filepath = os.path.join(dest, download_filename)
                download._stream_file_to_disk(client, final_url, filepath)
                result['changed'] = True

                if validation_result and validation_result.get('validated') is False:
                    result['msg'] = f"Successfully re-downloaded {download_filename} due to an invalid checksum."
                elif alternative_found:
                    result['msg'] = f"Successfully downloaded alternative SAP software: {download_filename} - original file {query} is not available to download"
                else:
                    result['msg'] = f"Successfully downloaded SAP software: {download_filename}"
        else:
            result['failed'] = True
            result['msg'] = f"Download link for {download_filename} is not available."

    except exceptions.SapLaunchpadError as e:
        result['failed'] = True
        result['msg'] = str(e)
    except Exception as e:
        result['failed'] = True
        result['msg'] = f"An unexpected error occurred: {type(e).__name__} - {e}"
    finally:
        download._clear_download_key_cookie(client)

    return result