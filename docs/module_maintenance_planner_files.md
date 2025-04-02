# maintenance_planner_files Ansible Module

## Description
The Ansible Module `maintenance_planner_files` is used to obtain list of SAP Software files belonging to Maintenance Plan transaction.

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
Obtain list of SAP Software files
```yaml
- name: Obtain list of SAP Software files
  community.sap_launchpad.maintenance_planner_files:
    suser_id: "Enter SAP S-User ID"
    suser_password: "Enter SAP S-User Password"
    transaction_name: "Transaction Name or Display ID from Maintenance Planner"
  register: __module_results
```

Obtain list of SAP Software files using Python Virtual Environment `/tmp/python_venv`
```yaml
- name: Obtain list of SAP Software files using Python Virtual Environment
  community.sap_launchpad.maintenance_planner_files:
    suser_id: "Enter SAP S-User ID"
    suser_password: "Enter SAP S-User Password"
    transaction_name: "Transaction Name or Display ID from Maintenance Planner"
  register: __module_results
  environment:
    PATH: "/tmp/python_venv:{{ ansible_env.PATH }}" 
    PYTHONPATH: "/tmp/python_venv/lib/python3.11/site-packages" 
    VIRTUAL_ENV: "/tmp/python_venv" 
  vars:
    ansible_python_interpreter: "/tmp/python_venv/bin/python3.11 }}"
```

### Output format
#### msg
- _Type:_ `string`<br>

The status of execution.

#### download_basket
- _Type:_ `list` with elements of type `dictionary`<br>

A Json list of software download links and filenames.<br>
```yml
- DirectLink: https://softwaredownloads.sap.com/file/0020000001739942021
  Filename: IMDB_SERVER20_060_0-80002031.SAR
- DirectLink: https://softwaredownloads.sap.com/file/0010000001440232021
  Filename: KD75379.SAR
```

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
