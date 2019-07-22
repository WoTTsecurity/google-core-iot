import argparse
import json
import os

import requests

from google.oauth2 import service_account
from google.cloud.iot import DeviceManagerClient, types, enums
from google.api_core.exceptions import NotFound


WOTT_ENDPOINT = os.getenv('WOTT_ENDPOINT', 'https://api.wott.io')
PROJECT = 'wott-244904'
LOCATION = 'europe-west1'
REGISTRY = 'wott_registry'
PUBSUB = 'wott-pubsub'


def create_client():
    # iot.DeviceManagerClient doesn't do this himself, unlike other Google libs.
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        with open(os.environ['GOOGLE_APPLICATION_CREDENTIALS']) as key:
            key_json = json.load(key)
            credentials = service_account.Credentials.from_service_account_info(key_json)
    else:
        credentials = None

    client = DeviceManagerClient(credentials=credentials)
    return client


def create_registry(client, project_name, location, registry_name, pubsub_topic, ca_cert):
    location_path = client.location_path(project_name, location)
    registry_path = client.registry_path(project_name, location, registry_name)
    try:
        registry = client.get_device_registry(registry_path)
    except NotFound:
        print(f'Registry "{registry_path}" not found, creating.')
        registry = types.DeviceRegistry(
            id = registry_name,
            # name should be empty
            mqtt_config = types.MqttConfig(
                mqtt_enabled_state = enums.MqttState.MQTT_ENABLED
            ),
            state_notification_config = types.StateNotificationConfig(
                pubsub_topic_name = f"projects/{project_name}/topics/{pubsub_topic}"
            ),
            credentials = [types.RegistryCredential(
                public_key_certificate=types.PublicKeyCertificate(
                    format=enums.PublicKeyCertificateFormat.X509_CERTIFICATE_PEM,
                    certificate=ca_cert
                )
            )],
            http_config = types.HttpConfig(
                http_enabled_state=enums.HttpState.HTTP_DISABLED
            )
        )
        registry = client.create_device_registry(location_path, registry)
    return registry


def create_or_update_device(client, project_name, location_name, registry_name, device_id, device_cert):
    device_name = client.device_path(project_name, location_name, registry_name, 'wott-' + device_id)
    try:
        device = client.get_device(device_name)
    except NotFound:
        print(f'Creating new device {device_name}')
        device = types.Device(
            id='wott-' + device_id,
            # name should be empty
            credentials=[
                types.DeviceCredential(
                    public_key=types.PublicKeyCredential(
                        format=enums.PublicKeyFormat.ES256_X509_PEM,
                        key=device_cert
                    )
                )
            ]
        )
        registry_path = client.registry_path(project_name, location_name, registry_name)
        device = client.create_device(registry_path, device)
    else:
        print(f'Updating device {device_name}')
        device = types.Device(
            name = device_name,
            credentials=[
                types.DeviceCredential(
                    public_key=types.PublicKeyCredential(
                        format=enums.PublicKeyFormat.ES256_X509_PEM,
                        key=device_cert
                    )
                )
            ]
        )
        client.update_device(device, types.FieldMask(paths=['credentials']))
    return device


def get_ca_cert(debug):
    ca = requests.get(f'{WOTT_ENDPOINT}/v0.2/ca-bundle')

    if debug:
        print("[RECEIVED] Get CA Cert: {}".format(ca.status_code))
        print("[RECEIVED] Get CA Cert: {}".format(ca.content))

    if not ca.ok:
        print('Failed to get CA...')
        print(ca.status_code)
        print(ca.content)
        return

    return ca.json()['ca_bundle']


def get_device_cert(device_id, debug):
    cert_request = requests.get(f'{WOTT_ENDPOINT}/v0.2/device-cert/{device_id}')

    if debug:
        print("[RECEIVED] Get CA Cert: {}".format(cert_request.status_code))
        print("[RECEIVED] Get CA Cert: {}".format(cert_request.content))

    if not cert_request.ok:
        print('Failed to get CA...')
        print(cert_request.status_code)
        print(cert_request.content)
        return

    return cert_request.content



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--project',
        required=True,
        help="IoT Project name.")
    parser.add_argument(
        '--location',
        required=True,
        help="IoT location region.")
    parser.add_argument(
        '--registry',
        required=False,
        default=REGISTRY,
        help="IoT Registry name.")
    parser.add_argument(
        '--pubsub',
        required=False,
        default=PUBSUB,
        help="pubsub name.")
    parser.add_argument(
        '--device',
        required=False,
        default='',
        help="device id.")
    parser.add_argument(
        '--debug',
        action="store_true",
        help="debug mode.")
    args = parser.parse_args()

    ca_cert = get_ca_cert(args.debug)
    client = create_client()
    registry = create_registry(client, args.project, args.location, args.registry, args.pubsub, ca_cert)

    device_cert = get_device_cert(args.device, args.debug)
    device = create_or_update_device(client, args.project, args.location, args.registry, args.device, device_cert)
