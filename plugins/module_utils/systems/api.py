import json
import time
from functools import wraps

from urllib.parse import urljoin

from .. import constants as C
from .. import exceptions


class InstallationNotFoundError(Exception):
    def __init__(self, installation_nr, available_installations):
        self.installation_nr = installation_nr
        self.available_installations = available_installations
        super(InstallationNotFoundError, self).__init__(
            "Installation number '{0}' not found. Available installations: {1}".format(installation_nr, available_installations)
        )


class SystemNotFoundError(Exception):
    def __init__(self, system_nr, details):
        self.system_nr = system_nr
        self.details = details
        super(SystemNotFoundError, self).__init__("System with number '{0}' not found. Details: {1}".format(system_nr, details))


class ProductNotFoundError(Exception):
    def __init__(self, product, available_products):
        self.product = product
        self.available_products = available_products
        super(ProductNotFoundError, self).__init__("Product '{0}' not found. Available products: {1}".format(product, available_products))


class VersionNotFoundError(Exception):
    def __init__(self, version, available_versions):
        self.version = version
        self.available_versions = available_versions
        super(VersionNotFoundError, self).__init__("Version '{0}' not found. Available versions: {1}".format(version, available_versions))


class LicenseTypeInvalidError(Exception):
    def __init__(self, license_type, available_license_types):
        self.license_type = license_type
        self.available_license_types = available_license_types
        super(LicenseTypeInvalidError, self).__init__("License type '{0}' is invalid. Available types: {1}".format(license_type, available_license_types))


class DataInvalidError(Exception):
    def __init__(self, scope, unknown_fields, missing_required_fields, fields_with_invalid_option):
        self.scope = scope
        self.unknown_fields = unknown_fields
        self.missing_required_fields = missing_required_fields
        self.fields_with_invalid_option = fields_with_invalid_option
        message = ("Invalid data for {0}: Unknown fields: {1}, Missing required fields: {2}, "
                   "Invalid options: {3}".format(scope, unknown_fields, missing_required_fields,
                                                 fields_with_invalid_option))
        super(DataInvalidError, self).__init__(message)


try:
    from requests.exceptions import HTTPError
except ImportError:
    HAS_REQUESTS = False
    HTTPError = None
else:
    HAS_REQUESTS = True


def require_requests(func):
    # A decorator to check for the 'requests' library before executing a function.
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not HAS_REQUESTS:
            raise ImportError("The 'requests' library is required but was not found.")
        return func(*args, **kwargs)
    return wrapper


@require_requests
def get_systems(client, filter_str):
    # Retrieves a list of systems based on an OData filter string.
    query_path = "Systems?$filter={0}".format(filter_str)
    return client.get(_url(query_path), headers=_headers({})).json()['d']['results']


@require_requests
def get_system(client, system_nr, installation_nr, username):
    # Retrieves details for a single, specific system.
    filter_str = "Uname eq '{0}' and Insnr eq '{1}' and Sysnr eq '{2}'".format(username, installation_nr, system_nr)
    try:
        systems = get_systems(client, filter_str)
    except HTTPError as err:
        # In case the system is not found, the backend doesn't return an empty result set or a 404, but a 400.
        # To make the error checking here as resilient as possible, just consider an error 400 as an invalid user error and return it to the user.
        if err.response.status_code == 400:
            raise SystemNotFoundError(system_nr, err.response.content)
        else:
            raise err

    if len(systems) == 0:
        raise SystemNotFoundError(system_nr, "no systems returned by API")

    system = systems[0]
    if 'Prodver' not in system and 'Version' not in system:
        message = ("System {0} was found, but it is missing a required Product Version ID "
                   "(checked for 'Prodver' and 'Version' keys). System details: {1}".format(system_nr, system))
        raise exceptions.SapLaunchpadError(message)

    return system


