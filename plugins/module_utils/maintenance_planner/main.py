import pathlib

from .. import auth, exceptions
from ..client import ApiClient
from . import api
from requests.exceptions import HTTPError


def run_files(params):
    # Runner for maintenance_planner_files module.
    result = dict(
        download_basket={},
        changed=False,
        msg=''
    )

    client = ApiClient()
    username = params['suser_id']
    password = params['suser_password']
    transaction_name = params['transaction_name']
    validate_url = params['validate_url']

    try:
        auth.login(client, username, password)
        api.auth_userapps(client)

        transaction_id = api.get_transaction_id(client, transaction_name)
        download_basket_details = api.get_transaction_filename_url(client, transaction_id)

        if validate_url:
            for pair in download_basket_details:
                url = pair[0]
                try:
                    client.head(url)
                except HTTPError:
                    raise exceptions.DownloadError(f'Download link is not available: {url}')

        result['download_basket'] = [{'DirectLink': i[0], 'Filename': i[1]} for i in download_basket_details]
        result['changed'] = True
        result['msg'] = "Successfully retrieved file list from SAP Maintenance Planner."

    except (exceptions.SapLaunchpadError, HTTPError) as e:
        result['failed'] = True
        result['msg'] = str(e)
    except Exception as e:
        result['failed'] = True
        result['msg'] = f"An unexpected error occurred: {e}"

    return result


def run_stack_xml_download(params):
    # Runner for maintenance_planner_stack_xml_download module.
    result = dict(
        changed=False,
        msg=''
    )

    client = ApiClient()
    username = params['suser_id']
    password = params['suser_password']
    transaction_name = params['transaction_name']
    dest = params['dest']

    try:
        auth.login(client, username, password)
        api.auth_userapps(client)

        transaction_id = api.get_transaction_id(client, transaction_name)
        xml_content, filename = api.get_transaction_stack_xml_content(client, transaction_id)

        if not filename:
            filename = f"{transaction_name}_stack.xml"

        dest_path = pathlib.Path(dest)
        if not dest_path.is_dir():
            result['failed'] = True
            result['msg'] = f"Destination directory does not exist: {dest}"
            return result

        output_file = dest_path / filename

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)
        except IOError as e:
            result['failed'] = True
            result['msg'] = f"Failed to write to destination file {output_file}: {e}"
            return result

        result['changed'] = True
        result['msg'] = f"SAP Maintenance Planner Stack XML successfully downloaded to {output_file}"

    except (exceptions.SapLaunchpadError, HTTPError) as e:
        result['failed'] = True
        result['msg'] = str(e)
    except Exception as e:
        result['failed'] = True
        result['msg'] = f"An unexpected error occurred: {e}"

    return result
