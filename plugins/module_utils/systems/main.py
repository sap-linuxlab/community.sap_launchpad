import os
import pathlib
from requests.exceptions import HTTPError

from .. import auth, exceptions
from ..client import ApiClient
from . import api


def run_systems_info(params):
    # Main runner function for the systems_info module.
    result = {'changed': False, 'failed': False, 'systems': []}
    client = ApiClient()
    try:
        auth.login(client, params['suser_id'], params['suser_password'])
        result['systems'] = api.get_systems(client, params['filter'])
    except (exceptions.SapLaunchpadError, api.SystemNotFoundError) as e:
        result['failed'] = True
        result['msg'] = str(e)
    return result


def run_license_keys(params):
    # Main runner function for the license_keys module.
    result = {'changed': False, 'failed': False, 'warnings': []}
    client = ApiClient()
    username = params['suser_id']
    password = params['suser_password']
    installation_nr = params['installation_nr']
    system_nr = params['system_nr']
    state = params['state']

    try:
        auth.login(client, username, password)
        api.validate_installation(client, installation_nr, username)

        # If system_nr is not provided, try to find it using the SID for idempotency.
        if not system_nr:
            system_data_params = params.get('system_data', {})
            sid = system_data_params.get('sysid')
            if sid:
                filter_str = f"Insnr eq '{installation_nr}' and sysid eq '{sid}'"
                existing_systems = api.get_systems(client, filter_str)
                if len(existing_systems) == 1:
                    system_nr = existing_systems[0]['Sysnr']
                    result['warnings'].append(f"A system with SID '{sid}' already exists. Using system number {system_nr} for update.")
                elif len(existing_systems) > 1:
                    # Ambiguous situation: multiple systems with the same SID.
                    # Force user to provide system_nr to select one.
                    system_nrs_found = [s['Sysnr'] for s in existing_systems]
                    result['failed'] = True
                    result['msg'] = (f"Multiple systems with SID '{sid}' found under installation '{installation_nr}': "
                                     f"{', '.join(system_nrs_found)}. Please provide a specific 'system_nr' to select which system to update.")
                    return result

        is_new_system = not system_nr
        if is_new_system:
            if state == 'absent':
                result['msg'] = "Cannot ensure absence of a new system; system_nr is required."
                result['failed'] = True
                return result

            product_id = api.get_product_id(client, params['product_name'], installation_nr, username)
            version_id = api.get_version_id(client, params['product_version'], product_id, installation_nr, username)

            system_data, warning = api.validate_system_data(client, params['system_data'], version_id, system_nr, installation_nr, username)
            if warning:
                result['warnings'].append(warning)

            license_data = api.validate_licenses(client, params['licenses'], version_id, installation_nr, username)
            generated_licenses = api.generate_licenses(client, license_data, [], version_id, installation_nr, username)
            system_nr = api.submit_system(client, True, system_data, generated_licenses, username)

            result['changed'] = True
            result['system_nr'] = system_nr
            result['msg'] = f"System {system_nr} created successfully."

        else:  # Existing system
            system = api.get_system(client, system_nr, installation_nr, username)
            # The API has been observed to return the version ID under the 'Version' key for existing systems.
            # We check for 'Version' first, then fall back to 'Prodver' for compatibility.
            version_id = system.get('Version') or system.get('Prodver')
            if not version_id:
                raise exceptions.SapLaunchpadError(f"System {system_nr} is missing a required Product Version ID.")
            existing_licenses = api.get_existing_licenses(client, system_nr, username)

            # The API requires a sysdata payload even for an edit operation.
            # It must contain at least the installation number, system number, product version, and system ID.
            sysid = system.get('sysid')
            if not sysid:
                raise exceptions.SapLaunchpadError(f"System {system_nr} is missing a required System ID ('sysid').")

            systype = system.get('systype')
            if not systype:
                raise exceptions.SapLaunchpadError(f"System {system_nr} is missing a required System Type ('systype').")

            sysdata_for_edit = [
                {"name": "insnr", "value": installation_nr},
                {"name": "sysnr", "value": system_nr},
                {"name": "prodver", "value": version_id},
                {"name": "sysid", "value": sysid},
                {"name": "systype", "value": systype}
            ]

            if state == 'present':
                user_licenses = params.get('licenses')
                if not user_licenses:
                    result['msg'] = "System already present. No licenses specified to update."
                    return result

                license_data = api.validate_licenses(client, user_licenses, version_id, installation_nr, username)
                new_or_changed = [l for l in license_data if not any(l['HWKEY'] == el['HWKEY'] and l['LICENSETYPE'] == el['LICENSETYPE'] for el in existing_licenses)]

                if not new_or_changed:
                    result['msg'] = "System and licenses are already in the desired state."
                    return result

                generated = api.generate_licenses(client, new_or_changed, existing_licenses, version_id, installation_nr, username)
                api.submit_system(client, False, sysdata_for_edit, generated, username)
                result['changed'] = True
                result['msg'] = f"System {system_nr} licenses updated successfully."

            elif state == 'absent':
                user_licenses_to_keep = params.get('licenses', [])
                if not user_licenses_to_keep:  # Delete all licenses
                    licenses_to_delete = existing_licenses
                else:
                    validated_to_keep = api.validate_licenses(client, user_licenses_to_keep, version_id, installation_nr, username)
                    key_nrs_to_keep = [l['KEYNR'] for l in existing_licenses if any(k['HWKEY'] == l['HWKEY'] and k['LICENSETYPE'] == l['LICENSETYPE'] for k in validated_to_keep)]
                    licenses_to_delete = [l for l in existing_licenses if l['KEYNR'] not in key_nrs_to_keep]

                if not licenses_to_delete:
                    result['msg'] = "All specified licenses are already absent or were not present."
                    return result

                deleted_licenses = api.delete_licenses(client, licenses_to_delete, existing_licenses, version_id, installation_nr, username)
                api.submit_system(client, False, sysdata_for_edit, deleted_licenses, username)
                result['changed'] = True
                result['msg'] = f"Successfully deleted licenses from system {system_nr}."

        # Download/return license file content if applicable
        if state == 'present':
            user_licenses = params.get('licenses')
            if user_licenses:
                validated_licenses = api.validate_licenses(client, user_licenses, version_id, installation_nr, username)
                key_nrs = api.get_license_key_numbers(client, validated_licenses, system_nr, username)
                content_bytes = api.download_licenses(client, key_nrs)
                content_str = content_bytes.decode('utf-8')

                result['license_file'] = content_str

                if params.get('download_path'):
                    dest_path = pathlib.Path(params['download_path'])
                    if not dest_path.is_dir():
                        result['failed'] = True
                        result['msg'] = f"Destination for license file does not exist or is not a directory: {dest_path}"
                        return result

                    output_file = dest_path / f"{system_nr}_licenses.txt"
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(content_str)

                        current_msg = result.get('msg', '')
                        download_msg = f"License file downloaded to {output_file}."
                        result['msg'] = f"{current_msg} {download_msg}".strip()
                    except IOError as e:
                        result['failed'] = True
                        result['msg'] = f"Failed to write license file: {e}"

    except (exceptions.SapLaunchpadError,
            api.InstallationNotFoundError,
            api.SystemNotFoundError,
            api.ProductNotFoundError,
            api.VersionNotFoundError,
            api.LicenseTypeInvalidError,
            api.DataInvalidError,
            ValueError) as e:
        result['failed'] = True
        result['msg'] = str(e)
    except Exception as e:
        result['failed'] = True
        result['msg'] = f"An unexpected error occurred: {type(e).__name__} - {e}"

    return result