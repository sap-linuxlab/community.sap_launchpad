<!-- BEGIN Title -->
# sap_software_download Ansible Role
<!-- END Title -->

## Description
<!-- BEGIN Description -->
The Ansible Role `sap_software_download` is used to download SAP Software Media from SAP.
<!-- END Description -->

<!-- BEGIN Dependencies -->
## Dependencies
This role requires the following Python modules to be installed on the target node (the machine where SAP software will be downloaded):

- wheel
- urllib3
- requests
- beautifulsoup4
- lxml

The role installs these modules if they are not already present. Installation can be done in one of the following ways:

- **Virtual Environment (Default):**
  - When `sap_software_download_use_venv` is `true` (default), a temporary virtual environment is created, and modules are installed via `pip`.
  - The Python version is determined by `sap_software_download_python_interpreter`.
- **System Environment:**
  - When `sap_software_download_use_venv` is `false`, modules are installed directly into the system's Python environment using OS packages specified by `sap_software_download_python_module_packages`.
<!-- END Dependencies -->

<!-- BEGIN Prerequisites -->
## Prerequisites
The target node must meet the following requirements:

*   **OS Package Repositories:** The operating system must be registered and have access to repositories to install the required Python packages.
    *   The actual package name is determined by the `sap_software_download_python_package` variable.
    *   For example, on some systems, these packages might be named `python3` and `python3-pip`. 
<!-- END Prerequisites -->

## Execution
<!-- BEGIN Execution -->
<!-- END Execution -->

<!-- BEGIN Execution Recommended -->
<!-- END Execution Recommended -->

### Execution Flow
<!-- BEGIN Execution Flow -->
1.  **Input Validation:** The role first checks if all required input variables have been provided.
2.  **Python Environment Preparation:** The role prepares the Python environment:
    *   **Virtual Environment (Default):** A temporary Python virtual environment is created, and all necessary dependencies are installed within it.
    *   **System Environment:** Alternatively, if `sap_software_download_use_venv` is set to `false`, dependencies are installed directly into the system's default Python environment.
