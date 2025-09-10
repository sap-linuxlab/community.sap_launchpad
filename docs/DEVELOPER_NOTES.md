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
**NOTE:** Python modules are installed as packages to avoid `externally-managed-environment` error.
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
