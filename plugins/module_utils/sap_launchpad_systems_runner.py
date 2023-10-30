from . import constants as C
from .sap_api_common import _request
import json

from requests.exceptions import HTTPError


class InstallationNotFoundError(Exception):
    def __init__(self, installation_nr, available_installations):
        self.installation_nr = installation_nr
        self.available_installations = available_installations


def validate_installation(installation_nr, username):
    query_path = f"Installations?$filter=Ubname eq '{username}' and ValidateOnly eq ''"
    installations = _request(_url(query_path), headers=_headers({})).json()['d']['results']
    if not any(installation['Insnr'] == installation_nr for installation in installations):
        raise InstallationNotFoundError(installation_nr, installations)


def get_systems(filter):
    query_path = f"Systems?$filter={filter}"
    return _request(_url(query_path), headers=_headers({})).json()['d']['results']


class SystemNrInvalidError(Exception):
    def __init__(self, system_nr, details):
        self.system_nr = system_nr
        self.details = details


def get_system(system_nr, installation_nr, username):
    query_path = f"Systems?$filter=Uname eq '{username}' and Insnr eq '{installation_nr}' and Sysnr eq '{system_nr}'"

    try:
        systems = _request(_url(query_path), headers=_headers({})).json()['d']['results']
    except HTTPError as err:
        # in case the system is not found, the backend doesn't return an empty result set or a 404, but a 400.
        # to make the error checking here as resilient as possible,
        # just consider an error 400 as an invalid user error and return it to the user.
        if err.response.status_code == 400:
            raise SystemNrInvalidError(system_nr, err.response.content)
        else:
            raise err

    # not sure this case ever happens; catch it nevertheless.
    if len(systems) == 0:
        raise SystemNrInvalidError(system_nr, "no systems returned by API")

    return systems[0]


class ProductNotFoundError(Exception):
    def __init__(self, product, available_products):
        self.product = product
        self.available_products = available_products


def get_product(product_name, installation_nr, username):
    query_path = f"SysProducts?$filter=Uname eq '{username}' and Insnr eq '{installation_nr}' and Sysnr eq '' and Nocheck eq ''"
    products = _request(_url(query_path), headers=_headers({})).json()['d']['results']
    product = next((product for product in products if product['Description'] == product_name), None)
    if product is None:
        raise ProductNotFoundError(product_name, products)

    return product['Product']


class VersionNotFoundError(Exception):
    def __init__(self, version, available_versions):
        self.version = version
        self.available_versions = available_versions


def get_version(version_name, product_id, installation_nr, username):
    query_path = f"SysVersions?$filter=Uname eq '{username}' and Insnr eq '{installation_nr}' and Product eq '{product_id}' and Nocheck eq ''"
    versions = _request(_url(query_path), headers=_headers({})).json()['d']['results']
    version = next((version for version in versions if version['Description'] == version_name), None)
    if version is None:
        raise VersionNotFoundError(version_name, versions)

    return version['Version']


def validate_system_data(data, version_id, system_nr, installation_nr, username):
    query_path = f"SystData?$filter=Pvnr eq '{version_id}' and Insnr eq '{installation_nr}'"
    results = _request(_url(query_path), headers=_headers({})).json()['d']['results'][0]
    possible_fields = json.loads(results['Output'])
    final_fields = _validate_user_data_against_supported_fields("system", data, possible_fields)

    final_fields['Prodver'] = version_id
    final_fields['Insnr'] = installation_nr
    final_fields['Uname'] = username
    final_fields['Sysnr'] = system_nr
    final_fields = [{"name": k, "value": v} for k, v in final_fields.items()]
    query_path = f"SystemDataCheck?$filter=Nocheck eq '' and Data eq '{json.dumps(final_fields)}'"
    results = _request(_url(query_path), headers=_headers({})).json()['d']['results']

    warning = None
    if len(results) > 0:
        warning = json.loads(results[0]['Data'])[0]['VALUE']

    # interestingly, all downstream api calls require the names in lowercase. transform it for further usage.
    final_fields = [{"name": entry["name"].lower(), "value": entry["value"]} for entry in final_fields]
    return final_fields, warning


