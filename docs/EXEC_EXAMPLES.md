# Execution examples

## Execution example with Ansible Playbook calling Ansible Module

**Ansible Playbook YAML, execute Ansible Module**
```yaml
---
- hosts: all

  collections:
    - community.sap_launchpad

  pre_tasks:
    - name: Install Python package manager pip3 to system Python
      yum:
        name: python3-pip
        state: present
    - name: Install Python dependencies for Ansible Modules to system Python
      pip:
        name:
          - urllib3
          - requests
          - beautifulsoup4
          - lxml

# Prompt for Ansible Variables
  vars_prompt:
    - name: suser_id
      prompt: Please enter S-User
      private: no
    - name: suser_password
      prompt: Please enter Password
      private: yes

# Define Ansible Variables
  vars:
    ansible_python_interpreter: python3
    softwarecenter_search_list: 
      - 'SAPCAR_1324-80000936.EXE'
      - 'HCMT_057_0-80003261.SAR'

# Use task block to call Ansible Module
  tasks:   
    - name: Execute Ansible Module to download SAP software
      community.sap_launchpad.software_center_download:
        suser_id: "{{ suser_id }}"
        suser_password: "{{ suser_password }}"
        softwarecenter_search_query: "{{ item }}"
      dest: "/tmp/"
      loop: "{{ softwarecenter_search_list }}"
      loop_control:
        label: "{{ item }} : {{ download_task.msg }}"
      register: download_task
      retries: 1
      until: download_task is not failed
```

**Execution of Ansible Playbook, with in-line Ansible Inventory set as localhost**

```shell
# Install from local source directory for Ansible 2.11+
ansible-galaxy collection install community.sap_launchpad

# Workaround install from local source directory for Ansible 2.9.x
# mv ./community.sap_launchpad ~/.ansible/collections/ansible_collections/community

# Run Ansible Collection on localhost
ansible-playbook --timeout 60 ./community.sap_launchpad/playbooks/sample-download-install-media.yml --inventory "localhost," --connection=local
```

## Execution example with Ansible Playbook calling Ansible Role

**Ansible Playbook YAML, execute Ansible Role on target/remote host**
```yaml
---
- hosts: all

  collections:
    - community.sap_launchpad

  pre_tasks:
    - name: Install Python package manager pip3 to system Python
      ansible.builtin.package:
        name: python3-pip
        state: present
    - name: Install Python dependencies for Ansible Modules to system Python
      ansible.builtin.pip:
        name:
          - urllib3
          - requests
          - beautifulsoup4
          - lxml

# Prompt for Ansible Variables
  vars_prompt:
    - name: suser_id
      prompt: Please enter S-User
      private: no
    - name: suser_password
      prompt: Please enter Password
      private: yes

# Define Ansible Variables
  vars:
    ansible_python_interpreter: python3
    softwarecenter_search_list: 
      - 'SAPCAR_1324-80000936.EXE'
      - 'HCMT_057_0-80003261.SAR'

# Option 1: Use roles declaration
  roles:
    - { role: community.sap_launchpad.software_center_download }

# Option 2: Use sequential parse/execution, by using include_role inside Task block
  tasks:
    - name: Execute Ansible Role to download SAP software
      include_role:
        name: { role: community.sap_launchpad.software_center_download }
      vars:
          suser_id: "{{ suser_id }}"
          suser_password: "{{ suser_password }}"
          softwarecenter_search_query: "{{ item }}"
      loop: "{{ softwarecenter_search_list }}"
      loop_control:
        label: "{{ item }} : {{ download_task.msg }}"
      register: download_task
      retries: 1
      until: download_task is not failed


# Option 3: Use task block with import_roles
  tasks:
    - name: Execute Ansible Role to download SAP software
      import_roles:
        name: { role: community.sap_launchpad.software_center_download }
      vars:
        suser_id: "{{ suser_id }}"
        suser_password: "{{ suser_password }}"
        softwarecenter_search_query: "{{ item }}"
      loop: "{{ softwarecenter_search_list }}"
      loop_control:
        label: "{{ item }} : {{ download_task.msg }}"
      register: download_task
      retries: 1
      until: download_task is not failed

```

**Execution of Ansible Playbook, with in-line Ansible Inventory of target/remote hosts**

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

## Execution example with Python environment

**Setup local Python environment**
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

**Execute Python Functions**
```python
>>> from module_utils.sap_launchpad_software_center_download_runner import *
>>>
>>> # Debug
>>> # from module_utils.sap_api_common import debug_https
>>> # debug_https()
>>>
>>> ## Perform API requests to SAP Support
>>> username='S0000000'
>>> password='password'
>>> sap_sso_login(username, password)
>>> query_result = search_software_filename("HCMT_057_0-80003261.SAR")
>>> download_software(*query_result, output_dir='/tmp')
...
>>> ## API responses from SAP Support
>>> exit()
```
