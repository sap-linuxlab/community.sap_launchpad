# maintenance_planner_stack_xml_download Ansible Module

## Description
The Ansible Module `maintenance_planner_stack_xml_download` is used to obtain Stack file belonging to Maintenance Plan transaction.

## Dependencies
This module requires the following Python modules to be installed on the target node (the machine where SAP software will be downloaded):

- wheel
- urllib3
- requests
- beautifulsoup4
- lxml

Installation instructions are available at [Installation of prerequisites](#installation-of-prerequisites)

## Execution

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
  pre_tasks:
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
  pre_tasks:
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

The directory where downloaded SAP software files will be stored.
