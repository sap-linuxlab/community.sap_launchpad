#!/usr/bin/python

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
---
module: maintenance_planner_files

short_description: Retrieves a list of files from an SAP Maintenance Planner transaction.

description:
  - This module connects to the SAP Maintenance Planner to retrieve a list of all downloadable files associated with a specific transaction.
  - It returns a list containing direct download links and filenames for each file.
  - This is useful for automating the download of a complete stack file set defined in a Maintenance Planner transaction.

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
  transaction_name:
    description:
      - Transaction Name or Transaction Display ID from Maintenance Planner.
    required: true
    type: str
  validate_url:
    description:
      - Validates if the download URLs are accessible before returning them.
    type: bool
    default: false
author:
    - Matthias Winzeler (@MatthiasWinzeler)
    - Marcel Mamula (@marcelmamula)

'''

EXAMPLES = r'''
- name: Retrieve a list of downloadable files from a Maintenance Planner transaction
  community.sap_launchpad.maintenance_planner_files:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    transaction_name: 'MP_NEW_INST_20211015_044854'
  register: sap_mp_register
- name: Display the list of download links and filenames
  ansible.builtin.debug:
    msg: "Files found for transaction: {{ sap_mp_register.download_basket }}"
'''

RETURN = r'''
msg:
  description: A message indicating the status of the operation.
  returned: always
  type: str
  sample: "Successfully retrieved file list from SAP Maintenance Planner."
download_basket:
  description: A list of files retrieved from the Maintenance Planner transaction.
  returned: always
  type: list
  elements: dict
  contains:
    DirectLink:
      description: The direct URL to download the file.
      type: str
      sample: "https://softwaredownloads.sap.com/file/0020000001234562023"
    Filename:
      description: The name of the file.
      type: str
      sample: "SAPCAR_1324-80000936.EXE"
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ..module_utils.maintenance_planner import main as maintenance_planner_runner


def run_module():

    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        suser_id=dict(type='str', required=True),
        suser_password=dict(type='str', required=True, no_log=True),
        transaction_name=dict(type='str', required=True),
        validate_url=dict(type='bool', required=False, default=False)
    )

    # Define result dictionary objects to be passed back to Ansible
    result = dict(
        changed=False,
    )

    # Instantiate module
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Check mode
    if module.check_mode:
        module.exit_json(changed=False, download_basket={})

    result = maintenance_planner_runner.run_files(module.params)

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
