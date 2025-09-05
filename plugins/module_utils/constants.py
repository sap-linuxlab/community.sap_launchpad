# SAP Launchpad & Software Center URLs
URL_LAUNCHPAD = 'https://launchpad.support.sap.com'
URL_SOFTWARE_CENTER_SERVICE = 'https://launchpad.support.sap.com/services/odata/svt/swdcuisrv'
URL_SOFTWARE_CENTER_VERSION = 'https://launchpad.support.sap.com/applications/softwarecenter/version.json'
URL_SOFTWARE_CATALOG = 'https://launchpad.support.sap.com/applications/softwarecenter/~{v}~/model/ProductView.json'
URL_ACCOUNT_ATTRIBUTES = 'https://launchpad.support.sap.com/services/account/attributes'
URL_SERVICE_INCIDENT = 'https://launchpad.support.sap.com/services/odata/incidentws'
URL_SERVICE_USER_ADMIN = 'https://launchpad.support.sap.com/services/odata/useradminsrv'
URL_SOFTWARE_DOWNLOAD = 'https://softwaredownloads.sap.com'

# Maintenance Planner URLs
URL_MAINTENANCE_PLANNER = 'https://maintenanceplanner.cfapps.eu10.hana.ondemand.com'
URL_SYSTEMS_PROVISIONING = 'https://launchpad.support.sap.com/services/odata/i7p/odata/bkey'
URL_USERAPPS = 'https://userapps.support.sap.com/sap/support/mp/index.html'
URL_USERAPP_MP_SERVICE = 'https://userapps.support.sap.com/sap/support/mnp/services'
URL_LEGACY_MP_API = 'https://tech.support.sap.com/sap/support/mnp/services'

# Gigya Authentication URLs
# These URLs are part of the SAP Universal ID (Gigya) authentication flow.
URL_ACCOUNT = 'https://accounts.sap.com'
URL_ACCOUNT_CORE_API = 'https://core-api.account.sap.com/uid-core'
URL_ACCOUNT_CDC_API = 'https://cdc-api.account.sap.com'
URL_ACCOUNT_SSO_IDP = 'https://cdc-api.account.sap.com/saml/v2.0/{k}/idp/sso/continue'
URL_ACCOUNT_SAML_PROXY = 'https://account.sap.com/core/SAMLProxyPage.html'
URL_SUPPORT_PORTAL = 'https://hana.ondemand.com/supportportal'

# HTTP Headers & User Agents
USER_AGENT_CHROME = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) '
                     'AppleWebKit/537.36 (KHTML, like Gecko) '
                     'Chrome/72.0.3626.109 Safari/537.36')

# Common headers sent with most requests to mimic a browser.
COMMON_HEADERS = {'User-Agent': USER_AGENT_CHROME}

# Specific headers required for Gigya API requests.
GIGYA_HEADERS = {
    'User-Agent': USER_AGENT_CHROME,
    'Origin': URL_ACCOUNT,
    'Referer': URL_ACCOUNT,
    'Accept': '*/*',
}

# General Configuration
# The maximum number of times to retry a failed network request.
MAX_RETRY_TIMES = 3
