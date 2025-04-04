# community.sap_launchpad Ansible Collection

![Ansible Lint](https://github.com/sap-linuxlab/community.sap_launchpad/actions/workflows/ansible-lint.yml/badge.svg?branch=main)

## Description

This Ansible Collection provides roles and modules to automate interaction with SAP Launchpad API, primarily focusing on downloading software and files from the SAP Software Download Center and Maintenance Planner.

Included role and modules cover range of options:
- Preparation of environment before download.
- Download of specific SAP Software files.
- Download of alternative SAP Software files if specific was not available. 
- Download of SAP Software files from existing Maintenance Plan transaction.
- Download of Stack file from existing Maintenance Plan transaction.


## Requirements

### Control Nodes
| Type | Version |
| :--- | :--- |
| Operating system | Any operating system with required Python and Ansible versions |
| Python | 3.11 or higher |
| Ansible | 9.9 or higher |
| Ansible-core | 2.16 or higher |


### Managed Nodes
| Type | Version |
| :--- | :--- |
| Operating system | SUSE Linux Enterprise Server 15 SP5+, 16 <br> Red Hat Enterprise Linux 8.x, 9.x, 10.x |
| Python | 3.11 or higher (SUSE) <br> 3.9 or higher (Red Hat) |

**NOTE: Operating system needs to have access to required package repositories either directly or via subscription registration.**


## Installation Instructions

### Installation
Install this collection with Ansible Galaxy command:
```console
ansible-galaxy collection install community.sap_launchpad
```

Optionally you can include collection in requirements.yml file and include it together with other collections using: `ansible-galaxy collection install -r requirements.yml`
Requirements file need to be maintained in following format:
```yaml
collections:
  - name: community.sap_launchpad
```

### Upgrade
Installed Ansible Collection will not be upgraded automatically when Ansible package is upgraded.

To upgrade the collection to the latest available version, run the following command:
```console
ansible-galaxy collection install community.sap_launchpad --upgrade
```

You can also install a specific version of the collection, when you encounter issues with latest version. Please report these issues in affected Role repository if that happens.
Example of downgrading collection to version 1.0.0:
```
ansible-galaxy collection install community.sap_launchpad:==1.0.0
```

See [Installing collections](https://docs.ansible.com/ansible/latest/collections_guide/collections_installing.html) for more details on installation methods.


## Contents

### Ansible Modules
| Name | Summary |
| :-- | :-- |
| [sap_launchpad.software_center_download](./docs/module_software_center_download.md) | Search and download SAP Software file |
| [sap_launchpad.maintenance_planner_files](./docs/module_maintenance_planner_files.md) | Get list of files from Maintenance Planner |
| [sap_launchpad.maintenance_planner_stack_xml_download](./docs/module_maintenance_planner_stack_xml_download.md) | Get stack file from Maintenance Planner |

### Ansible Roles
| Name | Summary |
| :-- | :-- |
| [sap_software_download](./roles/sap_software_download/README.md) | Prepare environment and download SAP Software files or Maintenance Plan transaction files |


## Testing
This Ansible Collection was tested across different Operating Systems and SAP products.

| Type | Version |
| :--- | :--- |
| Operating system | SUSE Linux Enterprise Server 15 SP5+, 16 <br> Red Hat Enterprise Linux 8.x, 9.x, 10.x |
| Python | 3.11, 3.12 |
| Ansible | 9, 10, 11 |
| Ansible-core | 2.16, 2.17, 2.18 |


## Contributing
You can find more information about ways you can contribute at [sap-linuxlab website](https://sap-linuxlab.github.io/initiative_contributions/).


## Support
You can report any issues using [Issues](https://github.com/sap-linuxlab/community.sap_launchpad/issues) section.


## Release Notes and Roadmap
You can find the release notes of this collection in [Changelog file](./CHANGELOG.rst)


## Further Information

### Credentials - SAP S-User

SAP software files must be obtained from SAP directly, and requires valid license agreements with SAP in order to access these files.

An SAP Company Number (SCN) contains one or more Installation Number/s, providing licenses for specified SAP Software. When an SAP User ID is created within the SAP Customer Number (SCN), the administrator must provide SAP Download authorizations for the SAP User ID.

When an SAP User ID (e.g. S-User) is enabled with and part of an SAP Universal ID, then the `sap_launchpad` Ansible Collection **must** use:
- the SAP User ID
- the password for login with the SAP Universal ID

In addition, if a SAP Universal ID is used then the recommendation is to check and reset the SAP User ID ‘Account Password’ in the [SAP Universal ID Account Manager](https://account.sap.com/manage/accounts), which will help to avoid any potential conflicts.

For further information regarding connection errors, please see the FAQ section [Errors with prefix 'SAP SSO authentication failed - '](./docs/FAQ.md#errors-with-prefix-sap-sso-authentication-failed---).

**Multi Factor Authentication is not supported.**

### Variable Precedence Rules
Please follow [Ansible Precedence guidelines](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable) on how to pass variables when using this collection.

## License
[Apache 2.0](./LICENSE)
