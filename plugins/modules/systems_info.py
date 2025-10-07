#!/usr/bin/python

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
---
module: systems_info

short_description: Retrieves information about SAP systems.

description:
- This module queries the SAP Launchpad to retrieve a list of registered systems based on a filter string.
- It allows for fetching details about systems associated with the authenticated S-User.

version_added: 1.1.0

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
  filter:
    description:
      - An ODATA filter expression to query the systems.
    required: true
    type: str
author:
    - Matthias Winzeler (@MatthiasWinzeler)
    - Marcel Mamula (@marcelmamula)

'''


EXAMPLES = r'''
- name: Get all systems for a specific installation number
  community.sap_launchpad.systems_info:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    filter: "Insnr eq '1234567890'"
  register: result

- name: Display system details
  debug:
    var: result.systems
'''


RETURN = r'''
systems:
  description:
    - A list of dictionaries, where each dictionary represents an SAP system.
    - The product version ID may be returned under the 'Version' or 'Prodver' key, depending on the system's age and type.
  returned: always
  type: list
  elements: dict
  sample:
    - Sysnr: "0000123456"
      Sysid: "S4H"
      Systxt: "S/4HANA Development System"
      Insnr: "1234567890"
      Version: "73554900100800000266"
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ..module_utils.systems import main as systems_runner


def run_module():
    module_args = dict(
        suser_id=dict(type='str', required=True),
        suser_password=dict(type='str', required=True, no_log=True),
        filter=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = systems_runner.run_systems_info(module.params)

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