class LicenseTypeInvalidError(Exception):
    def __init__(self, license_type, available_license_types):
        self.license_type = license_type
        self.available_license_types = available_license_types


def validate_licenses(licenses, version_id, installation_nr, username):
    query_path = f"LicenseType?$filter=PRODUCT eq '{version_id}' and INSNR eq '{installation_nr}' and Uname eq '{username}' and Nocheck eq 'True'"
    results = _request(_url(query_path), headers=_headers({})).json()['d']['results']

    available_license_types = {result["LICENSETYPE"] for result in results}
    license_data = []

    for license in licenses:
        result = next((result for result in results if result["LICENSETYPE"] == license['type']), None)
        if result is None:
            raise LicenseTypeInvalidError(license['type'], available_license_types)

        final_fields = _validate_user_data_against_supported_fields(f'license {license["type"]}', license['data'],
                                                                    json.loads(result["Selfields"]))
        # for some reason, the API wants to have the keys in uppercase, transform it
        final_fields = {k.upper(): v for k, v in final_fields.items()}
        final_fields["LICENSETYPE"] = result['PRODID']
        final_fields["LICENSETYPETEXT"] = result['LICENSETYPE']
        license_data.append(final_fields)

    return license_data


def get_existing_licenses(system_nr, username):
    query_path = f"LicenseKeys?$filter=Uname eq '{username}' and Sysnr eq '{system_nr}'"
    results = _request(_url(query_path), headers=_headers({})).json()['d']['results']
    # for some weird reason that probably only SAP knows, when updating the licenses based on the results here,
    # they expect a completely different format. let's transform to the format the backend expects.
    # this code most likely doesn't work for licenses that have different parameters than S4HANA or SAP HANA
    # (which only use HWKEY, EXPDATE and QUANTITY), as I only tested it with those two license types.
    # feel free to extend (or, even better, come up with a generic way to transform the parameters).
    return [
        {
            "LICENSETYPETEXT": result["LicenseDescr"],
            "LICENSETYPE": result["Prodid"],
            "HWKEY": result["Hwkey"],
            "EXPDATE": result["LidatC"],
            "STATUS": result["Status"],
            "STATUSCODE": result["StatusCode"],
            "KEYNR": result["Keynr"],
            "QUANTITY": result["Ulimit"],
            "QUANTITY_C": result["UlimitC"],
            "MAXEXPDATE": result["MaxLiDat"]
        } for result in results
    ]


def keep_only_new_or_changed_licenses(existing_licenses, license_data):
    new_or_changed_licenses = []
    for license in license_data:
        if not any(license['HWKEY'] == lic['HWKEY'] and license['LICENSETYPE'] == lic['LICENSETYPE'] for lic in
                   existing_licenses):
            new_or_changed_licenses.append(license)

    return new_or_changed_licenses


def generate_licenses(license_data, existing_licenses, version_id, installation_nr, username):
    body = {
        "Prodver": version_id,
        "ActionCode": "add",
        "ExistingData": json.dumps(existing_licenses),
        "Entry": json.dumps(license_data),
        "Nocheck": "",
        "Insnr": installation_nr,
        "Uname": username
    }
    response = _request(_url("BSHWKEY"), json=body, headers=_headers({'x-csrf-token': _get_csrf_token()})).json()
    return json.loads(response['d']['Result'])


def submit_system(is_new, system_data, generated_licenses, username):
    body = {
        "actcode": "add" if is_new else "edit",
        "Uname": username,
        "sysdata": json.dumps(system_data),
        "matdata": json.dumps(
            # again, SAP Backend requires a completely different format than it returned. let's map it.
            # this code most likely doesn't work for licenses that have different parameters than S4HANA or SAP HANA
            # (which only use HWKEY, EXPDATE and QUANTITY), as I only tested it with those two license types.
            # feel free to extend (or, even better, come up with a generic way to transform the parameters).
            [
                {
                    "hwkey": license["HWKEY"],
                    "prodid": license["LICENSETYPE"],
                    "quantity": license["QUANTITY"],
                    "keynr": license["KEYNR"],
                    "expdat": license["EXPDATE"],
                    "status": license["STATUS"],
                    "statusCode": license["STATUSCODE"],
                } for license in generated_licenses
            ]
        )
    }
    response = _request(_url("Submit"), json=body, headers=_headers({'x-csrf-token': _get_csrf_token()})).json()
    return json.loads(response['d']['licdata'])[0]['VALUE']  # contains system number


