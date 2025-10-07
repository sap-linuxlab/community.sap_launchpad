#!/usr/bin/python

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
---
module: maintenance_planner_stack_xml_download

short_description: Downloads the stack.xml file from an SAP Maintenance Planner transaction.

description:
  - This module connects to the SAP Maintenance Planner to download the stack.xml file associated with a specific transaction.
  - The stack.xml file contains the plan for a system update or installation and is used by tools like Software Update Manager (SUM).
  - The file is saved to the specified destination directory.

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
  dest:
    description:
      - The path to an existing destination directory where the stack.xml file will be saved.
    required: true
    type: str
author:
    - Matthias Winzeler (@MatthiasWinzeler)
    - Sean Freeman (@sean-freeman)
    - Marcel Mamula (@marcelmamula)

'''

EXAMPLES = r'''
- name: Download a Stack XML file from a Maintenance Planner transaction
  community.sap_launchpad.maintenance_planner_stack_xml_download:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    transaction_name: 'MP_NEW_INST_20211015_044854'
    dest: "/tmp/"
  register: sap_mp_stack_xml_result
- name: Display the result message
  ansible.builtin.debug:
    msg: "{{ sap_mp_stack_xml_result.msg }}"
'''

RETURN = r'''
msg:
  description: A message indicating the status of the download operation.
  returned: always
  type: str
  sample: "SAP Maintenance Planner Stack XML successfully downloaded to /tmp/MP_STACK_20211015_044854.xml"
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.maintenance_planner import main as maintenance_planner_runner


def run_module():

    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        suser_id=dict(type='str', required=True),
        suser_password=dict(type='str', required=True, no_log=True),
        transaction_name=dict(type='str', required=True),
        dest=dict(type='str', required=True)
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

    result = maintenance_planner_runner.run_stack_xml_download(module.params)

    # The runner function indicates failure via a key in the result.
    if result.get('failed'):
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
