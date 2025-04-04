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
    *   **Alternative File Search:** If `sap_software_download_find_alternatives` is `true`, the role will search for alternative files if the requested files are not found.
    *   More information about validation logic is available at [Explanation of relationship validation logic](#explanation-of-relationship-validation-logic)
6.  **Maintenance Plan File Download:** If `sap_software_download_mp_transaction` is provided, the role downloads the files associated with the Maintenance Plan.
7.  **Direct File Download:** If `sap_software_download_files` is provided, the role downloads the specified files.
8.  **Virtual Environment Cleanup:** If a temporary Python virtual environment was used, it is removed.

<!-- END Execution Flow -->

### Example
<!-- BEGIN Execution Example -->
Download of SAP Software files using input list
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
        sap_software_download_files:
          - 'SAPCAR_1115-70006178.EXE'
          - 'SAPEXE_100-80005509.SAR'
```

Download of SAP Software files using Maintenance Plan
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
        sap_software_download_mp_transaction: 'Transaction Name or Display ID from Maintenance Planner'
```

Combined download of SAP Software files and Maintenance Plan transaction together with settings:
- Use default Python instead of Python virtual environment
- No validation of S-User credentials
- No validation of relationships
- No warnings for unavailable files
- No warnings for unavailable Maintenance Plan transaction
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
        sap_software_download_deduplicate: first
        sap_software_download_files:
          - 'SAPCAR_1115-70006178.EXE'
          - 'SAPEXE_100-80005509.SAR'
        sap_software_download_mp_transaction: 'Transaction Name or Display ID from Maintenance Planner'
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
Validation is executed for known combinations of files, where we can validate their name and version.<br>
Example for SAP HANA Database Server 2.0 with LCAPPS and AFL.<br>

1. All files are examined, and a file starting with `IMDB_SERVER2` is found: `IMDB_SERVER20_084_0-80002031.SAR (Revision 2.00.084.0 (SPS08))`. This indicates a SAP HANA 2.0 database server file.
2. The HANA version and revision are extracted from the file name: `HANA 2.0`, `Version 084`.
3. Validation for HANA 1.0 is skipped because it expects files starting with `IMDB_SERVER1`. The following steps are only for `IMDB_SERVER2` (HANA 2.0).
4. All files are examined for files starting with `IMDB_LCAPPS_2` (indicating LCAPPS for HANA 2.0). Then the list is filtered to only include files starting with `IMDB_LCAPPS_2084` (indicating LCAPPS for HANA 2.0 revision 084).
5. Validation will have two outcomes:
   - A file like `IMDB_LCAPPS_2084_0-20010426.SAR` is present. In this case, validation will pass because the LCAPPS version is compatible with the HANA revision.
   - No file starting with `IMDB_LCAPPS_2084` is present, but there are files starting with `IMDB_LCAPPS_2`.<br>
     This indicates a mismatch because the LCAPPS version is not compatible with the specific HANA revision (084) found in step 2.<br>
     In this case, validation will fail. This can be ignored by setting `sap_software_download_ignore_relationship_warning` to `true`.
6. All files are examined for files starting with `IMDB_AFL20` (indicating AFL for HANA 2.0). Then the list is filtered to only include files starting with `IMDB_AFL20_084` (indicating AFL for HANA 2.0 revision 084).
7. Validation will have two outcomes:
   - A file like `IMDB_AFL20_084_1-80001894.SAR` is present. In this case, validation will pass because the AFL version is compatible with the HANA revision.
   - No file starting with `IMDB_AFL20_084` is present, but there are files starting with `IMDB_AFL20`.<br>
     This indicates a mismatch because the AFL version is not compatible with the specific HANA revision (084) found in step 2.<br>
     In this case, validation will fail. This can be ignored by setting `sap_software_download_ignore_relationship_warning` to `true`.

This validation example checks major and minor release (SPS and Revision), but it does not validate patch version.
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
### sap_software_download_python_interpreter
- _Type:_ `string`<br>
- _Default:_ **Determined by the operating system.**<br>

The Python interpreter executable to use when creating a Python virtual environment.<br>
**Mandatory** when `sap_software_download_use_venv` is `true`.<br>
This is the name of the Python executable (e.g., `python3.11`, `python3.9`), which may differ from the Python package name.<br>
The default value is determined by the operating system and is set in the corresponding OS-specific variables file.<br>
Examples: `python3.11` (SUSE), `python3.9` (Red Hat)<br>

### sap_software_download_python_package
- _Type:_ `string`<br>
- _Default:_ **Determined by the operating system.**<br>

The name of the OS package that provides the desired Python version.<br>
The Python version provided by this package must match the version specified by `sap_software_download_python_interpreter`.<br>
The default value is determined by the operating system and is set in the corresponding OS-specific variables file.<br>
Examples: `python311` (SUSE), `python3.9` (Red Hat)<br>

### sap_software_download_python_module_packages
- _Type:_ `list` with elements of type `string`<br>
- _Default:_ **Determined by the operating system.**<br>

The list of the OS packages that provide modules for the desired Python version.<br>
Required modules are wheel, urllib3, requests, beautifulsoup4, lxml<br>
The listed package versions must match the Python version specified by `sap_software_download_python_interpreter`.<br>
The default value is determined by the operating system and is set in the corresponding OS-specific variables file.<br>
Examples:<br>
- `['python311-wheel', 'python311-urllib3', 'python311-requests', 'python311-beautifulsoup4', 'python311-lxml']` (SUSE)<br>
- `['python3.9-wheel', 'python3.9-urllib3', 'python3.9-requests', 'python3.9-beautifulsoup4', 'python3.9-lxml']` (Red Hat)<br>

### sap_software_download_use_venv
- _Type:_ `boolean`<br>
- _Default:_ `true`<br>

Determines whether to execute the role within a Python virtual environment.<br>
Using a virtual environment is strongly recommended to isolate dependencies.<br>
If set to `false`, the role will install Python dependencies directly into the system's Python environment.<br>

### sap_software_download_suser_id
- _Type:_ `string`<br>

The SAP S-User ID with download authorization for SAP software.<br>

### sap_software_download_suser_password
- _Type:_ `string`<br>

The password for the SAP S-User specified in `sap_software_download_suser_id`.<br>

### sap_software_download_files
- _Type:_ `list` with elements of type `string`<br>

A list of SAP software file names to download.<br>

### sap_software_download_mp_transaction
- _Type:_ `string`<br>

The name or display ID of a transaction from the SAP Maintenance Planner.<br>
If provided, the role will download all files associated with this Maintenance Plan transaction.<br>

### sap_software_download_find_alternatives
- _Type:_ `boolean`<br>
- _Default:_ `true`<br>

Enables searching for alternative files if the requested file is not found.<br>
Only applies to files specified in `sap_software_download_files`.<br>
If set to `false`, the role will not search for alternatives.<br>

### sap_software_download_directory
- _Type:_ `string`<br>

The directory where downloaded SAP software files will be stored.<br>

### sap_software_download_validate_relationships
- _Type:_ `bool`<br>
- _Default:_ `true`<br>

Enables validation of relationships between SAP software files.<br>
Only applies to files specified in `sap_software_download_files`.<br>
If set to `false`, no relationship validation will be performed.<br>
Example: Verify version of IMDB_LCAPPS against IMDB_SERVER if IMDB_SERVER was found.<br>

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

Specifies how to handle duplicate file results when using `sap_software_download_files`.<br>
If multiple files with the same name are found, this setting determines which one to download.<br>
- `first`: Download the first file found<br>
- `last`: Download the last file found.<br>
<!-- END Role Variables -->
