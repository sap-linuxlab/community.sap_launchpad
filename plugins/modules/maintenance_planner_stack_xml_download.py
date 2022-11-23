#!/usr/bin/python

# SAP Maintenance Planner Stack XML download

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: maintenance_planner_stack_xml_download

short_description: SAP Maintenance Planner Stack XML download

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
      - Transaction name of your Maintenance Planner session.
    required: true
    type: str
  dest:
    description:
      - Destination folder.
    required: true
    type: str
author:
    - Lab for SAP Solutions

'''

EXAMPLES = r'''
- name: Execute Ansible Module 'maintenance_planner_stack_xml_download' to get files from MP
  community.sap_launchpad.sap_launchpad_software_center_download:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    transaction_name: 'MP_NEW_INST_20211015_044854'
    dest: "/tmp/"
  register: sap_mp_register
- name: Display the list of download links and filenames
  debug:
    msg:
      - "{{ sap_mp_register.download_basket }}"
'''

RETURN = r'''
msg:
  description: the status of the process
  returned: always
  type: str
'''


#########################

import requests
from ansible.module_utils.basic import AnsibleModule

# Import runner
from ..module_utils.sap_launchpad_maintenance_planner_runner import *


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

    # Define variables based on module inputs
    username = module.params.get('suser_id')
    password = module.params.get('suser_password')
    transaction_name = module.params.get('transaction_name')
    dest = module.params.get('dest')

    # Main run

    try:

        # EXEC: Retrieve login session, using Py Function from imported module in directory module_utils
        session = sap_sso_login(username, password)

        # EXEC: Authenticate against userapps.support.sap.com
        auth_userapps()

        # EXEC: Get MP stack transaction id from transaction name
        transaction_id = get_transaction_id_by_name(transaction_name)

        # EXEC: Download the MP Stack XML file
        get_transaction_stack_xml(transaction_id, dest)

        # Process return dictionary for Ansible
        result['changed'] = True
        result['msg'] = "SAP Maintenance Planner Stack XML download successful"

    except KeyError as e:
        # module.fail_json(msg='Maintenance planner session not found - ' + str(e), **result)
        result['msg'] = "Maintenance planner session not found - " + str(e)
        result['failed'] = True
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