3.  **Validate provided S-User credentials** The role will search for `SAPCAR` file to validate credentials and download authorization. 
4.  **Maintenance Plan File List:** If the `sap_software_download_mp_transaction` variable is provided, the role retrieves the list of files associated with the specified Maintenance Plan transaction.
5.  **File Relationship Validation:** If `sap_software_download_validate_relationships` is `true`, the role performs validation checks on the relationships between the files to be downloaded.
    *   **Alternative File Search:** If `sap_software_download_find_alternatives` is `true`, the role will search for alternative files during relationship validation if the requested files are not found.
    *   More information about validation logic is available at [Explanation of relationship validation logic](#explanation-of-relationship-validation-logic)
6.  **Maintenance Plan File Download:** If `sap_software_download_mp_transaction` is provided, the role downloads the files associated with the Maintenance Plan.
7.  **Direct File Download:** If `sap_software_download_files` is provided, the role downloads the specified files.
8.  **Virtual Environment Cleanup:** If a temporary Python virtual environment was used, it is removed.

<!-- END Execution Flow -->

### Example
<!-- BEGIN Execution Example -->
Download of SAP Software files using input list.
```yaml
---
- name: Ansible Play for downloading SAP Software
  hosts: localhost
  become: true
  tasks:
    - name: Include role sap_software_download
      ansible.builtin.include_role:
        name: community.sap_launchpad.sap_software_download
      vars:
        sap_software_download_suser_id: "Enter SAP S-User ID"
        sap_software_download_suser_password: "Enter SAP S-User Password"
        sap_software_download_directory: "/software"
        sap_software_download_validate_checksum: true
        sap_software_download_files:
          - 'SAPCAR_1115-70006178.EXE'
          - 'SAPEXE_100-80005509.SAR'
```

Download of SAP Software files using Maintenance Plan.
```yaml
---
- name: Ansible Play for downloading SAP Software
  hosts: localhost
  become: true
  tasks:
    - name: Include role sap_software_download
      ansible.builtin.include_role:
        name: community.sap_launchpad.sap_software_download
      vars:
        sap_software_download_suser_id: "Enter SAP S-User ID"
        sap_software_download_suser_password: "Enter SAP S-User Password"
        sap_software_download_directory: "/software"
        sap_software_download_validate_checksum: true
        sap_software_download_mp_transaction: 'MY-TRANSACTION-NAME'
```

Combined download of SAP Software files and Maintenance Plan transaction together with settings:
- Use default Python instead of Python virtual environment.
- No validation of S-User credentials.
- No validation of relationships.
- No warnings for unavailable files.
- No warnings for unavailable Maintenance Plan transaction.
- Validate checksum of already existing files with same name.
```yaml
- name: Ansible Play for downloading SAP Software
  hosts: localhost
  become: true
  tasks:
    - name: Include role sap_software_download
      ansible.builtin.include_role:
        name: community.sap_launchpad.sap_software_download
      vars:
        sap_software_download_suser_id: "Enter SAP S-User ID"
        sap_software_download_suser_password: "Enter SAP S-User Password"
        sap_software_download_directory: "/software"
        sap_software_download_use_venv: false
        sap_software_download_ignore_validate_credentials: true
        sap_software_download_ignore_file_not_found: true
        sap_software_download_ignore_plan_not_found: true
        sap_software_download_validate_relationships: false
        sap_software_download_deduplicate: last
        sap_software_download_validate_checksum: true
        sap_software_download_files:
          - 'SAPCAR_1115-70006178.EXE'
          - 'SAPEXE_100-80005509.SAR'
        sap_software_download_mp_transaction: 'MY-TRANSACTION-NAME'
```
Download of SAP Software files using Python version `3.13`.
```yaml
---
- name: Ansible Play for downloading SAP Software
  hosts: localhost
  become: true
  tasks:
    - name: Include role sap_software_download
      ansible.builtin.include_role:
        name: community.sap_launchpad.sap_software_download
      vars:
        sap_software_download_python_interpreter: python3.13
        sap_software_download_python_package: python313
        sap_software_download_python_module_packages:
          - python313-wheel
          - python313-urllib3
          - python313-requests
          - python313-beautifulsoup4
          - python313-lxml
        sap_software_download_suser_id: "Enter SAP S-User ID"
        sap_software_download_suser_password: "Enter SAP S-User Password"
        sap_software_download_directory: "/software"
        sap_software_download_validate_checksum: true
        sap_software_download_files:
          - 'SAPCAR_1115-70006178.EXE'
          - 'SAPEXE_100-80005509.SAR'
```
<!-- END Execution Example -->

<!-- BEGIN Role Tags -->
<!-- END Role Tags -->

<!-- BEGIN Further Information -->
## Further Information
### Explanation of relationship validation logic
Validation is executed for known combinations of SAP files, where we can validate their file name, extract versions and compare them.<br>
Supported scenarios:

- SAP HANA file `IMDB_SERVER` and components: `IMDB_AFL`, `IMDB_LCAPPS`, `IMDB_CLIENT`.
- SAP Kernel file `SAPEXE` and components: `SAPEXEDB`.

> **Limitations:**<br>
>
> 1. Multiple files for same component are not supported, because relationship validation is designed for one SAP System.
> 2. File contents and manifest are not validated, instead file name is used for validation.
> 3. Compatible operating system is not validated, because unique File ID is different for each component and operating system.
> 4. Searching for alternatives and upgrade candidates will result in longer execution times when `sap_software_download_find_alternatives` or `sap_software_download_upgrade_relationships` are set to `true`.


#### SAP HANA Server (IMDB_SERVER)
1. Find all files starting with prefix `IMDB_SERVER`, `IMDB_AFL`, `IMDB_LCAPPS`, `IMDB_CLIENT` in `sap_software_download_files`.
   - Fail if multiple files with same prefix are found.
2. Parse file name of `IMDB_SERVER` file to determine SAP HANA version, revision, patch and file ID.
3. Attempt to download `IMDB_SERVER` file in `dry_run` mode to validate its availability.
   - If alternative was found, update software list with new file name.
   - Fail if file is not found and the variable `sap_software_download_upgrade_relationships` is set to `false`.
4. Attempt to download upgrade candidate for `IMDB_SERVER` file in `dry_run` mode if previous attempt failed and `sap_software_download_upgrade_relationships` is set to `true`.
   - If upgrade candidate was found, update software list with new file name.
   - Fail if file is not found.
5. Start validation for detected components `IMDB_AFL`, `IMDB_LCAPPS`, `IMDB_CLIENT`. Following steps show example for `IMDB_AFL`.
6. Parse file name of `IMDB_AFL` file to determine SAP HANA version, revision, patch and file ID.
   - Fail if `IMDB_AFL` is for a different SAP HANA version (e.g. `IMDB_AFL` for 1.0 while `IMDB_SERVER` is 2.0).
7. Attempt to download `IMDB_AFL` file in `dry_run` mode to validate its availability.
   - If alternative was found, update software list with new file name.
   - Fail if file is not found and the variable `sap_software_download_upgrade_relationships` is set to `false`.
8. Create search regex to validate that `IMDB_AFL` has same revision and patch as `IMDB_SERVER`.
9. Attempt to download upgrade candidate for `IMDB_AFL` file in `dry_run` mode if previous attempt failed and `sap_software_download_upgrade_relationships` is set to `true`. Uses search query based on version details of `IMDB_SERVER`.
   - If upgrade candidate was found, update software list with new file name.
   - Fail if file is not found.
10. Show summary of validation and fail if validation has failed.


**File name versioning breakdown**
| File name | Version | Revision | Patch | File ID |
| --- | --- | --- | --- | --- |
| IMDB_SERVER100_122_35-10009569.SAR | 1.0 | 122 | 35 | 10009569 |
| IMDB_AFL100_122P_3500-10012328.SAR | 1.0 | 122 | 35 | 10012328 |
| IMDB_LCAPPS_122P_3500-20010426.SAR | 1.0 | 122 | 35 | 20010426 |
| IMDB_CLIENT100_120_140-10009663.SAR | 1.0 | N/A | 140 | 10009663 |
| IMDB_SERVER20_089_3-80002031.SAR | 2.0 | 89 | 3 | 80002031 |
| IMDB_AFL20_089P_300-80001894.SAR | 2.0 | 89 | 3 | 80001894 |
| IMDB_LCAPPS_2089P_300-20010426.SAR | 2.0 | 89 | 3 | 20010426 |
| IMDB_CLIENT20_028_22-80002082.SAR | 2.0 | N/A | 22 | 80002082 |

> **NOTES:**<br>
> - `IMDB_AFL` and `IMDB_LCAPPS` expand patch number when bugfixes are released. Patch `1` can be `1`, but if bugfix occurs then all future numbers will be in thousands (e.g. `2000` for patch `2`).<br>
> - `IMDB_CLIENT` is not tied to same Revision and Patch as `IMDB_SERVER` and other components.<br>


#### SAP Kernel (SAPEXE)
1. Find all files starting with prefix `SAPEXE` and `SAPEXEDB` in `sap_software_download_files`.
   - Fail if multiple files with same prefix are found.
2. Parse file name of `SAPEXE` file to determine SAP Kernel patch and file ID.
3. Attempt to download `SAPEXE` file in `dry_run` mode to validate its availability.
   - If alternative was found, update software list with new file name.
   - Fail if file is not found and the variable `sap_software_download_upgrade_relationships` is set to `false`.
4. Attempt to download upgrade candidate for `SAPEXE` file in `dry_run` mode if previous attempt failed and `sap_software_download_upgrade_relationships` is set to `true`.
   - If upgrade candidate was found, update software list with new file name.
   - Fail if file is not found.
5. Start validation for `SAPEXEDB`.
6. Parse file name of `SAPEXEDB` file to determine SAP Kernel patch and file ID.
7. Attempt to download `SAPEXEDB` file in `dry_run` mode to validate its availability.
   - If alternative was found, update software list with new file name.
   - Fail if file is not found and the variable `sap_software_download_upgrade_relationships` is set to `false`.
8. Create search regex to validate that `SAPEXEDB` has same patch as `SAPEXE`.
9. Attempt to download upgrade candidate for `SAPEXEDB` file in `dry_run` mode if previous attempt failed and `sap_software_download_upgrade_relationships` is set to `true`. Uses search query based on version details of `SAPEXE`.
   - If upgrade candidate was found, update software list with new file name.
   - Fail if file is not found.
10. Show summary of validation and fail if validation has failed.


**File name versioning breakdown**
| File name  | Patch | File ID |
| --- | --- | --- |
| SAPEXE_1500-70000596.SAR | 1500 | 70000596 |
| SAPEXEDB_1500-70000612.SAR | 1500 | 70000612 |

> **NOTES:**<br>
> - SAP Kernel files do not contain identifier of version in file name, only Patch.<br>
> - Actual SAP Kernel version is part of unique File ID and inside of archive. It's validation is not handled by this role.<br>

<!-- END Further Information -->

## License
<!-- BEGIN License -->
Apache 2.0
<!-- END License -->

## Maintainers
<!-- BEGIN Maintainers -->
- [Marcel Mamula](https://github.com/marcelmamula)
<!-- END Maintainers -->

## Role Variables
<!-- BEGIN Role Variables -->
### sap_software_download_suser_id
- _Type:_ `string`<br>

The SAP S-User ID with download authorization for SAP software.<br>

### sap_software_download_suser_password
- _Type:_ `string`<br>

The password for the SAP S-User specified in `sap_software_download_suser_id`.<br>

### sap_software_download_directory
- _Type:_ `string`<br>

The directory where downloaded SAP software files will be stored.<br>

### sap_software_download_files
- _Type:_ `list` with elements of type `string`<br>

A list of SAP software file names to download.<br>

### sap_software_download_mp_transaction
- _Type:_ `string`<br>

The name or display ID of a transaction from the SAP Maintenance Planner.<br>
If provided, the role will download all files associated with this Maintenance Plan transaction.<br>

### sap_software_download_mp_stack_xml
- _Type:_ `boolean`<br>
- _Default:_ `true`<br>

Enables download of Maintenance Plan Stack XML file together with files.<br>
If set to `false`, Stack XML file will not be downloaded.<br>


### sap_software_download_find_alternatives
- _Type:_ `boolean`<br>
- _Default:_ `true`<br>

Enables searching for alternative files if the requested file is not found.<br>
Only applies to files specified in `sap_software_download_files`, not Maintenance Plan files.<br>
If set to `false`, the role will not search for alternatives.<br>
Example: File `IMDB_SERVER20_067_4-80002046.SAR` searches for `IMDB_SERVER20_067`<br>

### sap_software_download_find_upgrades
- _Type:_ `boolean`<br>
- _Default:_ `false`<br>

Enables broader searching for alternative files if the requested file is not found.<br>
Only applies to files specified in `sap_software_download_files`, not Maintenance Plan files.<br>
Only applies when file was not found with `sap_software_download_find_alternatives` set to `true`.<br>
If set to `false`, the role will not search for upgrade candidates.<br>
Example: File `IMDB_SERVER20_067_4-80002046.SAR` searches for `IMDB_SERVER20_067`, `IMDB_SERVER20_068`, `IMDB_SERVER20_`<br>

> **NOTE:** Important for when SAP releases new patch for SAP HANA Revision, because:
> - Previous patch of `IMDB_SERVER` will be removed and only new patch will be available to download.
> - Previous patch for other components like `IMDB_AFL` will remain available to download as well as new patch. 

### sap_software_download_ignore_file_not_found
- _Type:_ `bool`<br>
- _Default:_ `false`<br>

Determines whether to ignore errors when a requested file is not found.<br>
If set to `true`, the role will continue execution and download other files, even if some files are not found.<br>
If set to `false`, the role will fail if any requested file is not found.<br>

### sap_software_download_ignore_plan_not_found
- _Type:_ `bool`<br>
- _Default:_ `false`<br>

Determines whether to ignore errors when a specified Maintenance Plan transaction is not found.<br>
If set to `true` and a Maintenance Plan is not found, the role will continue execution, downloading any files specified in `sap_software_download_files`.<br>
If set to `false`, the role will fail if the specified Maintenance Plan is not found.<br>


### sap_software_download_validate_relationships
- _Type:_ `bool`<br>
- _Default:_ `true`<br>

Enables validation of relationships between known combinations of SAP files.<br>
Only applies to files specified in `sap_software_download_files`, not Maintenance Plan files.<br>
If set to `false`, no relationship validation will be performed.<br>
See [Explanation of relationship validation logic](#explanation-of-relationship-validation-logic) for more information.<br>

### sap_software_download_upgrade_relationships
- _Type:_ `bool`<br>
- _Default:_ `false`<br>

Enables automatic upgrade of related known combinations of SAP files when leading component version changes.<br>
Only applies when `sap_software_download_validate_relationships` is set to `true`.<br>
If set to `false`, no search for upgrade candidates before validation will be performed.<br>
See [Explanation of relationship validation logic](#explanation-of-relationship-validation-logic) for more information.<br>

> **NOTE:** Important for when SAP releases new patch for SAP HANA Revision, because:
> - Previous patch of `IMDB_SERVER` will be removed and only new patch will be available to download.
> - Previous patch for other components like `IMDB_AFL` will remain available to download as well as new patch. 

### sap_software_download_ignore_relationship_warning
- _Type:_ `bool`<br>
- _Default:_ `false`<br>

Determines whether to ignore warnings during file relationship validation.<br>
If set to `true`, the role will continue execution even if there are warnings during the validation of file relationships.<br>
If set to `false`, the role will fail if any warnings are encountered during file relationship validation.<br>

### sap_software_download_ignore_validate_credentials
- _Type:_ `bool`<br>
- _Default:_ `false`<br>

Determines whether to ignore validate credentials task.<br>
Disabling this check can lead to locked account, if password is incorrect.<br>
If set to `true`, the role will continue execution without validating S-User credentials.<br>
If set to `false`, the role will execute dry run to validate S-User credentials.<br>

### sap_software_download_deduplicate
- _Type:_ `string`<br>
- _Default:_ `last`<br>

Specifies how to handle duplicate file results when using `sap_software_download_files`.<br>
If multiple files with the same name are found, this setting determines which one to download.<br>

- `first`: Download the first file found<br>
- `last`: Download the last file found.<br>
- `''`: No deduplication, will cause an error if multiple files with the same name are found.<br>
        Can be used to find list of all available files without downloading them.<br>

### sap_software_download_validate_checksum
- _Type:_ `bool`<br>
- _Default:_ `false`<br>

Enables checksum validation of existing files present in `sap_software_download_directory`.<br>
This does not affect automatic checksum validation of downloaded files.<br>


### sap_software_download_use_venv
- _Type:_ `boolean`<br>
- _Default:_ `true`<br>

Determines whether to execute the role within a Python virtual environment.<br>
Using a virtual environment is strongly recommended to isolate dependencies.<br>
If set to `false`, the role will install Python dependencies directly into the system's Python environment.<br>

### sap_software_download_python_interpreter
- _Type:_ `string`<br>
- _Default:_ **Determined by the supported operating system.**<br>

The Python interpreter executable to use when creating a Python virtual environment.<br>
**Mandatory** when the variable `sap_software_download_use_venv` is `true`.<br>
This is the name of the Python executable (e.g., `python3.11`, `python3.9`), which may differ from the Python package name.<br>
The default value is determined by the operating system and is set in the corresponding OS-specific variables file.<br>
Examples: `python3.11` (SLES 15 SP7), `python3.9` (RHEL 8)<br>

### sap_software_download_python_package
- _Type:_ `string`<br>
- _Default:_ **Determined by the supported operating system.**<br>

The name of the OS package that provides the desired Python version.<br>
The Python version provided by this package must match the version specified by `sap_software_download_python_interpreter`.<br>
The default value is determined by the operating system and is set in the corresponding OS-specific variables file.<br>
Examples: `python311` (SLES 15 SP7), `python3.9` (RHEL 8)<br>

### sap_software_download_python_module_packages
- _Type:_ `list` with elements of type `string`<br>
- _Default:_ **Determined by the supported operating system.**<br>

The list of the OS packages that provide modules for the desired Python version.<br>
Required modules are `wheel`, `urllib3`, `requests`, `beautifulsoup4`, `lxml`<br>
The listed package versions must match the Python version specified by `sap_software_download_python_interpreter`.<br>
The default value is determined by the operating system and is set in the corresponding OS-specific variables file.<br>
Examples:<br>
- `['python311-wheel', 'python311-urllib3', 'python311-requests', 'python311-beautifulsoup4', 'python311-lxml']` (SLES 15 SP7)<br>
- `['python3.9-wheel', 'python3.9-urllib3', 'python3.9-requests', 'python3.9-beautifulsoup4', 'python3.9-lxml']` (RHEL 8)<br>
<!-- END Role Variables -->
