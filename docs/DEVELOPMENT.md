
# Development of community.sap_launchpad Ansible Collection

This Ansible Collection is developed with several design principles and code practices.

## Code structure

This Ansible Collection is heavily focused on Ansible Modules to perform required SAP Support API calls. The directory tree structure is shown below:
```code
collection/
├── docs/
├── meta/
├── plugins/
│   ├── modules/
│   │   ├── users.py
│   │   ├── software_center_download.py
│   │   ├── software_center_catalog.py
│   │   ├── maintenance_planner_files.py
│   │   ├── maintenance_planner_stack_xml_download.py
│   │   ├── licenses.py
│   │   └── incidents.py
│   └── module_utils/
│       ├── sap_id_sso.py
│       ├── sap_launchpad_software_center_download_runner.py
│       ├── sap_launchpad_software_center_catalog_runner.py
│       └── sap_launchpad_maintenance_planner_runner.py
├── roles/
├── playbooks/
│   ├── sample-download-install-media.yml
│   └── sample-maintenance-planner-download.yml
├── tests/
├── galaxy.yml
└── README.md
```

## Execution logic

This Ansible Collection is designed to be heavily re-usable for various SAP Support scenarios (both server-side and client-side), and avoid encapsulation of commands within Ansible's syntax; this ensures the scripts (and the sequence of commands) could be re-used manually or re-used by another automation framework.

It is important to understand the execution flow by an Ansible Playbook to either an Ansible Role (with or without embedded Playbooks), an Ansible Task, or an Ansible Module (and contained Script files). Alternatively it is possible to call the script files manually.


See examples below:

### Ansible Playbook to call many Ansible Roles (and the contained interlinked Ansible Tasks)
```code
# Produce outcome scenario, using many interlinked tasks
- Run: Ansible Playbook
  - Run: Ansible Role
    - Ansible Task
      - Ansible Playbook 1..n
        - Ansible Task
          - execute custom Ansible Module
            - execute specified Python Module Functions
              - call APIs or CLIs/binaries
    - Ansible Task
      - Ansible Playbook 1..n
        - Ansible Task
          - subsequent OS commands using output from APIs or CLIs/binaries
```

### Ansible Playbook to call single set of Ansible Tasks
```code
# Produce outcome scenario, with single set of tasks
- Run: Ansible Playbook
  - Ansible Task
    - execute custom Ansible Module
      - execute specified Python Module Functions
        - call APIs or CLIs/binaries
```

### Python Shell to call single Python Function
```code
# Produce outcome scenario manually with singular code execution
- Run: Python Shell
  - Import Python Module file for APIs or CLIs/binaries
  - Execute specificed Python Functions
```