@require_requests
def get_product_id(client, product_name, installation_nr, username):
    # Finds the internal product ID for a given product name.
    query_path = "SysProducts?$filter=Uname eq '{0}' and Insnr eq '{1}' and Sysnr eq '' and Nocheck eq ''".format(username, installation_nr)
    products = client.get(_url(query_path), headers=_headers({})).json()['d']['results']
    product = next((p for p in products if p['Description'] == product_name), None)
    if product is None:
        raise ProductNotFoundError(product_name, [p['Description'] for p in products])
    return product['Product']


@require_requests
def get_version_id(client, version_name, product_id, installation_nr, username):
    # Finds the internal version ID for a given product version name.
    query_path = "SysVersions?$filter=Uname eq '{0}' and Insnr eq '{1}' and Product eq '{2}' and Nocheck eq ''".format(username, installation_nr, product_id)
    versions = client.get(_url(query_path), headers=_headers({})).json()['d']['results']
    version = next((v for v in versions if v['Description'] == version_name), None)
    if version is None:
        raise VersionNotFoundError(version_name, [v['Description'] for v in versions])
    return version['Version']


@require_requests
def validate_installation(client, installation_nr, username):
    # Checks if the user has access to the specified installation number.
    query_path = "Installations?$filter=Ubname eq '{0}' and ValidateOnly eq ''".format(username)
    installations = client.get(_url(query_path), headers=_headers({})).json()['d']['results']
    if not any(i['Insnr'] == installation_nr for i in installations):
        raise InstallationNotFoundError(installation_nr, [i['Insnr'] for i in installations])


@require_requests
def validate_system_data(client, data, version_id, system_nr, installation_nr, username):
    # Validates user-provided system data against the fields supported by the API for a given product version.
    query_path = "SystData?$filter=Pvnr eq '{0}' and Insnr eq '{1}'".format(version_id, installation_nr)
    results = client.get(_url(query_path), headers=_headers({})).json()['d']['results'][0]
    possible_fields = json.loads(results['Output'])
    final_fields = _validate_user_data_against_supported_fields("system", data, possible_fields)

    final_fields['Version'] = version_id
    final_fields['Insnr'] = installation_nr
    final_fields['Uname'] = username
    final_fields['Sysnr'] = system_nr
    final_fields_for_check = [{"name": k, "value": v} for k, v in final_fields.items()]
    query_path = "SystemDataCheck?$filter=Nocheck eq '' and Data eq '{0}'".format(json.dumps(final_fields_for_check))
    results = client.get(_url(query_path), headers=_headers({})).json()['d']['results']

    warning = None
    if len(results) > 0:
        warning = json.loads(results[0]['Data'])[0]['VALUE']

    final_fields_lower = [{"name": entry["name"].lower(), "value": entry["value"]} for entry in final_fields_for_check]
    return final_fields_lower, warning


@require_requests
def validate_licenses(client, licenses, version_id, installation_nr, username):
    # Validates user-provided license data against the license types and fields supported by the API.
    query_path = "LicenseType?$filter=PRODUCT eq '{0}' and INSNR eq '{1}' and Uname eq '{2}' and Nocheck eq 'X'".format(version_id, installation_nr, username)
    results = client.get(_url(query_path), headers=_headers({})).json()['d']['results']
    available_license_types = {r["LICENSETYPE"] for r in results}
    license_data = []

    for lic in licenses:
        result = next((r for r in results if r["LICENSETYPE"] == lic['type']), None)
        if result is None:
            raise LicenseTypeInvalidError(lic['type'], available_license_types)

        final_fields = _validate_user_data_against_supported_fields('license {0}'.format(lic["type"]), lic['data'], json.loads(result["Selfields"]))
        final_fields = {k.upper(): v for k, v in final_fields.items()}
        final_fields["LICENSETYPE"] = result['PRODID']
        final_fields["LICENSETYPETEXT"] = result['LICENSETYPE']
        license_data.append(final_fields)
    return license_data


