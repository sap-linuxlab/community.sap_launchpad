#!/usr/bin/python

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: license_keys

short_description: Creates systems and license keys on me.sap.com/licensekey

description:
 - This ansible module creates and updates systems and their license keys using the Launchpad API.
 - It is closely modeled after the interactions in the portal U(https://me.sap.com/licensekey)
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
  download_path:
    description: If specified, the generated license key file will be downloaded to this directory.
    required: false
    type: path

author:
    - Matthias Winzeler (@MatthiasWinzeler)
    - Marcel Mamula (@marcelmamula)

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
    var: result.license_file
'''


RETURN = r'''
license_file:
  description: |
    The license file content containing the digital signatures of the specified licenses.
    This is returned when C(state) is 'present' and licenses are specified.
  returned: on success
  type: str
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
  returned: on success
  type: str
  sample: "0000123456"
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.systems import main as systems_runner


def run_module():
    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        suser_id=dict(type='str', required=True),
        suser_password=dict(type='str', required=True, no_log=True),
        installation_nr=dict(type='str', required=True),
        system=dict(
            type='dict',
            required=True,
            options=dict(
                nr=dict(type='str', required=False),
                product=dict(type='str', required=True),
                version=dict(type='str', required=True),
                data=dict(type='dict', required=True)
            )
        ),
        licenses=dict(type='list', required=True, elements='dict', options=dict(
            type=dict(type='str', required=True),
            data=dict(type='dict', required=True),
        )),
        delete_other_licenses=dict(type='bool', required=False, default=False),
        download_path=dict(type='path', required=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(changed=False, msg="Check mode not supported for license key management.")

    # Translate original parameters to the new, flat structure for the runner.
    params = module.params.copy()

    # The runner expects a flat structure, so we unpack the 'system' dictionary.
    system_info = params.pop('system')
    params['system_nr'] = system_info.get('nr')
    params['product_name'] = system_info.get('product')
    params['product_version'] = system_info.get('version')
    params['system_data'] = system_info.get('data')

    # The runner uses a 'state' parameter instead of 'delete_other_licenses'.
    if params.pop('delete_other_licenses', False):
        params['state'] = 'absent'
    else:
        params['state'] = 'present'

    # Call the runner with the translated parameters.
    result = systems_runner.run_license_keys(params)

    if result.get('failed'):
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
