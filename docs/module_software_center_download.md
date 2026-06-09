# software_center_download Ansible Module

## Description
The Ansible Module `software_center_download` automates downloading files from the SAP Software Center.
- It can find a file using a search query or download it directly using a specific download link and filename.
- Supports wildcard search to find and download specific versions (oldest/newest) from multiple available versions.
- If a file is not found via search, it can look for alternative versions.
- It supports checksum validation to ensure file integrity and avoid re-downloading valid files.
- The module can also perform a dry run to check for file availability without downloading.

## Dependencies
This module requires the following Python modules to be installed on the target node (the machine where SAP software will be downloaded):

- wheel
- urllib3
- requests
- beautifulsoup4
- lxml

## Execution

### Wildcard Search Format
The module supports wildcard search to find files across multiple versions. This is useful when you want to download the latest (or oldest) version of a software package without knowing the exact version number.

**Format:** `PREFIX*-ID.EXT`

Where:

- `PREFIX`: The software name prefix (e.g., `SAPEXE`, `SAPHOSTAGENT`).
- `*`: Single wildcard representing the version number.
- `-`: Dash separator (required).
- `ID`: File ID number (e.g., `80002630`).
- `.EXT`: File extension (e.g., `.SAR`, `.EXE`).

> **NOTE:** File ID is unique number that represents combination of component and platform version. 

**Requirements:**
- The parameter `search_alternatives: true` must be enabled.
- Only one wildcard (`*`) is allowed per query.
- File format must include both dash and extension according to pattern above.
- Use `deduplicate` parameter to select oldest (`first`) or newest (`last`) version.

**Examples:**
- `SWPM20SP2*-80003424.SAR` - Matches all available SWPM20 versions starting with `2` (SWPM20SP23, SWPM20SP24, etc.) for `Linux on x86_64 64bit` (80003424).
- `SAPEXE_10*-80002630.SAR` - Matches all available SAPEXE_10 versions starting with `10` (SAPEXE_10, SAPEXE_100, SAPEXE_1000, etc.) for `Linux on Power LE 64bit` (80002630).
- `SAPHOSTAGENT*-80004822.SAR` - Matches all available SAPHOSTAGENT versions for `Linux on x86_64 64bit` (80004822).

**Special Files:**
Some SAP media files don't follow the standard naming pattern and require exact filenames:

- `S4CORE107_INST_EXPORT_1.zip`
- `KD75783.SAR`
- `19118000000000009032` (SAP Media downloaded with ID instead of Title).

### Execution Flow
The module follows a sophisticated logic flow to determine whether to download, skip, or fail. Here is a simplified breakdown of the decision-making process:

1.  **Parameter Validation**:
    *   The module first ensures that either a `search_query` or both `download_link` and `download_filename` are provided. If not, it fails.

2.  **Pre-flight File Check** (if `validate_checksum: false`):
    *   Checks if a file with the exact name already exists at the destination.
        *   **If yes:** The module skips the download and exits.
    *   Checks for files with a similar base name (e.g., `FILE.*` for `FILE.SAR`).
        *   **If yes:** The module skips the download and exits.

3.  **Authentication**:
    *   The module authenticates with the provided S-User credentials to establish a valid session.

4.  **Pre-flight Checksum Validation** (only if `validate_checksum: true` and a local file already exists):
    *   The module attempts to find the corresponding remote file on the SAP portal to get its checksum.
        *   If `search_alternatives: true`, it will look for newer versions if the original is not found.
    *   It compares the local file's checksum with the remote file's checksum (ETag).
        *   **If an alternative file was found:** The local file is considered outdated and is removed to allow the new version to be downloaded.
        *   **If checksums do not match:** The local file is invalid and is removed to allow a fresh download.
        *   **If checksums match (and no alternative was found):** The module skips the download.
        *   **If checksum cannot be validated (e.g., remote file not found):** The module skips the download with a warning.