@require_requests
def get_existing_licenses(client, system_nr, username):
    # Retrieves all existing license keys for a given system.
    # When updating the licenses based on the results here, the backend expects a completely different format.
    # This function transforms the response to the format the backend expects for subsequent update calls.
    query_path = "LicenseKeys?$filter=Uname eq '{0}' and Sysnr eq '{1}'".format(username, system_nr)
    results = client.get(_url(query_path), headers=_headers({})).json()['d']['results']
    return [
        {
            "LICENSETYPETEXT": r["LicenseDescr"], "LICENSETYPE": r["Prodid"], "HWKEY": r["Hwkey"],
            "EXPDATE": r["LidatC"], "STATUS": r["Status"], "STATUSCODE": r["StatusCode"],
            "KEYNR": r["Keynr"], "QUANTITY": r["Ulimit"], "QUANTITY_C": r["UlimitC"],
            "MAXEXPDATE": r["MaxLiDat"]
        } for r in results
    ]


@require_requests
def generate_licenses(client, license_data, existing_licenses, version_id, installation_nr, username):
    # Generates new license keys for a system.
    body = {
        "Prodver": version_id, "ActionCode": "add", "ExistingData": json.dumps(existing_licenses),
        "Entry": json.dumps(license_data), "Nocheck": "", "Insnr": installation_nr, "Uname": username
    }
    token = _get_csrf_token(client)
    post_headers = _headers({
        'x-csrf-token': token,
        'X-Requested-With': 'XMLHttpRequest'
    })
    response = client.post(_url("BSHWKEY"), json=body, headers=post_headers).json()
    return json.loads(response['d']['Result'])


@require_requests
def submit_system(client, is_new, system_data, generated_licenses, username):
    # Submits all system and license data to create or update a system.
    # The SAP Backend requires a completely different format for the license data (`matdata`)
    # than what it returns from the GET request, so we map it here.
    body = {
        "actcode": "add" if is_new else "edit", "Uname": username, "sysdata": json.dumps(system_data),
        "matdata": json.dumps([
            {
                "hwkey": lic["HWKEY"], "prodid": lic["LICENSETYPE"], "quantity": lic["QUANTITY"],
                "keynr": lic["KEYNR"], "expdat": lic["EXPDATE"], "status": lic["STATUS"],
                "statusCode": lic["STATUSCODE"],
            } for lic in generated_licenses
        ])
    }
    token = _get_csrf_token(client)
    post_headers = _headers({
        'x-csrf-token': token,
        'X-Requested-With': 'XMLHttpRequest'
    })
    response = client.post(_url("Submit"), json=body, headers=post_headers).json()
    licdata = json.loads(response['d']['licdata'])
    if not licdata:
        raise exceptions.SapLaunchpadError(
            "The API call to submit the system was successful, but the response did not contain the expected system number. " +
            "The 'licdata' field in the API response was empty: {0}".format(response['d']['licdata'])
        )
    return licdata[0]['VALUE']


@require_requests
def get_license_key_numbers(client, license_data, system_nr, username):
    # Retrieves the unique key numbers for a list of recently created licenses.
    key_nrs = []
    for lic in license_data:
        query_path_template = ("LicenseKeys?$filter=Uname eq '{0}' and Sysnr eq '{1}' and "
                               "Prodid eq '{2}' and Hwkey eq '{3}'")
        query_path = query_path_template.format(username, system_nr, lic['LICENSETYPE'], lic['HWKEY'])

        # Retry logic to handle potential replication delay in the backend API after a license is submitted.
        for attempt in range(9):
            results = client.get(_url(query_path), headers=_headers({})).json()['d']['results']
            if results:
                key_nrs.append(results[0]['Keynr'])
                break  # Found it, break the retry loop

            if attempt < 8:  # Don't sleep on the last attempt
                time.sleep(10)  # Wait 10 seconds before retrying
        else:  # This 'else' belongs to the 'for' loop, it runs if the loop completes without a 'break'
            raise exceptions.SapLaunchpadError(
                ("Could not find license key number for license type '{0}' and HW key '{1}' "
                 "on system '{2}' after submitting the changes. There might be a replication delay in the SAP backend.")
                .format(lic['LICENSETYPE'], lic['HWKEY'], system_nr)
            )

    return key_nrs


