# software_center_download Ansible Module

## Description
The Ansible Module `software_center_download` is used to download SAP Software file from SAP.

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
Download SAP Software file
```yaml
- name: Download SAP Software file
  community.sap_launchpad.software_center_download:
    suser_id: "Enter SAP S-User ID"
    suser_password: "Enter SAP S-User Password"
    search_query: "Enter SAP Software file name"
    download_path: "Enter download path (e.g. /software)"
```

Download SAP Software file, but search for alternatives if not found
```yaml
- name: Download SAP Software file with alternative
  community.sap_launchpad.software_center_download:
    suser_id: "Enter SAP S-User ID"
    suser_password: "Enter SAP S-User Password"
    search_query: "Enter SAP Software file name"
    download_path: "Enter download path (e.g. /software)"
    search_alternatives: true
    deduplicate: "last"
```

Download list of SAP Software files, but search for alternatives if not found
```yaml
- name: Download list of SAP Software files
  community.sap_launchpad.software_center_download:
    suser_id: "Enter SAP S-User ID"
    suser_password: "Enter SAP S-User Password"
    search_query: "{{ item }}"
    download_path: "Enter download path (e.g. /software)"
    search_alternatives: true
    deduplicate: "last"
  loop:
    - "Enter SAP Software file name 1"
    - "Enter SAP Software file name 2"
  loop_control:
    label: "{{ item }} : {{ __module_results.msg | d('') }}"
  register: __module_results
  retries: 1
  until: __module_results is not failed
```

Download SAP Software file using Python Virtual Environment `/tmp/venv`
```yaml
- name: Download list of SAP Software files
  community.sap_launchpad.software_center_download:
    suser_id: "Enter SAP S-User ID"
    suser_password: "Enter SAP S-User Password"
    search_query: "{{ item }}"
    download_path: "Enter download path (e.g. /software)"
  loop:
    - "Enter SAP Software file name 1"
    - "Enter SAP Software file name 2"
  loop_control:
    label: "{{ item }} : {{ __module_results.msg | d('') }}"
  register: __module_results
  retries: 1
  until: __module_results is not failed
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

### search_query
- _Type:_ `string`<br>

The SAP software file name to download.

### download_link
- _Type:_ `string`<br>

Direct download link to the SAP software.</br>
Download links can be obtained from SAP Software Center or using module `module_maintenance_planner_files`.

### download_filename
- _Type:_ `string`<br>

Download filename of the SAP software.</br>
Download names can be obtained from SAP Software Center or using module `module_maintenance_planner_files`.

### download_path
- _Required:_ `true`<br>
- _Type:_ `string`<br>

The directory where downloaded SAP software files will be stored.

### deduplicate
- _Type:_ `string`<br>

Specifies how to handle duplicate file results.<br>
If multiple files with the same name are found, this setting determines which one to download.<br>
- `first`: Download the first file found<br>
- `last`: Download the last file found.<br>

### search_alternatives
- _Type:_ `boolean`<br>

Enables searching for alternative files if the requested file is not found.<br>

### dry_run
- _Type:_ `boolean

Check availability of SAP Software without downloading.<br>
