# community.sap_launchpad Ansible Collection ![Ansible Lint](https://github.com/sap-linuxlab/community.sap_launchpad/actions/workflows/ansible-lint.yml/badge.svg?branch=main)

This Ansible Collection executes basic SAP.com Support operations tasks.

## Functionality

This Ansible Collection executes basic SAP.com Support operations tasks, including:

- **Software Center Catalog**
  - Search and Download of SAP software center catalog files
  - Search and Extraction of SAP software center catalog information
- **Maintenance Planner**
  - Lookup and download files from an existing 'New Implementation' MP Transaction and Stack, using SAP software center's download basket

## Contents

An Ansible Playbook can call either an Ansible Role, or the individual Ansible Modules for handling the API calls to various SAP Support Portal API capabilities:
- **Ansible Roles** (runs multiple Ansible Modules)
- **Ansible Modules** (and adjoining Python Functions)

For further information regarding the development, code structure and execution workflow please read the [Development documentation](./docs/DEVELOPMENT.md).

Within this Ansible Collection, there are various Ansible Modules.

#### Ansible Modules

| Name &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; | Summary |
| :-- | :-- |
| [sap_launchpad.software_center_download](./docs/module_software_center_download.md) | search for files and download |
| [sap_launchpad.maintenance_planner_files](./docs/module_maintenance_planner_files.md) | maintenance planner files retrieval |
| [sap_launchpad.maintenance_planner_stack_xml_download](./docs/module_maintenance_planner_stack_xml_download.md) | maintenance planner stack xml download |

## Execution

### Credentials - SAP User ID

SAP software installation media must be obtained from SAP directly, and requires valid license agreements with SAP in order to access these files.

An SAP Company Number (SCN) contains one or more Installation Number/s, providing licences for specified SAP Software. When an SAP User ID is created within the SAP Customer Number (SCN), the administrator must provide SAP Download authorizations for the SAP User ID.

When an SAP User ID (e.g. S-User) is enabled with and part of an SAP Universal ID, then the `sap_launchpad` Ansible Collection **must** use:
- the SAP User ID
- the password for login with the SAP Universal ID

In addition, if a SAP Universal ID is used then the recommendation is to check and reset the SAP User ID ‘Account Password’ in the [SAP Universal ID Account Manager](https://account.sap.com/manage/accounts), which will help to avoid any potential conflicts.

For further information regarding connection errors, please see the FAQ section [Errors with prefix 'SAP SSO authentication failed - '](./docs/FAQ.md#errors-with-prefix-sap-sso-authentication-failed---).

### Execution examples

There are various methods to execute the Ansible Collection, dependant on the use case. For more information, see [Execution examples with code samples](./docs/EXEC_EXAMPLES.md) and the summary below:

| Execution Scenario | Use Case | Target |
| --- | --- | --- |
| Ansible Playbook <br/>-> source Ansible Collection <br/>-> execute Ansible Task <br/>--> run Ansible Module <br/>---> run Python/Bash Functions | Simple executions with a few activities | Localhost or Remote |
| Ansible Playbook <br/>-> source Ansible Collection <br/>-> execute Ansible Task <br/>--> run Ansible Role <br/>---> run Ansible Module <br/>----> run Python/Bash Functions <br/>--> run Ansible Role<br/>---> ... | Complex executions with various interlinked activities;<br/> run in parallel or sequentially | Localhost or Remote |
| Python/Bash Functions | Simple testing or non-Ansible use cases | Localhost |

---

## Requirements, Dependencies and Testing

### Operating System requirements

Designed for Linux operating systems, e.g. RHEL.

This role has not been tested and amended for SAP NetWeaver Application Server instantiations on IBM AIX or Windows Server.

Assumptions for executing this role include:
- Registered OS License and OS Package repositories are available (from the relevant content delivery network of the OS vendor)
- Simultaneous Ansible Playbook executions will require amendment of Ansible Variable name `softwarecenter_search_list` shown in execution samples (containing the list of installation media to download). This avoids accidental global variable clashes from occuring in Ansible Playbooks executed from the same controller host with an inline Ansible Inventory against 'all' target hosts.

### Python requirements

Execution/Controller/Management host:
- Python 3

Target host:
- Python 3, with Python Modules `beautifulsoup4 lxml requests` (see [Execution examples with code samples](./docs/EXEC_EXAMPLES.md))

### Testing on execution/controller host

**Tests with Ansible Core release versions:**
- Ansible Core 2.11.5 community edition

**Tests with Python release versions:**
- Python 3.9.7 (i.e. CPython distribution)

**Tests with Operating System release versions:**
- RHEL 8.4
- macOS 11.6 (Big Sur), with Homebrew used for Python 3.x via PyEnv

### Testing on target/remote host

**Tests with Operating System release versions:**
- RHEL 8.2 for SAP

**Tests with Python release versions:**
- Python 3.6.x (i.e. CPython distribution), default for RHEL 8.x and SLES 15.x
- Python 3.8.x (i.e. CPython distribution)

## License

- [Apache 2.0](./LICENSE)

## Contributors

Contributors to the Ansible Roles within this Ansible Collection, are shown within [/docs/contributors](./docs/CONTRIBUTORS.md).
