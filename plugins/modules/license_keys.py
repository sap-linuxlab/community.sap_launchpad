from ansible.module_utils.basic import AnsibleModule

from ..module_utils.sap_launchpad_systems_runner import *
from ..module_utils.sap_id_sso import sap_sso_login


DOCUMENTATION = r'''
---
module: license_keys

short_description: Creates systems and license keys on me.sap.com/licensekey

description:
 - This ansible module creates and updates systems and their license keys using the Launchpad API.
 - It is closely modeled after the interactions in the portal U(https://me.sap.com/licensekey):
 - First, a SAP system is defined by its SID, product, version and other data.
 - Then, for this system, license keys are defined by license type, HW key and potential other attributes.
 - The system and license data is then validated and submitted to the Launchpad API and the license key files returned to the caller.
 - This module attempts to be as idempotent as possible, so it can be used in a CI/CD pipeline.

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
  installation_nr:
    description: 
      - Number of the Installation for which the system should be created/updated
    required: true
    type: str
  system:
    description:
      - The system to create/update
    required: true
    type: dict
    suboptions:
      nr:
        description:
          - The number of the system to update. If this attribute is not provided, a new system is created.
        required: false
        type: str
      product:
        description:
          - The product description as found in the SAP portal, e.g. SAP S/4HANA
        required: true
        type: str
      version:
        description:
          - The description of the product version, as found in the SAP portal, e.g. SAP S/4HANA 2022
        required: true
        type: str
      data:
        description: 
          - The data attributes of the system. The possible attributes are defined by product and version.
          - Running the module without any data attributes will return in the error message which attributes are supported/required.
        required: true
        type: dict

  licenses:
    description:
      - List of licenses to create for the system.
      - If the license does not exist, it is created.
      - If it exists, it is updated.
    required: true
    type: list
    elements: dict
    suboptions:
      type:
        description:
          - The license type description as found in the SAP portal, e.g. Maintenance Entitlement
        required: true
        type: str
      data:
        description: 
          - The data attributes of the licenses. The possible attributes are defined by product and version.
          - Running the module without any data attributes will return in the error message which attributes are supported/required
          - In practice, most license types require at least a hardware key (hwkey) and expiry date (expdate)
        required: true
        type: dict
      
  delete_other_licenses:
    description:
      - Whether licenses other than the ones specified in the licenses attributes should be deleted.
      - This is handy to clean up older licenses automatically.
    type: bool
    required: false
    default: false
    
  
author:
    - Lab for SAP Solutions

'''


EXAMPLES = r'''
- name: create license keys
  community.sap_launchpad.license_keys:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    installation_nr: 12345678
    system:
      nr: 23456789
      product: SAP S/4HANA
      version: SAP S/4HANA 2022
      data:
        sysid: H01
        sysname: Test-System
        systype: Development system
        sysdb: SAP HANA database
        sysos: Linux
        sys_depl: Public - Microsoft Azure
    licenses:
      - type: Standard - Web Application Server ABAP or ABAP+JAVA
        data:
          hwkey: H1234567890
          expdate: 99991231
      - type: Maintenance Entitlement
        data:
          hwkey: H1234567890
          expdate: 99991231
    delete_other_licenses: true
  register: result

- name: Display the license file containing the licenses
  debug:
    msg:
      - "{{ result.license_file }}"
'''


RETURN = r'''
license_file:
  description: |
    The license file containing the digital signatures of the specified licenses.
    All licenses that were provided in the licenses attribute are returned, no matter if they were modified or not. 
  returned: always
  type: string
  sample: |
    ----- Begin SAP License -----
    SAPSYSTEM=H01
    HARDWARE-KEY=H1234567890
    INSTNO=0012345678
    BEGIN=20231026
    EXPIRATION=99991231
    LKEY=MIIBO...
    SWPRODUCTNAME=NetWeaver_MYS
    SWPRODUCTLIMIT=2147483647
    SYSTEM-NR=00000000023456789
    ----- Begin SAP License -----
    SAPSYSTEM=H01
    HARDWARE-KEY=H1234567890
    INSTNO=0012345678
    BEGIN=20231026
    EXPIRATION=20240127
    LKEY=MIIBO...
    SWPRODUCTNAME=Maintenance_MYS
    SWPRODUCTLIMIT=2147483647
    SYSTEM-NR=00000000023456789
    
system_nr:
  description: The number of the system which was created/updated. 
  returned: always
  type: string
  sample: 23456789
'''


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
        system_nr='',
        # as we don't have a diff mechanism but always submit the system, we don't have a way to detect changes.
        # it might always have changed.
        changed=True,
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

    # This module closely mimics the flow of the portal (me.sap.com/licensekey) when creating license keys:
    # - validate the user-provided installation against the available installations from API call /Installations
    # - validate the user-provided product against the available products from API call /SysProducts
    # - validate the user-provided product against the available product versions from API call /SysVersions
    # - validate the user-provided system data (SID, OS etc.) via API calls /SystData and /SystemDataCheck
    # - validate the user-provided license type and data via API call /LicenseType
    # - if the validation succeeds, the data is enriched with the existing system and license data and submitted
    #   by first generating the licenses via API Call /BSHWKEY and then submitting the system via API call /Submit.
    # - as a last step, the license keys are now downloaded via API call /FileContent.

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
    result['system_nr'] = system_nr

    if delete_other_licenses:
        existing_licenses = get_existing_licenses(system_nr, username)
        licenses_to_delete = select_licenses_to_delete(key_nrs, existing_licenses)
        if len(licenses_to_delete) > 0:
            updated_licenses = delete_licenses(licenses_to_delete, existing_licenses, version_id, installation_nr, username)
            submit_system(False, system_data, updated_licenses, username)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
