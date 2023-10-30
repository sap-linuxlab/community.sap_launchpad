from ansible.module_utils.basic import AnsibleModule

from ..module_utils.sap_launchpad_systems_runner import *
from ..module_utils.sap_id_sso import sap_sso_login


def run_module():
    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        suser_id=dict(type='str', required=True),
        suser_password=dict(type='str', required=True, no_log=True),
        installation_nr=dict(type='str', required=True),
        system=dict(
            type='dict',
            options=dict(
                nr=dict(type='str', required=False),
                product=dict(type='str', required=True),
                version=dict(type='str', required=True),
                data=dict(type='dict')
            )
        ),
        licenses=dict(type='list', required=True, elements='dict', options=dict(
            type=dict(type='str', required=True),
            data=dict(type='dict'),
        )),
        delete_other_licenses=dict(type='bool', required=False, default=False),
    )

    # Define result dictionary objects to be passed back to Ansible
    result = dict(
        license_file='',
        changed=False,
        msg=''
    )

    # Instantiate module
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    username = module.params.get('suser_id')
    password = module.params.get('suser_password')
    installation_nr = module.params.get('installation_nr')
    system = module.params.get('system')
    system_nr = system.get('nr')
    product = system.get('product')
    version = system.get('version')
    data = system.get('data')
    licenses = module.params.get('licenses')

    if len(licenses) == 0:
        module.fail_json("licenses cannot be empty")

    delete_other_licenses = module.params.get('delete_other_licenses')

    sap_sso_login(username, password)

    try:
        validate_installation(installation_nr, username)
    except InstallationNotFoundError as err:
        module.fail_json("Installation could not be found", installation_nr=err.installation_nr,
                         available_installations=[inst['Text'] for inst in err.available_installations])

    existing_system = None
    if system_nr is not None:
        try:
            existing_system = get_system(system_nr, installation_nr, username)
        except SystemNrInvalidError as err:
            module.fail_json("System could not be found", system_nr=err.system_nr, details=err.details)

    product_id = None
    try:
        product_id = get_product(product, installation_nr, username)
    except ProductNotFoundError as err:
        module.fail_json("Product could not be found", product=err.product,
                         available_products=[product['Description'] for product in err.available_products])

    version_id = None
    try:
        version_id = get_version(version, product_id, installation_nr, username)
    except VersionNotFoundError as err:
        module.fail_json("Version could not be found", version=err.version,
                         available_versions=[version['Description'] for version in err.available_versions])

    system_data = None
    try:
        system_data, warning = validate_system_data(data, version_id, system_nr, installation_nr, username)
        if warning is not None:
            module.warn(warning)
    except DataInvalidError as err:
        module.fail_json(f"Invalid {err.scope} data",
                         unknown_fields=err.unknown_fields,
                         missing_required_fields=err.missing_required_fields,
                         fields_with_invalid_option=err.fields_with_invalid_option)

    license_data = None
    try:
        license_data = validate_licenses(licenses, version_id, installation_nr, username)
    except LicenseTypeInvalidError as err:
        module.fail_json(f"Invalid license type", license_type=err.license_type, available_license_types=err.available_license_types)
    except DataInvalidError as err:
        module.fail_json(f"Invalid {err.scope} data",
                         unknown_fields=err.unknown_fields,
                         missing_required_fields=err.missing_required_fields,
                         fields_with_invalid_option=err.fields_with_invalid_option)

    generated_licenses = []
    existing_licenses = []
    new_or_changed_license_data = license_data

    if existing_system is not None:
        existing_licenses = get_existing_licenses(system_nr, username)
        new_or_changed_license_data = keep_only_new_or_changed_licenses(existing_licenses, license_data)

    if len(new_or_changed_license_data) > 0:
        generated_licenses = generate_licenses(new_or_changed_license_data, existing_licenses, version_id,
                                               installation_nr, username)

    system_nr = submit_system(existing_system is None, system_data, generated_licenses, username)
    key_nrs = get_license_key_numbers(license_data, system_nr, username)
    result['license_file'] = download_licenses(key_nrs)

    if delete_other_licenses:
        existing_licenses = get_existing_licenses(system_nr, username)
        licenses_to_delete = find_licenses_to_delete(key_nrs, existing_licenses)
        if len(licenses_to_delete) > 0:
            updated_licenses = delete_licenses(licenses_to_delete, existing_licenses, version_id, installation_nr, username)
            submit_system(False, system_data, updated_licenses, username)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
