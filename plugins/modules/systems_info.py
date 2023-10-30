from ansible.module_utils.basic import AnsibleModule

from ..module_utils.sap_launchpad_systems_runner import *
from ..module_utils.sap_id_sso import sap_sso_login

from requests.exceptions import HTTPError

# TODO document

def run_module():

    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        suser_id=dict(type='str', required=True),
        suser_password=dict(type='str', required=True, no_log=True),
        filter=dict(type='str', required=True),
    )

    # Define result dictionary objects to be passed back to Ansible
    result = dict(
        systems='',
        changed=False,
    )

    # Instantiate module
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
