# systems_info Ansible Module

## Description
The Ansible Module `systems_info` queries the SAP Launchpad to retrieve a list of registered systems based on a filter string.
- It allows for fetching details about systems associated with the authenticated S-User.
- The OData filter expression allows for precise queries, for example, by installation number, system ID, or product description.

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
The module follows a straightforward logic flow to retrieve system information.

1.  **Authentication**:
    *   The module authenticates with the provided S-User credentials to establish a valid session with the SAP Launchpad.

2.  **System Query**:
    *   The module makes a GET request to the SAP Systems OData API.
    *   It passes the user-provided `filter` string directly to the API to query for specific systems.

3.  **Return Data**:
    *   The module returns the list of systems that match the filter criteria in the `systems` key.
    *   Each system in the list is a dictionary containing its details.

### Example
```yaml
- name: Get all systems for a specific installation number
  community.sap_launchpad.systems_info:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    filter: "Insnr eq '1234567890'"
  register: result

- name: Display system details
  ansible.builtin.debug:
    var: result.systems

- name: Get a specific system by SID and product description
  community.sap_launchpad.systems_info:
    suser_id: 'SXXXXXXXX'
    suser_password: 'password'
    filter: "Insnr eq '12345678' and sysid eq 'H01' and ProductDescr eq 'SAP S/4HANA'"
  register: result
```

### Output format
#### systems
- _Type:_ `list` of `dictionaries`<br>

A list of dictionaries, where each dictionary represents an SAP system.<br>
The product version ID may be returned under the 'Version' or 'Prodver' key, depending on the system's age and type.

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

The SAP S-User ID with authorization to get System information.

### suser_password
- _Required:_ `true`<br>
- _Type:_ `string`<br>

The password for the SAP S-User specified in `suser_id`.

### filter
- _Type:_ `string`<br>

An OData filter expression to query the systems.
