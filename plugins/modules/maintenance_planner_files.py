#!/usr/bin/python

# SAP Maintenance Planner files retrieval

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: maintenance_planner_files

short_description: SAP Maintenance Planner files retrieval

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
author:
    - Lab for SAP Solutions

'''

EXAMPLES = r'''
- name: Execute Ansible Module 'maintenance_planner_files' to get files from MP
  community.sap_launchpad.sap_launchpad_software_center_download:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    transaction_name: 'MP_NEW_INST_20211015_044854'
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
download_basket:
  description: a json list of software download links and filenames from the MP transaction
  returned: always
  type: json list
'''


#########################

import requests
from ansible.module_utils.basic import AnsibleModule

# Import runner
from ..module_utils.sap_launchpad_maintenance_planner_runner import *
from ..module_utils.sap_launchpad_software_center_download_runner import \
    is_download_link_available


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
        download_basket={},
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
    validate_url = module.params.get('validate_url')

    # Main run

    try:
        # EXEC: Retrieve login session, using Py Function from imported module in directory module_utils
        session = sap_sso_login(username, password)

        # EXEC: Authenticate against userapps.support.sap.com
        auth_userapps()

        # EXEC: Get MP stack transaction id from transaction name
        transaction_id = get_transaction_id_by_name(transaction_name)

        # EXEC: Get a json list of download_links and download_filenames
        download_basket_details = get_transaction_filename_url(transaction_id)

        if validate_url:
            for pair in download_basket_details:
                url = pair[0]
                if not is_download_link_available(url):
                    module.fail_json(failed=True, msg='Download link is not available: {}'.format(url))

        # Process return dictionary for Ansible
        result['download_basket'] = [{'DirectLink': i[0], 'Filename': i[1]} for i in download_basket_details]
        result['changed'] = True
        result['msg'] = "Successful SAP maintenance planner stack generation"

    except ValueError as e:
        # module.fail_json(msg='Stack files not found - ' + str(e), **result)
        result['msg'] = "Stack files not found - " + str(e)
        result['failed'] = True
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
