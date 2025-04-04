# -*- coding: utf-8 -*-

# SAP software download module

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: software_center_download

short_description: SAP software download

version_added: 1.0.0

options:
  suser_id:
    description:
      - SAP S-User ID.
    required: true
    type: str
  suser_password:
    description:
      - SAP S-User Password.
    required: true
    type: str
  softwarecenter_search_query:
    description:
      - "Deprecated. Use 'search_query' instead."
    required: false
    type: str
    deprecated:
        alternative: search_query
        removed_in: "1.2.0"
  search_query:
    description:
      - Filename of the SAP software to download.
    required: false
    type: str
  download_link:
    description:
      - Direct download link to the SAP software.
    required: false
    type: str
  download_filename:
    description:
      - Download filename of the SAP software.
    required: false
    type: str
  dest:
    description:
      - Destination folder path.
    required: true
    type: str
  deduplicate:
    description:
      - How to handle multiple search results.
    required: false
    type: str
  search_alternatives:
    description:
      - Enable search for alternative packages, when filename is not available.
    required: false
    type: bool
  dry_run:
    description:
      - Check availability of SAP Software without downloading.
    required: false
    type: bool
author:
    - SAP LinuxLab

'''

EXAMPLES = r'''
- name: Download using search query
  community.sap_launchpad.sap_launchpad_software_center_download:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    search_query:
      - 'SAPCAR_1324-80000936.EXE'
    dest: "/tmp/"
- name: Download using direct link and filename
  community.sap_launchpad.software_center_download:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    download_link: 'https://softwaredownloads.sap.com/file/0010000000048502015'
    download_filename: 'IW_FNDGC100.SAR'
    dest: "/tmp/"
'''

RETURN = r'''
msg:
  description: the status of the process
  returned: always
  type: str
filename:
  description: the name of the original or alternative file found to download.
  returned: always
  type: str
alternative:
  description: true if alternative file was found
  returned: always
  type: bool
