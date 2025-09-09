# license_keys Ansible Module

## Description
The Ansible Module `license_keys` creates and updates systems and their license keys using the SAP Launchpad API.
- It is closely modeled after the interactions in the portal at `https://me.sap.com/licensekey`.
- First, a SAP system is defined by its SID, product, version, and other data.
- Then, for this system, license keys are defined by license type, hardware key, and other potential attributes.
- The system and license data is then validated and submitted to the API, and the license key file content is returned.
- This module attempts to be as idempotent as possible. If a system with the same SID is found under the installation, it will be updated instead of creating a new one.

## Dependencies
This module requires the following Python modules to be installed on the target node:

- wheel
- urllib3
- requests
- beautifulsoup4
- lxml

Installation instructions are available at [Installation of prerequisites](#installation-of-prerequisites)

## Execution

### Execution Flow
The module follows a sophisticated logic flow to determine whether to create, update, or remove systems and licenses.

1.  **Authentication**:
    *   The module authenticates with the provided S-User credentials to establish a valid session.
    *   It validates that the user has access to the specified `installation_nr`.

2.  **System Identification (Idempotency Check)**:
    *   **If `system.nr` is provided:** The module targets the specified system for updates.
    *   **If `system.nr` is NOT provided:**
        *   The module searches for an existing system using the `sysid` from `system.data` and the `installation_nr`.
        *   **If one system is found:** It targets that system for updates and issues a warning.
        *   **If multiple systems are found:** The module fails with an error, asking the user to provide a specific `system.nr` to select one.
        *   **If no system is found:** The module proceeds to create a new system.

3.  **Action: Create New System**:
    *   Validates the provided `product`, `version`, and `system.data`.
    *   Validates the provided `licenses`.
    *   Submits the request to the API to create the new system with its initial licenses.
    *   The new `system_nr` is returned.

4.  **Action: Update Existing System**:
    *   **Validation:** It first checks if the `product` and `version` provided in the playbook match the details of the existing system on the portal. If they do not match, the module fails, as changing these properties is not supported.
    *   It retrieves the list of licenses that already exist on the system.
    *   **If `delete_other_licenses: false` (default):**
        *   It compares the `licenses` from the playbook with the existing licenses.
        *   Only new or changed licenses are sent to the API for creation/update.
        *   If all specified licenses already exist in the desired state, no changes are made.
    *   **If `delete_other_licenses: true`:**
        *   It ensures that only the licenses specified in the playbook exist on the system.
        *   Any license on the system that is *not* in the playbook's `licenses` list will be deleted.
        *   If the `licenses` list is empty, all licenses will be removed from the system.

5.  **License File Download**:
    *   If licenses were successfully created or updated, their content is returned in the `license_file` key.
    *   If `download_path` is specified, the license file is also saved to that directory.

### Example
```yaml
- name: Create a new system and generate license keys
  community.sap_launchpad.license_keys:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    installation_nr: '12345678'
    system:
      # 'nr' is omitted to create a new system
      product: "SAP S/4HANA"
      version: "SAP S/4HANA 2022"
      data:
        sysid: "S4H"
        sysname: "s4hana-new-dev"
        systype: "Application Server (ABAP)"
        sysdb: "SAP HANA"
        sysos: "Linux on x86_64 64bit"
        sys_depl: "Private - On Premise"
    licenses:
      - type: "SAP S/4HANA"
        data:
          hwkey: "A1234567890"
          expdate: "99991231"
    download_path: "/tmp/licenses"
  register: result

- name: Update an existing system and remove other licenses
  community.sap_launchpad.license_keys:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    installation_nr: '12345678'
    system:
      nr: '0000123456' # Specify the system number to update
      product: "SAP S/4HANA"
      version: "SAP S/4HANA 2022"
      data:
        sysid: "S4H"
        sysname: "s4hana-new-dev"
        systype: "Application Server (ABAP)"
        sysdb: "SAP HANA"
        sysos: "Linux on x86_64 64bit"
        sys_depl: "Private - On Premise"
    licenses:
      - type: "SAP S/4HANA"
        data:
          hwkey: "A1234567890"
          expdate: "99991231"
    delete_other_licenses: true
  register: result

- name: Display the license file content
  ansible.builtin.debug:
    var: result.license_file
```

### Output format
#### license_file
- _Type:_ `string`<br>

The license file content containing the digital signatures of the specified licenses. This is returned when licenses are successfully generated or updated.
**Sample:**
```text
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
```

## Further Information
### Installation of prerequisites
**All preparation steps are included in role `sap_launchpad.sap_software_download`.**</br>

Prerequisite preparation using Python 3.11 Virtual Environment `/tmp/python_venv` (Recommended)
```yaml
---
- name: Example play to install prerequisites for sap_launchpad
  hosts: all
  tasks:
    - name: Install Python and Python package manager pip
      ansible.builtin.package:
        name:
          - python311
          - python311-pip
        state: present

    - name: Pre-Steps - Install Python modules to Python venv
      ansible.builtin.pip:
        name:
          - wheel
          - urllib3
          - requests
          - beautifulsoup4
          - lxml
        virtualenv: "/tmp/python_venv"
        virtualenv_command: "python3.11 -m venv"
```

Prerequisite preparation using Python 3.11 system default</br>
```yaml
---
- name: Example play to install prerequisites for sap_launchpad
  hosts: all
  tasks:
    - name: Install Python and Python package manager pip
      ansible.builtin.package:
        name:
          - python311
          - python311-pip
        state: present

    - name: Install Python module packages
      ansible.builtin.package:
        name:
          - python311-wheel
          - python311-urllib3
          - python311-requests
          - python311-beautifulsoup4
          - python311-lxml
        state: present
```
**NOTE:** Python modules are installed as packages to avoid `externally-managed-environment` error.

## License
Apache 2.0

## Maintainers
Maintainers are shown within [/docs/contributors](./CONTRIBUTORS.md).

## Module Variables
### suser_id
- _Required:_ `true`<br>
- _Type:_ `string`<br>

The SAP S-User ID with authorization to manage systems and licenses.

### suser_password
- _Required:_ `true`<br>
- _Type:_ `string`<br>

The password for the SAP S-User specified in `suser_id`.

### installation_nr
- _Required:_ `true`<br>
- _Type:_ `string`<br>

The SAP installation number under which the system is registered.

### system
- _Required:_ `true`<br>
- _Type:_ `dictionary`<br>

A dictionary containing the details of the system to create or update.
- **nr** (_string_): The 10-digit number of an existing system to update. If this is omitted, the module will attempt to create a new system.
- **product** (_string_): The product description as found in the SAP portal (e.g., `SAP S/4HANA`).
- **version** (_string_): The description of the product version (e.g., `SAP S/4HANA 2022`).
- **data** (_dictionary_): A dictionary of system attributes (e.g., `sysid`, `sysos`).

### licenses
- _Required:_ `true`<br>
- _Type:_ `list` of `dictionaries`<br>

A list of licenses to manage for the system.
- **type** (_string_): The license type description as found in the SAP portal (e.g., `Maintenance Entitlement`).
- **data** (_dictionary_): A dictionary of license attributes. The required attributes (e.g., `hwkey`, `expdate`) vary by license type.

### delete_other_licenses
- _Required:_ `false`<br>
- _Type:_ `boolean`<br>
- _Default:_ `false`<br>

If set to `true`, any licenses found on the system that are not specified in the `licenses` list will be removed.

### download_path
- _Required:_ `false`<br>
- _Type:_ `path`<br>

If specified, the generated license key file will be downloaded to this directory.
