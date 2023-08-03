# FAQ

This FAQ document includes sections:
- [Errors with prefix 'SAP SSO authentication failed - '](#errors-with-prefix-sap-sso-authentication-failed---)
- [Errors with prefix 'An exception has occurred - '](#errors-with-prefix-an-exception-has-occurred---)

<br/>

## Errors with prefix 'SAP SSO authentication failed - '
---

### <samp>'SAP SSO authentication failed - 401 Client Error'</samp>

:white_check_mark: Login to SAP.com was successful
:question: SAP Download authorizations for the SAP User ID

SAP software installation media must be obtained from SAP directly, and requires valid license agreements with SAP in order to access these files.

The error HTTP 401 refers to either:
- Unauthorized, the SAP User ID being used belongs to an SAP Company Number (SCN) with one or more Installation Number/s which do not have license agreements for these files
- Unauthorized, the SAP User ID being used does not have SAP Download authorizations
- Unauthorized, the SAP User ID is part of an SAP Universal ID and must use the password of the SAP Universal ID
  - In addition, if a SAP Universal ID is used then the recommendation is to check and reset the SAP User ID ‘Account Password’ in the [SAP Universal ID Account Manager](https://account.sap.com/manage/accounts), which will help to avoid any potential conflicts.

This is documented under [Execution - Credentials](https://github.com/sap-linuxlab/community.sap_launchpad#requirements-dependencies-and-testing).

### <samp>'SAP SSO authentication failed - 404 Client Error: Not Found for url: `https://origin.softwaredownloads.sap.com/tokengen/?file=___`'</samp>

:white_check_mark: Login to SAP.com was successful
:white_check_mark: SAP Download authorizations for the SAP User ID

SAP has refreshed the installation media (new revisions or patch levels) for the files in your SAP Maintenance Planner stack, and you will need to update / create a new plan to re-generate the up to date files.

### <samp>'SAP SSO authentication failed - 403 Client Error: Forbidden for url: `https://softwaredownloads.sap.com/file/___`'</samp>

:white_check_mark: Login to SAP.com was successful
:question: SAP Download authorizations for the SAP User ID

SAP Software Center is likely experiencing temporary problems, please try again later. The Ansible Collection for SAP Launchpad will always attempt 3 retries if a HTTP 403 error code is received, if after 3 attempts the file is not available then a failure will occur.


## Errors with prefix 'An exception has occurred - '
---

### <samp>'An exception has occurred - You do not have proper authorization to download software, please check: `https://launchpad.support.sap.com/#/user/authorizations`'</samp>

:white_check_mark: Login to SAP.com was successful
:x: SAP Download authorizations for the SAP User ID


### <samp>'An exception has occurred - download link `https://softwaredownloads.sap.com/file/___` is not available'</samp>

:white_check_mark: Login to SAP.com was successful
:white_check_mark: SAP Download authorizations for the SAP User ID

SAP has refreshed the installation media (new revisions or patch levels) for the files in your SAP Maintenance Planner stack, and you will need to update / create a new plan to re-generate the up to date files.

### <samp>'An exception has occurred - no result found for `FILENAME_HERE.SAR`'</samp>

:white_check_mark: Login to SAP.com was successful
:white_check_mark: SAP Download authorizations for the SAP User ID

SAP has refreshed the installation media (new revisions or patch levels), this filename cannot be found and you will need to search for the updated filename (usually an increment, e.g. `_0` to `_1` otherwise the file cannot be downloaded.
