#!/usr/bin/python

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
---
module: software_center_download

short_description: Downloads software from the SAP Software Center.

description:
  - This module automates downloading files from the SAP Software Center.
  - It can find a file using a search query or download it directly using a specific download link and filename.
  - If a file is not found via search, it can look for alternative versions.
  - It supports checksum validation to ensure file integrity and avoid re-downloading valid files.
  - The module can also perform a dry run to check for file availability without downloading.

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
    default: ''
    type: str
  search_query:
    description:
      - Filename of the SAP software to download.
    required: false
    default: ''
    type: str
  download_link:
    description:
      - Direct download link to the SAP software.
    required: false
    default: ''
    type: str
  download_filename:
    description:
      - Download filename of the SAP software.
    required: false
    default: ''
    type: str
  dest:
    description:
      - Destination folder path.
    required: true
    type: str
  deduplicate:
    description:
      - "Specifies how to handle multiple search results for the same filename.
      - Choices are `first` (oldest) or `last` (newest)."
    choices: [ 'first', 'last', '' ]
    required: false
    default: ''
    type: str
  search_alternatives:
    description:
      - Enable search for alternative packages, when filename is not available.
    required: false
    default: false
    type: bool
  dry_run:
    description:
      - Check availability of SAP Software without downloading.
    required: false
    default: false
    type: bool
  validate_checksum:
    description:
      - If a file with the same name already exists at the destination, validate its checksum against the remote file.
      - If the checksum is invalid, the local file will be removed and re-downloaded.
    required: false
    default: false
    type: bool
author:
    - Matthias Winzeler (@MatthiasWinzeler)
    - Sean Freeman (@sean-freeman)
    - Marcel Mamula (@marcelmamula)

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
- name: Download a file, searching for alternatives and validating checksum
  community.sap_launchpad.software_center_download:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    search_query: 'IMDB_SERVER20_023_0-80002031.SAR'
    dest: "/sap_media"
    search_alternatives: true
    deduplicate: "last"
    validate_checksum: true
'''

RETURN = r'''
msg:
  description: A message indicating the status of the download operation.
  returned: always
  type: str
  sample: "Successfully downloaded SAP software: SAPCAR_1324-80000936.EXE"
filename:
  description: The name of the file that was downloaded or checked. This may be an alternative if one was found.
  returned: on success or failure after finding a file
  type: str
  sample: "SAPCAR_1324-80000936.EXE"
alternative:
  description: A boolean indicating if an alternative file was downloaded instead of the one from the original search query.
  returned: on success
  type: bool
changed:
  description: A boolean indicating if a file was downloaded or changed on the remote host.
  returned: always
  type: bool
skipped:
  description: A boolean indicating if the download was skipped (e.g., file already exists and checksum is valid).
  returned: always
  type: bool
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
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
        deduplicate=dict(type='str', required=False, default='', choices=['first', 'last', '']),
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
        if result.get('missing_dependency'):
            module.fail_json(msg=missing_required_lib(result['missing_dependency']))
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
