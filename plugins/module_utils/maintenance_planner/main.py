import pathlib

from .. import auth, exceptions
from ..client import ApiClient
from . import api


def run_files(params):
    # Runner for maintenance_planner_files module.
    result = dict(
        download_basket={},
        changed=False,
        msg=''
    )

    try:
        client = ApiClient()
        username = params['suser_id']
        password = params['suser_password']
        transaction_name = params['transaction_name']
        validate_url = params['validate_url']

        auth.login(client, username, password)
        api.auth_userapps(client)

        transaction_id = api.get_transaction_id(client, transaction_name)
        download_basket_details = api.get_transaction_filename_url(client, transaction_id, validate_url)

        result['download_basket'] = [{'DirectLink': i[0], 'Filename': i[1]} for i in download_basket_details]
        result['changed'] = True
        result['msg'] = "Successfully retrieved file list from SAP Maintenance Planner."

    except ImportError as e:
        result['failed'] = True
        if 'requests' in str(e):
            result['missing_dependency'] = 'requests'
        elif 'urllib3' in str(e):
            result['missing_dependency'] = 'urllib3'
        elif 'beautifulsoup4' in str(e):
            result['missing_dependency'] = 'beautifulsoup4'
        elif 'lxml' in str(e):
            result['missing_dependency'] = 'lxml'
        else:
            result['msg'] = "An unexpected import error occurred: {0}".format(e)
    except exceptions.SapLaunchpadError as e:
        result['failed'] = True
        result['msg'] = str(e)
    except Exception as e:
        result['failed'] = True
        result['msg'] = 'An unexpected error occurred: {0}'.format(e)

    return result


def run_stack_xml_download(params):
    # Runner for maintenance_planner_stack_xml_download module.
    result = dict(
        changed=False,
        msg=''
    )

    try:
        client = ApiClient()
        username = params['suser_id']
        password = params['suser_password']
        transaction_name = params['transaction_name']
        dest = params['dest']

        auth.login(client, username, password)
        api.auth_userapps(client)

        transaction_id = api.get_transaction_id(client, transaction_name)
        xml_content, filename = api.get_transaction_stack_xml_content(client, transaction_id)

        if not filename:
            filename = "{0}_stack.xml".format(transaction_name)

        dest_path = pathlib.Path(dest)
        if not dest_path.is_dir():
            result['failed'] = True
            result['msg'] = "Destination directory does not exist: {0}".format(dest)
            return result

        output_file = dest_path / filename

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)
        except IOError as e:
            result['failed'] = True
            result['msg'] = "Failed to write to destination file {0}: {1}".format(output_file, e)
            return result

        result['changed'] = True
        result['msg'] = "SAP Maintenance Planner Stack XML successfully downloaded to {0}".format(output_file)

    except ImportError as e:
        result['failed'] = True
        if 'requests' in str(e):
            result['missing_dependency'] = 'requests'
        elif 'urllib3' in str(e):
            result['missing_dependency'] = 'urllib3'
        elif 'beautifulsoup4' in str(e) or 'lxml' in str(e):
            result['missing_dependency'] = 'beautifulsoup4 and/or lxml'
        else:
            result['msg'] = "An unexpected import error occurred: {0}".format(e)
    except exceptions.SapLaunchpadError as e:
        result['failed'] = True
        result['msg'] = str(e)
    except Exception as e:
        result['failed'] = True
        result['msg'] = 'An unexpected error occurred: {0}'.format(e)

    return result