'''


#########################

import requests
import glob
from ansible.module_utils.basic import AnsibleModule

# Import runner
from ..module_utils.sap_launchpad_software_center_download_runner import *
from ..module_utils.sap_id_sso import sap_sso_login

def _check_similar_files(dest, filename):
    """
    Checks for similar files in the download path based on the given filename.

    Args:
        dest (str): The path where files are downloaded.
        filename (str): The filename to check for similar files.

    Returns:
        bool: True if similar files exist, False otherwise.
        filename_similar_names: A list of similar filenames if they exist, empty list otherwise.
    """
    # pattern = dest + '/**/' + os.path.splitext(filename)[0]
    filename_base = os.path.splitext(filename)[0]
    filename_pattern = os.path.join(dest, "**", filename_base)
    filename_similar = glob.glob(filename_pattern, recursive=True)

    if filename_similar:
        filename_similar_names = [os.path.basename(f) for f in filename_similar]
        return True, filename_similar_names
    else:
        return False, []


def run_module():

    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        suser_id=dict(type='str', required=True),
        suser_password=dict(type='str', required=True, no_log=True),
        softwarecenter_search_query=dict(type='str', required=False, default=''),
        search_query=dict(type='str', required=False, default=''),
        download_link=dict(type='str', required=False, default=''),
        download_filename=dict(type='str', required=False, default=''),
        dest=dict(type='str', required=True),
        dry_run=dict(type='bool', required=False, default=False),
        deduplicate=dict(type='str', required=False, default=''),
        search_alternatives=dict(type='bool', required=False, default=False)
    )

    # Instantiate module
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Define variables based on module inputs
    username = module.params.get('suser_id')
    password = module.params.get('suser_password')

    if module.params['search_query'] != '':
        query = module.params['search_query']
    elif module.params['softwarecenter_search_query'] != '':
        query = module.params['softwarecenter_search_query']
        module.warn("The 'softwarecenter_search_query' is deprecated and will be removed in a future version. Use 'search_query' instead.")
    else:
        query = None

    dest = module.params['dest']
    download_link= module.params.get('download_link')
    download_filename= module.params.get('download_filename')
    dry_run = module.params.get('dry_run')
    deduplicate = module.params.get('deduplicate')
    search_alternatives = module.params.get('search_alternatives')

    # Define result dictionary objects to be passed back to Ansible
    result = dict(
        changed=False,
        msg='',
        filename=download_filename,
        alternative=False,
        skipped=False,
        failed=False
    )

    # Check mode
    if module.check_mode:
        module.exit_json(**result)


    # Main
    try:

        # Ensure that required parameters are provided
        if not (query or (download_link and download_filename)):
              module.fail_json(
                  msg="Either 'search_query' or both 'download_link' and 'download_filename' must be provided."
              )

        # Search for existing files using exact filename
        filename = query if query else download_filename
        filename_exact = os.path.join(dest, filename)
        result['filename'] = filename

        if os.path.exists(filename_exact):
            result['skipped'] = True
            result['msg'] = f"File already exists: {filename}"
            module.exit_json(**result)
        else:
            # Exact file not found, search for similar files with pattern
            filename_similar_exists, filename_similar_names = _check_similar_files(dest, filename)
            if filename_similar_exists and not (query and search_alternatives):
                result['skipped'] = True
                result['msg'] = f"Similar file(s) already exist: {', '.join(filename_similar_names)}"
                module.exit_json(**result)
            
        # Initiate login with given credentials
        sap_sso_login(username, password)

        # Execute search_software_filename first to get download link and filename
        alternative_found = False  # True if search_alternatives was successful
        if query:
            download_link, download_filename, alternative_found = search_software_filename(query,deduplicate,search_alternatives)

            # Search for existing files again with alternative filename
            if  search_alternatives and alternative_found:
                result['filename'] = download_filename
                result['alternative'] = True

                filename_alternative_exact = os.path.join(dest, download_filename)
                if os.path.exists(filename_alternative_exact):
                    result['skipped'] = True
                    result['msg'] = f"Alternative file already exists: {download_filename} - original file {query} is not available to download"
                    module.exit_json(**result)
                else:
                    # Exact file not found, search for similar files with pattern
                    filename_similar_exists, filename_similar_names = _check_similar_files(dest, download_filename)
                    if filename_similar_exists:
                        result['skipped'] = True
                        result['msg'] = f"Similar alternative file(s) already exist: {', '.join(filename_similar_names)}"                     
                        module.exit_json(**result)
            
            # Triggers for CD Media, where number was changed to name using _get_valid_filename
            elif filename != download_filename and not alternative_found:
                result['filename'] = download_filename

                if os.path.exists(os.path.join(dest, download_filename)):
                    result['skipped'] = True
                    result['msg'] = f"File already exists with correct name: {download_filename}"
                    module.exit_json(**result)
                else:
                    # Exact file not found, search for similar files with pattern
                    filename_similar_exists, filename_similar_names = _check_similar_files(dest, download_filename)                 
                    if filename_similar_exists:
                        result['skipped'] = True
                        result['msg'] = f"Similar file(s) already exist for correct name {download_filename}: {', '.join(filename_similar_names)}"                     
                        module.exit_json(**result)


        # Ensure that download_link is provided when query was not provided
        if not download_link:
            module.fail_json(msg="Missing parameters 'query' or 'download_link'.")

        # Exit module before download when dry_run is true
        if dry_run:
            available = is_download_link_available(download_link)
            if available and query and not alternative_found:
                result['msg'] = f"SAP Software is available to download: {download_filename}"
                module.exit_json(**result)
            elif available and query and alternative_found:
                result['msg'] = f"Alternative SAP Software is available to download: {download_filename} - original file {query} is not available to download"
                module.exit_json(**result) 
            else:
                module.fail_json(msg="Download link {} is not available".format(download_link))

        download_software(download_link, download_filename, dest)

        # Update final results json
        result['changed'] = True
        if query and alternative_found:
            result['msg'] = f"Successfully downloaded alternative SAP software: {download_filename} - original file {query} is not available to download"
        else:
            result['msg'] = f"Successfully downloaded SAP software: {download_filename}"

    except requests.exceptions.HTTPError as e:
        # module.fail_json(msg='SAP SSO authentication failed' + str(e), **result)
        result['msg'] = "SAP SSO authentication failed - " + str(e)
        result['failed'] = True
    except Exception as e:
        # module.fail_json(msg='An exception has occurred' + str(e), **result)
        result['msg'] = "An exception has occurred - " + str(e)
        result['failed'] = True

    # Return to Ansible
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
