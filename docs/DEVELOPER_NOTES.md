# Developer notes for community.sap_launchpad Ansible Collection

This document contains details for maintaining Ansible Collection.

## Dependencies for all modules
Modules require the following Python modules to be installed on the target node (the machine where SAP software will be downloaded):

- wheel
- urllib3
- requests
- beautifulsoup4
- lxml

### Installation of dependencies using role `sap_software_download`
Ansible Role `sap_software_download` installs all required dependencies as part of `02_prepare_python_environment.yml` task file.

### Installation of dependencies with Python Virtual Environment (venv)
It is recommended to install dependencies in venv that can be removed after execution is completed.
```yaml
- name: Example play to install prerequisites with Python Virtual Environment
  hosts: all
  tasks:
    - name: Create temporary directory for Python Virtual Environment
      ansible.builtin.tempfile:
        state: directory
        suffix: __sap_software_download_venv
      register: __sap_software_download_venv

    - name: Install Python and Python package manager pip
      ansible.builtin.package:
      name:
        - python311
        - python311-pip
      state: present

    - name: Install Python modules to Python Virtual Environment
      ansible.builtin.pip:
        name:
          - wheel
          - urllib3
          - requests
          - beautifulsoup4
          - lxml
        virtualenv: "{{ __sap_software_download_venv.path }}"
        virtualenv_command: "python3.11 -m venv"

    - name: Remove temporary Python Virtual Environment
      ansible.builtin.file:
        path: "{{ __sap_software_download_venv.path }}"
        state: absent
```

### Installation of dependencies with Python system default
```yaml
- name: Example play to install prerequisites with Python system default
  hosts: all
  tasks:
    - name: Install Python and Python package manager pip
      ansible.builtin.package:
      name:
        - python31
        - python311-pip
      state: present

    - name: Install Python modules to Python system default
      ansible.builtin.pip:
      name:
        - wheel
        - urllib3
        - requests
        - beautifulsoup4
        - lxml
```

## Additional execution methods
### Execution of Ansible Playbook, with in-line Ansible Inventory set as localhost

```shell
# Install from local source directory for Ansible 2.11+
ansible-galaxy collection install community.sap_launchpad

# Workaround install from local source directory for Ansible 2.9.x
# mv ./community.sap_launchpad ~/.ansible/collections/ansible_collections/community

# Run Ansible Collection on localhost
ansible-playbook --timeout 60 ./community.sap_launchpad/playbooks/sample-download-install-media.yml --inventory "localhost," --connection=local
```

### Execution of Ansible Playbook, with in-line Ansible Inventory of target/remote hosts

```shell
# Install from local source directory for Ansible 2.11+
ansible-galaxy collection install ./community.sap_launchpad

# Workaround install from local source directory for Ansible 2.9.x
# mv ./community.sap_launchpad ~/.ansible/collections/ansible_collections/community

# SSH Connection details
bastion_private_key_file="$PWD/bastion_rsa"
bastion_host="169.0.40.4"
bastion_port="50222"
bastion_user="bastionuser"

target_private_key_file="$PWD/vs_rsa"
target_host="10.0.50.5"
target_user="root"

# Run Ansible Collection to target/remote hosts via Proxy/Bastion
ansible-playbook --timeout 60 ./sample-playbook.yml \
--connection 'ssh' --user "$target_user" --inventory "$target_host," --private-key "$target_private_key_file" \
--ssh-extra-args="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ProxyCommand='ssh -W %h:%p $bastion_user@$bastion_host -p $bastion_port -i $bastion_private_key_file -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'"
```

## Execution of Python Modules directly
### Setup local Python environment
```shell
# Change directory to Python scripts source
cd ./plugins

# Create isolated Python (protect system Python)
pyenv install 3.9.6
pyenv virtualenv 3.9.6 sap_launchpad
pyenv activate sap_launchpad

# Install Python Modules to current Python environment
pip3 install beautifulsoup4 lxml requests

# Run Python, import Python Modules and run Python Functions
python3
```

### Execute Python Functions
```python
>>> from module_utils.sap_id_sso import sap_sso_login
>>> from module_utils.sap_launchpad_software_center_download_runner import *
>>>
>>> # Debug
>>> # from module_utils.sap_api_common import debug_https
>>> # debug_https()
>>>
>>> ## Perform API login requests to SAP Support
>>> username='S0000000'
>>> password='password'
>>> sap_sso_login(username, password)
>>> ## Perform API activity requests to SAP Support (e.g. software search without deduplication, and download software)
>>> query_result = search_software_filename("HCMT_057_0-80003261.SAR",'')
>>> download_software(*query_result, output_dir='/tmp')
...
>>> ## API responses from SAP Support
>>> exit()
```
