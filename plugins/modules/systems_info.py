from ansible.module_utils.basic import AnsibleModule

from ..module_utils.sap_launchpad_systems_runner import *
from ..module_utils.sap_id_sso import sap_sso_login

from requests.exceptions import HTTPError

DOCUMENTATION = r'''
---
module: systems_info

short_description: Queries registered systems in me.sap.com

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
    - Lab for SAP Solutions

'''


EXAMPLES = r'''
- name: get system by SID and product
  community.sap_launchpad.systems_info:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    filter: "Insnr eq '12345678' and sysid eq 'H01' and ProductDescr eq 'SAP S/4HANA'"
  register: result

- name: Display the first returned system
  debug:
    msg:
      - "{{ result.systems[0] }}"
'''


RETURN = r'''
systems:
  description: the systems returned for the filter
  returned: always
  type: list
'''


def run_module():
    module_args = dict(
        suser_id=dict(type='str', required=True),
        suser_password=dict(type='str', required=True, no_log=True),
        filter=dict(type='str', required=True),
    )

    result = dict(
        systems='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    username = module.params.get('suser_id')
    password = module.params.get('suser_password')
    filter = module.params.get('filter')

    sap_sso_login(username, password)

    try:
        result["systems"] = get_systems(filter)
    except HTTPError as err:
        module.fail_json("Error while querying systems", status_code=err.response.status_code,
                         response=err.response.content)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