5.  **File Search**:
    *   **If using `search_query`:**
        *   The module searches for the file. If `search_alternatives: true`, it will look for newer versions if the original is not found.
        *   If an alternative is found and it already exists locally, its checksum is validated as described in the pre-flight check.
    *   **If using `download_link`:**
        *   The module proceeds directly to the download step.

6.  **Download & Post-Download Validation**:
    *   The module verifies that the final download link is active.
    *   **If `dry_run: true`:** The module exits with a success message indicating the file is available, without downloading.
    *   **If `dry_run: false`:** The module streams the file to the destination directory.
    *   **After every download**, the module automatically validates the downloaded file's checksum against the one provided by the server. If they don't match, it will delete the corrupt file and retry the download.

### Example
> **NOTE:** The Python versions in these examples vary by operating system. Always use the version that is compatible with your specific system or managed node.</br>
> To simplify this process, the Ansible Role `sap_launchpad.sap_software_download` will install the correct Python version and required modules for you.</br>

Download SAP Software file
```yaml
---
- name: Example play for Ansible Module software_center_download
  hosts: all
  tasks:
    - name: Download SAP Software file using search_query
      community.sap_launchpad.software_center_download:
        suser_id: "Enter SAP S-User ID"
        suser_password: "Enter SAP S-User Password"
        search_query: "Enter SAP Software file name"
        dest: "Enter download path (e.g. /software)"
```

Download SAP Software file using download_link and download_filename
```yaml
---
- name: Example play for Ansible Module software_center_download
  hosts: all
  tasks:
    - name: Download SAP Software file using download_link and download_filename
      community.sap_launchpad.software_center_download:
        suser_id: "Enter SAP S-User ID"
        suser_password: "Enter SAP S-User Password"
        download_link: 'https://softwaredownloads.sap.com/file/0010000000048502015'
        download_filename: 'IW_FNDGC100.SAR'
        dest: "Enter download path (e.g. /software)"
```

Download latest version of SAP Software using wildcard search
```yaml
---
- name: Example play for Ansible Module software_center_download
  hosts: all
  tasks:
    - name: Download latest SAPEXE version using wildcard
      community.sap_launchpad.software_center_download:
        suser_id: "Enter SAP S-User ID"
        suser_password: "Enter SAP S-User Password"
        search_query: "SAPEXE*-80002630.SAR"
        dest: "Enter download path (e.g. /software)"
        search_alternatives: true
        deduplicate: "last"
    
    - name: Download oldest SAPHOSTAGENT version using wildcard
      community.sap_launchpad.software_center_download:
        suser_id: "Enter SAP S-User ID"
        suser_password: "Enter SAP S-User Password"
        search_query: "SAPHOSTAGENT*-80004822.SAR"
        dest: "Enter download path (e.g. /software)"
        search_alternatives: true
        deduplicate: "first"
```

Download list of SAP Software files, but search for alternatives if not found
```yaml
---
- name: Example play for Ansible Module software_center_download
  hosts: all
  tasks:
    - name: Download list of SAP Software files
      community.sap_launchpad.software_center_download:
        suser_id: "Enter SAP S-User ID"
        suser_password: "Enter SAP S-User Password"
        search_query: "{{ item }}"
        dest: "Enter download path (e.g. /software)"
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
---
- name: Example play for Ansible Module software_center_download
  hosts: all
  tasks:
    - name: Download SAP Software file using search_query
      community.sap_launchpad.software_center_download:
        suser_id: "Enter SAP S-User ID"
        suser_password: "Enter SAP S-User Password"
        search_query: "Enter SAP Software file name"
        dest: "Enter download path (e.g. /software)"
      environment:
        PATH: "/tmp/venv:{{ ansible_facts['env'].PATH }}" 
        PYTHONPATH: "/tmp/venv/lib/python3.11/site-packages" 
        VIRTUAL_ENV: "/tmp/venv" 
      vars:
        ansible_python_interpreter: "/tmp/venv/bin/python3.11"
```

