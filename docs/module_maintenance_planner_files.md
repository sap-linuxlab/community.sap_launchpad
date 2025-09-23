# maintenance_planner_files Ansible Module

## Description
The Ansible Module `maintenance_planner_files` connects to the SAP Maintenance Planner to retrieve a list of all downloadable files associated with a specific transaction.
- It returns a list containing direct download links and filenames for each file.
- This is useful for automating the download of a complete stack file set defined in a Maintenance Planner transaction.

## Dependencies
This module requires the following Python modules to be installed on the target node (the machine where SAP software will be downloaded):

- wheel
- urllib3
- requests
- beautifulsoup4
- lxml

## Execution

### Execution Flow
The module follows a clear logic flow to retrieve the file list from a Maintenance Planner transaction.

1.  **Authentication**:
    *   The module first authenticates with the provided S-User credentials to establish a general session with the SAP Launchpad.
    *   It then performs a second authentication step against the `userapps.support.sap.com` service, which is required to access the Maintenance Planner API.

2.  **Transaction Lookup**:
    *   The module fetches a list of all Maintenance Planner transactions available to the user.
    *   It searches this list for a transaction that matches the provided `transaction_name` (checking both the name and the display ID). If no match is found, the module fails.

3.  **File List Retrieval**:
    *   Using the ID of the found transaction, the module makes an API call to retrieve the stack XML file that defines all the downloadable files for that transaction.
    *   It parses this XML to extract a list of direct download links and their corresponding filenames.

4.  **URL Validation (Optional)**:
    *   If `validate_url` is set to `true`, the module will perform a `HEAD` request for each download link to verify that it is active and accessible. If any link is invalid, the module will fail.

5.  **Return Data**:
    *   The module returns the final list of files as the `download_basket`, with each item containing a `DirectLink` and a `Filename`.

### Example
> **NOTE:** The Python versions in these examples vary by operating system. Always use the version that is compatible with your specific system or managed node.</br>
> To simplify this process, the Ansible Role `sap_launchpad.sap_software_download` will install the correct Python version and required modules for you.</br>

Obtain list of SAP Software files using existing System Python.
```yaml
---
- name: Example play for Ansible Module maintenance_planner_files
  hosts: all
  tasks:
    - name: Obtain list of SAP Software files
      community.sap_launchpad.maintenance_planner_files:
        suser_id: "Enter SAP S-User ID"
        suser_password: "Enter SAP S-User Password"
        transaction_name: "Transaction Name or Display ID from Maintenance Planner"
      register: __module_results
```

Obtain list of SAP Software files using existing Python Virtual Environment `/tmp/python_venv`.
```yaml
---
- name: Example play for Ansible Module maintenance_planner_files
  hosts: all
  tasks:
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

Install prerequisites and obtain list of SAP Software files using existing System Python.</br>
**NOTE:** Python modules are installed as packages to avoid `externally-managed-environment` error.
```yaml
---
- name: Example play for Ansible Module maintenance_planner_files
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

    - name: Obtain list of SAP Software files
      community.sap_launchpad.maintenance_planner_files:
        suser_id: "Enter SAP S-User ID"
        suser_password: "Enter SAP S-User Password"
        transaction_name: "Transaction Name or Display ID from Maintenance Planner"
      register: __module_results
```

Install prerequisites and obtain list of SAP Software files using existing Python Virtual Environment `/tmp/python_venv`.
```yaml
---
- name: Example play for Ansible Module maintenance_planner_files
  hosts: all
  tasks:
    - name: Install Python and Python package manager pip
      ansible.builtin.package:
        name:
          - python311
          - python311-pip
        state: present

    - name: Install Python modules to Python venv
      ansible.builtin.pip:
        name:
          - wheel
          - urllib3
          - requests
          - beautifulsoup4
          - lxml
        virtualenv: "/tmp/python_venv"
        virtualenv_command: "python3.11 -m venv"

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

### validate_url
- _Type:_ `boolean`<br>

Validate if the download links are available and not expired.