@require_requests
def download_licenses(client, key_nrs):
    # Downloads the license key file content for a list of key numbers.
    keys_json = json.dumps([{"Keynr": key_nr} for key_nr in key_nrs])
    return client.get(_url("FileContent(Keynr='{0}')/$value".format(keys_json))).content


@require_requests
def delete_licenses(client, licenses_to_delete, existing_licenses, version_id, installation_nr, username):
    # Deletes a list of specified licenses from a system.
    body = {
        "Prodver": version_id, "ActionCode": "delete", "ExistingData": json.dumps(existing_licenses),
        "Entry": json.dumps(licenses_to_delete), "Nocheck": "", "Insnr": installation_nr, "Uname": username
    }
    token = _get_csrf_token(client)
    post_headers = _headers({
        'x-csrf-token': token,
        'X-Requested-With': 'XMLHttpRequest'
    })
    response = client.post(_url("BSHWKEY"), json=body, headers=post_headers).json()
    return json.loads(response['d']['Result'])


def _url(query_path):
    # Helper to construct the full URL for the systems provisioning service.
    return '{0}/{1}'.format(C.URL_SYSTEMS_PROVISIONING, query_path)


def _headers(additional_headers):
    # Helper to construct standard request headers.
    headers = {'Accept': 'application/json'}
    headers.update(additional_headers)
    return headers


@require_requests
def _get_csrf_token(client):
    # Fetches the CSRF token required for POST/write operations.
    # Add Origin and a more specific Referer header, as the service may require them to issue a CSRF token.
    license_key_app_url = urljoin(C.URL_LAUNCHPAD, '/#/licensekey')
    csrf_headers = _headers({
        'x-csrf-token': 'Fetch',
        'Origin': C.URL_LAUNCHPAD,
        'Referer': license_key_app_url
    })
    res = client.get(_url(''), headers=csrf_headers)

    # The CSRF token is primarily expected in the 'x-csrf-token' header.
    token = res.headers.get('x-csrf-token')

    # As a fallback, check if the token was already set in a cookie by a previous
    # request. The cookie name can vary in case.
    if not token:
        cookies = client.get_cookies()
        token = cookies.get('X-CSRF-Token') or cookies.get('x-csrf-token') or cookies.get('__HOST-XSRF_COOKIE')

    if not token:
        raise exceptions.SapLaunchpadError(
            "Failed to retrieve CSRF token. The API did not return the 'x-csrf-token' header or a CSRF cookie."
        )
    return token


def _validate_user_data_against_supported_fields(scope, user_data, possible_fields):
    # A generic helper to validate a dictionary of user data against a list of API-supported fields.
    unknown_fields = {field for field in user_data if not any(field == pf['FIELD'] for pf in possible_fields)}
    missing_required_fields = {}
    fields_with_invalid_option = {}
    final_fields = {}

    for pf in possible_fields:
        user_value = user_data.get(pf["FIELD"])
        if user_value is not None:
            if len(pf["DATA"]) == 0:
                final_fields[pf["FIELD"]] = user_value
            else:
                resolved_value = next((entry["NAME"] for entry in pf["DATA"] if entry['VALUE'] == user_value), None)
                if resolved_value is None:
                    fields_with_invalid_option[pf["FIELD"]] = [d['VALUE'] for d in pf["DATA"]]
                else:
                    final_fields[pf["FIELD"]] = resolved_value
        elif pf['REQUIRED'] == "X":
            missing_required_fields[pf["FIELD"]] = [d['VALUE'] for d in pf["DATA"]]

    if len(unknown_fields) > 0 or len(missing_required_fields) > 0 or len(fields_with_invalid_option) > 0:
        raise DataInvalidError(scope, unknown_fields, missing_required_fields, fields_with_invalid_option)

    return final_fields