Install prerequisites and download SAP Software file using existing System Python.</br>
**NOTE:** Python modules are installed as packages to avoid `externally-managed-environment` error.
```yaml
---
- name: Example play for Ansible Module software_center_download
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

    - name: Download SAP Software file using search_query
      community.sap_launchpad.software_center_download:
        suser_id: "Enter SAP S-User ID"
        suser_password: "Enter SAP S-User Password"
        search_query: "Enter SAP Software file name"
        dest: "Enter download path (e.g. /software)"
```

Install prerequisites and download SAP Software file using existing Python Virtual Environment `/tmp/python_venv`.
```yaml
---
- name: Example play for Ansible Module software_center_download
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

    - name: Download SAP Software file using search_query
      community.sap_launchpad.software_center_download:
        suser_id: "Enter SAP S-User ID"
        suser_password: "Enter SAP S-User Password"
        search_query: "Enter SAP Software file name"
        dest: "Enter download path (e.g. /software)"
      environment:
        PATH: "/tmp/python_venv:{{ ansible_facts['env'].PATH }}" 
        PYTHONPATH: "/tmp/python_venv/lib/python3.11/site-packages" 
        VIRTUAL_ENV: "/tmp/python_venv" 
      vars:
        ansible_python_interpreter: "/tmp/python_venv/bin/python3.11"
```

### Output format
#### msg
- _Type:_ `string`<br>

A message indicating the status of the download operation.

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

The SAP software file name to download.<br>
Supports wildcard format for version matching when `search_alternatives` is enabled.<br>

**Wildcard Format:** `PREFIX*-ID.EXT`<br>
- Only one wildcard (`*`) is allowed per query<br>
- Example: `SAPEXE*-80002630.SAR` matches all SAPEXE versions<br>

**Exact Filename:** Use the complete filename without wildcards for specific files.<br>
- Example: `SAPCAR_1324-80000936.EXE`

### download_link
- _Type:_ `string`<br>

Direct download link to the SAP software.</br>
Download links can be obtained from SAP Software Center or using module `module_maintenance_planner_files`.

### download_filename
- _Type:_ `string`<br>

Download filename of the SAP software.</br>
Download names can be obtained from SAP Software Center or using module `module_maintenance_planner_files`.

### dest
- _Required:_ `true`<br>
- _Type:_ `string`<br>

The directory where downloaded SAP software files will be stored.

### deduplicate
- _Type:_ `string`<br>
- _Choices:_ `first`, `last`, `` (empty)<br>
- _Default:_ `last`<br>

Specifies how to handle multiple search results.<br>
Only applies when `search_alternatives` is enabled and multiple versions are found.<br>

**Options:**<br>
- `first`: Download the oldest version<br>
- `last`: Download the newest version<br>
- `` (empty): If multiple results are found, display all available versions and fail with an error<br>

Files are sorted numerically by version number, ensuring correct ordering (e.g., version 7 < 10 < 100 < 1500).<br>

### search_alternatives
- _Type:_ `boolean`<br>
- _Default:_ `false`<br>

Enables searching for alternative files if the requested file is not found.<br>
**Required** when using wildcard queries in `search_query`.<br>

**Requirements:**<br>
- Only works for files following the format `PREFIX-ID.EXT` (with dash and extension)<br>
- Special media files without this pattern (e.g., `S4CORE107_INST_EXPORT_1.zip`) must use exact filenames<br>
- Wildcard searches are not supported for files without dashes or extensions<br>

### dry_run
- _Type:_ `boolean

Check availability of SAP Software without downloading.<br>

### validate_checksum
- _Type:_ `boolean

If a file with the same name already exists at the destination, validate its checksum against the remote file.<br>
If the checksum is invalid, the local file will be removed and re-downloaded.<br>
