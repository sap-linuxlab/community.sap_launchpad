# maintenance_planner_stack_xml_download Ansible Module

## Description
The Ansible Module `maintenance_planner_stack_xml_download` connects to the SAP Maintenance Planner to download the `stack.xml` file associated with a specific transaction.
- The `stack.xml` file contains the plan for a system update or installation and is used by tools like Software Update Manager (SUM).
- The file is saved to the specified destination directory.

## Dependencies
This module requires the following Python modules to be installed on the target node (the machine where SAP software will be downloaded):

- wheel
- urllib3
- requests
- beautifulsoup4
- lxml

Installation instructions are available at [Installation of prerequisites](#installation-of-prerequisites)

## Execution

### Execution Flow
The module follows a clear logic flow to download the stack XML file from a Maintenance Planner transaction.

1.  **Authentication**:
    *   The module first authenticates with the provided S-User credentials to establish a general session with the SAP Launchpad.
    *   It then performs a second authentication step against the `userapps.support.sap.com` service, which is required to access the Maintenance Planner API.

2.  **Transaction Lookup**:
    *   The module fetches a list of all Maintenance Planner transactions available to the user.
    *   It searches this list for a transaction that matches the provided `transaction_name` (checking both the name and the display ID). If no match is found, the module fails.

3.  **Stack XML Retrieval**:
    *   Using the ID of the found transaction, the module makes an API call to download the raw content of the `stack.xml` file.

4.  **File Creation**:
    *   The module validates that the provided `dest` path is an existing directory.
    *   It determines the filename from the response headers or creates a default name based on the transaction name.
    *   It writes the retrieved XML content to the destination file.

5.  **Return Data**:
    *   The module returns a success message indicating the full path where the `stack.xml` file was saved.

### Example
Obtain Stack file
```yaml
- name: Obtain Stack file
  community.sap_launchpad.maintenance_planner_stack_xml_download:
    suser_id: "Enter SAP S-User ID"
    suser_password: "Enter SAP S-User Password"
    transaction_name: "Transaction Name or Display ID from Maintenance Planner"
    dest: "/software"
  register: __module_results
```

Obtain Stack file using Python Virtual Environment `/tmp/venv`
```yaml
- name: Obtain Stack file using Python Virtual Environment
  community.sap_launchpad.maintenance_planner_stack_xml_download:
    suser_id: "Enter SAP S-User ID"
    suser_password: "Enter SAP S-User Password"
    transaction_name: "Transaction Name or Display ID from Maintenance Planner"
    dest: "/software"
  register: __module_results
  environment:
    PATH: "/tmp/venv:{{ ansible_env.PATH }}" 
    PYTHONPATH: "/tmp/venv/lib/python3.11/site-packages" 
    VIRTUAL_ENV: "/tmp/venv" 
  vars:
    ansible_python_interpreter: "/tmp/venv/bin/python3.11 }}"
```

### Output format
#### msg
- _Type:_ `string`<br>

The status of execution.

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

The SAP S-User ID with download authorization for SAP software.

### suser_password
- _Required:_ `true`<br>
- _Type:_ `string`<br>

The password for the SAP S-User specified in `suser_id`.

### transaction_name
- _Required:_ `true`<br>
- _Type:_ `string`<br>

The name or display ID of a transaction from the SAP Maintenance Planner.

### dest
- _Required:_ `true`<br>
- _Type:_ `string`<br>

The path to an existing destination directory where the stack.xml file will be saved.