def get_license_key_numbers(license_data, system_nr, username):
    key_nrs = []
    for license in license_data:
        query_path = f"LicenseKeys?$filter=Uname eq '{username}' and Sysnr eq '{system_nr}' and Prodid eq '{license['LICENSETYPE']}' and Hwkey eq '{license['HWKEY']}'"
        results = _request(_url(query_path), headers=_headers({})).json()['d']['results']
        key_nrs.append(results[0]['Keynr'])

    return key_nrs


def download_licenses(key_nrs):
    keys_json = json.dumps([{"Keynr": key_nr} for key_nr in key_nrs])
    return _request(_url(f"FileContent(Keynr='{keys_json}')/$value")).content


def find_licenses_to_delete(key_nrs_to_keep, existing_licenses):
    return [existing_license for existing_license in existing_licenses if
            not existing_license['KEYNR'] in key_nrs_to_keep]


def delete_licenses(licenses_to_delete, existing_licenses, version_id, installation_nr, username):
    body = {
        "Prodver": version_id,
        "ActionCode": "delete",
        "ExistingData": json.dumps(existing_licenses),
        "Entry": json.dumps(licenses_to_delete),
        "Nocheck": "",
        "Insnr": installation_nr,
        "Uname": username
    }
    response = _request(_url("BSHWKEY"), json=body, headers=_headers({'x-csrf-token': _get_csrf_token()})).json()
    return json.loads(response['d']['Result'])


def _url(query_path):
    return f'{C.URL_SYSTEMS_PROVISIONING}/{query_path}'


def _headers(additional_headers):
    return {**{'Accept': 'application/json'}, **additional_headers}


def _get_csrf_token():
    return _request(C.URL_SYSTEMS_PROVISIONING, headers=_headers({'x-csrf-token': 'Fetch'})).headers['x-csrf-token']


class DataInvalidError(Exception):
    def __init__(self, scope, unknown_fields, missing_required_fields, fields_with_invalid_option):
        self.scope = scope
        self.unknown_fields = unknown_fields
        self.missing_required_fields = missing_required_fields
        self.fields_with_invalid_option = fields_with_invalid_option


def _validate_user_data_against_supported_fields(scope, user_data, possible_fields):
    unknown_fields = {field for field, _ in user_data.items() if
                      not any(field == possible_field['FIELD'] for possible_field in possible_fields)}
    missing_required_fields = {}
    fields_with_invalid_option = {}
    final_fields = {}

    for possible_field in possible_fields:
        user_value = user_data.get(possible_field["FIELD"])
        if user_value is not None:  # user has provided a value for this field
            if len(possible_field["DATA"]) == 0:  # there are no options for these fields = all inputs are ok.
                final_fields[possible_field["FIELD"]] = user_value

            else:  # there are options for these fields - resolve their values by their description
                resolved_value = next(
                    (entry["NAME"] for entry in possible_field["DATA"] if entry['VALUE'] == user_value), None)
                if resolved_value is None:
                    fields_with_invalid_option[possible_field["FIELD"]] = possible_field["DATA"]
                else:
                    final_fields[possible_field["FIELD"]] = resolved_value
        elif possible_field['REQUIRED'] == "X":  # missing required field
            missing_required_fields[possible_field["FIELD"]] = possible_field["DATA"]

    if len(unknown_fields) > 0 or len(missing_required_fields) > 0 or len(fields_with_invalid_option) > 0:
        raise DataInvalidError(scope, unknown_fields, missing_required_fields, fields_with_invalid_option)

    return final_fields
