#!/usr/bin/python

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
      - Destination folder.
    required: true
    type: str
  deduplicate:
    description:
      - How to handle multiple search results.
    required: false
    type: str
author:
    - Lab for SAP Solutions

'''

EXAMPLES = r'''
- name: Download using search query
  community.sap_launchpad.sap_launchpad_software_center_download:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    softwarecenter_search_query:
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
'''


#########################

import requests
import glob
from ansible.module_utils.basic import AnsibleModule

# Import runner
from ..module_utils.sap_launchpad_software_center_download_runner import *


def run_module():

    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        suser_id=dict(type='str', required=True),
        suser_password=dict(type='str', required=True, no_log=True),
        softwarecenter_search_query=dict(type='str', required=False, default=''),
        download_link=dict(type='str', required=False, default=''),
        download_filename=dict(type='str', required=False, default=''),
        dest=dict(type='str', required=True),
        dry_run=dict(type='bool', required=False, default=False),
        deduplicate=dict(type='str', required=False, default='')
    )

    # Define result dictionary objects to be passed back to Ansible
    result = dict(
        changed=False,
        msg=''
    )

    # Instantiate module
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Check mode
    if module.check_mode:
        module.exit_json(**result)

    # Define variables based on module inputs
    username = module.params.get('suser_id')
    password = module.params.get('suser_password')
    query = module.params.get('softwarecenter_search_query')
    download_link= module.params.get('download_link')
    download_filename= module.params.get('download_filename')
    dest = module.params.get('dest')
    dry_run = module.params.get('dry_run')
    deduplicate = module.params.get('deduplicate')

    # Main run

    try:

        # Search directory and subdirectories for filename without file extension
        filename = query if query else download_filename
        pattern = dest + '/**/' + os.path.splitext(filename)[0] + '*'
        for file in glob.glob(pattern, recursive=True):
            if os.path.exists(file):
                module.exit_json(skipped=True, msg="file {} already exists".format(file))

        # Initiate login with given credentials
        sap_sso_login(username, password)

        # EXEC: query
        # execute search_software_filename first to get download link and filename
        if query:
            download_link, download_filename = search_software_filename(query,deduplicate)

        # execute download_software
        if dry_run:
            available = is_download_link_available(download_link)
            if available:
                module.exit_json(changed=False, msg="download link {} is available".format(download_link))
            else:
                module.fail_json(msg="download link {} is not available".format(download_link))

        download_software(download_link, download_filename, dest)

        # Process return dictionary for Ansible
        result['changed'] = True
        result['msg'] = "SAP software download successful"

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
