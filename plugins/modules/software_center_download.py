#!/usr/bin/python

from __future__ import absolute_import, division, print_function

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
  validate_checksum:
    description:
      - If a file with the same name already exists at the destination, validate its checksum against the remote file. If the checksum is invalid, the local file will be removed and re-downloaded.
    required: false
    type: bool
author:
    - SAP LinuxLab

'''

EXAMPLES = r'''
- name: Download using search query
  community.sap_launchpad.software_center_download:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    search_query: 'SAPCAR_1324-80000936.EXE'
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


from ansible.module_utils.basic import AnsibleModule

# Import the main runner function from the module_utils
from ..module_utils.software_center import main as software_center_runner


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
        search_alternatives=dict(type='bool', required=False, default=False),
        validate_checksum=dict(type='bool', required=False, default=False)
    )

    # Instantiate module
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(changed=False)

    result = software_center_runner.run_software_download(module.params)

    # The runner function can also return warnings for the module to display.
    for warning in result.pop('warnings', []):
        module.warn(warning)

    # The runner function indicates failure via a key in the result.
    if result.get('failed'):
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
