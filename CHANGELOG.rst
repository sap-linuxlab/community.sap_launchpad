===================================
community.sap\_launchpad Release Notes
===================================

.. contents:: Topics

v1.3.1
======

Release Summary
---------------

Various bug fixes fixing issues identified by new workflows for sanity tests.

Bugfixes
--------
- collection: Add ansible-test sanity workflow and fix sanity errors (https://github.com/sap-linuxlab/community.sap_launchpad/pull/55)


v1.3.0
======

Release Summary
---------------

Refactor Ansible Modules and adjust for ansible-core 2.19.

Minor Changes
-------------
- collection: Refactor all Ansible Modules (https://github.com/sap-linuxlab/community.sap_launchpad/pull/51)
- sap_software_download: Update for ansible-core 2.19 (https://github.com/sap-linuxlab/community.sap_launchpad/pull/49)

Bugfixes
--------
- sap_software_download: Fix for failed checksums not correctly retrying (https://github.com/sap-linuxlab/community.sap_launchpad/pull/50)


v1.2.1
======

Release Summary
---------------

Various bug fixes

Bugfixes
--------
- software_center_download: Improved logic for skipping existing files and getting valid filename (https://github.com/sap-linuxlab/community.sap_launchpad/pull/40)
- sap_software_download: Add SLES 16 python313 support and update changelog (https://github.com/sap-linuxlab/community.sap_launchpad/pull/41)


v1.2.0
======

Release Summary
---------------

Enhancements to Modules and introduction of new Ansible Role.

Minor Changes
-------------
- sap_software_download: New Ansible Role with enhanced logic for downloading software using Ansible Module software_center_download (https://github.com/sap-linuxlab/community.sap_launchpad/pull/32)
- sap_software_download: Download stack XML option (https://github.com/sap-linuxlab/community.sap_launchpad/pull/35)
- software_center_download: Add option to search for latest packages (https://github.com/sap-linuxlab/community.sap_launchpad/pull/28)
- maintenance_planner modules: Add option to use Display ID instead of name (https://github.com/sap-linuxlab/community.sap_launchpad/pull/31)
- Collection Readme update and preparation for 1.2.0 release (https://github.com/sap-linuxlab/community.sap_launchpad/pull/34)

Bugfixes
--------

- fix: cache gigya sdk build number (https://github.com/sap-linuxlab/community.sap_launchpad/pull/33)


v1.1.1
======

Release Summary
---------------

Various bug fixes

Bugfixes
--------
- Append logic for Account Temporarily Locked Out
- Fix errors in the example file


v1.1.0 (2023-11-28)
======

Release Summary
---------------

Community contribution with new Ansible Modules `systems_info` and `license_keys``

Minor Changes
-------------

- Create/update systems and license keys (https://github.com/sap-linuxlab/community.sap_launchpad/pull/16)


v1.0.1 (2023-09-14)
======

Release Summary
---------------

Various bug fixes

Bugfixes
--------

- Fix for handling old password prompt


v1.0.0 (2023-08-22)
======

Release Summary
---------------

Initial Release on Galaxy
