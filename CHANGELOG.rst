===================================
community.sap\_launchpad Release Notes
===================================

.. contents:: Topics

v1.2.0
======

Release Summary
---------------

Enhancements to Modules and introduction of new Ansible Role.

Minor Changes
-------------
- sap_software_download: New Ansible Role with enhanced logic for downloading software using Ansible Module software_center_download (https://github.com/sap-linuxlab/community.sap_launchpad/pull/32)
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
