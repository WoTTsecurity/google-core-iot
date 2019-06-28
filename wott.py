import json
import os

from google.oauth2 import service_account
from google.cloud.iot import DeviceManagerClient, types, enums
from google.api_core.exceptions import NotFound


PROJECT = 'wott-244904'
LOCATION = 'europe-west1'
REGISTRY = 'wott_registry'
PUBSUB = 'wott-pubsub'
CA_CERT = "-----BEGIN CERTIFICATE-----\nMIICIjCCAcigAwIBAgIUVX6IR6IZkUV5c9uFtkCPqz/S/8IwCgYIKoZIzj0EAwIw\nWzELMAkGA1UEBhMCVUsxDzANBgNVBAcTBkxvbmRvbjEeMBwGA1UEChMVV2ViIG9m\nIFRydXN0ZWQgVGhpbmdzMRswGQYDVQQDExJyb290LWNhLndvdHQubG9jYWwwHhcN\nMTkwMTI0MTY0NjAwWhcNMjAwMTI0MTY0NjAwWjBfMQswCQYDVQQGEwJVSzEPMA0G\nA1UEBxMGTG9uZG9uMSMwIQYDVQQKExpXZWIgb2YgVHJ1c3RlZCBUaGluZ3MsIEx0\nZDEaMBgGA1UEAxMRY2EwLWNhLndvdHQubG9jYWwwWTATBgcqhkjOPQIBBggqhkjO\nPQMBBwNCAARtfUDIXmuqlXh/iUBASCMsuv/okVl5Rr411rtDVkJb9/pOXvytrLHO\npqRoaTb20vjvZJyIfIQHjYCVhqgydJ/0o2YwZDAOBgNVHQ8BAf8EBAMCAYYwEgYD\nVR0TAQH/BAgwBgEB/wIBADAdBgNVHQ4EFgQUqbbNcauIPejjNseUbyqxFACFNwEw\nHwYDVR0jBBgwFoAUFFMJ5IilG4BJpHcho67y9faWbpQwCgYIKoZIzj0EAwIDSAAw\nRQIhALsFD/KDOFfMpiL4/8VA65quwJYPQIZZSljuFbjIadnJAiAJ5rYreEJ0A8du\nlTjJd3us3c4uqtFC+9lvbyvY7Kqsbg==\n-----END CERTIFICATE-----"
DEVICE_ID = '799d00d82544489eb01b339c618d0b62.d.wott.local'
DEVICE_CERT = """
-----BEGIN CERTIFICATE-----
MIICljCCAj2gAwIBAgIUHeVSXevXy8NaE4oW8FhHH66Q3EMwCgYIKoZIzj0EAwIw
XzELMAkGA1UEBhMCVUsxDzANBgNVBAcTBkxvbmRvbjEjMCEGA1UEChMaV2ViIG9m
IFRydXN0ZWQgVGhpbmdzLCBMdGQxGjAYBgNVBAMTEWNhMC1jYS53b3R0LmxvY2Fs
MB4XDTE5MDYyNjEwNTAwMFoXDTE5MDcwMzEwNTAwMFowezELMAkGA1UEBhMCVUsx
DzANBgNVBAgTBkxvbmRvbjEjMCEGA1UEChMaV2ViIG9mIFRydXN0ZWQgVGhpbmdz
LCBMdGQxNjA0BgNVBAMTLTc5OWQwMGQ4MjU0NDQ4OWViMDFiMzM5YzYxOGQwYjYy
LmQud290dC5sb2NhbDBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABHPR6u35nKxO
+YwmBud6tykF0FHEBu2XAN7KBGl9E0Ad3QH1GL9Xn9izpAhN9uRBMVzjriOpmEBn
IeWMThDRO3ejgbowgbcwDgYDVR0PAQH/BAQDAgeAMB0GA1UdJQQWMBQGCCsGAQUF
BwMCBggrBgEFBQcDATAMBgNVHRMBAf8EAjAAMB0GA1UdDgQWBBS/FuaT7csgjr3m
jUetHjWVwK7O9DAfBgNVHSMEGDAWgBSpts1xq4g96OM2x5RvKrEUAIU3ATA4BgNV
HREEMTAvgi03OTlkMDBkODI1NDQ0ODllYjAxYjMzOWM2MThkMGI2Mi5kLndvdHQu
bG9jYWwwCgYIKoZIzj0EAwIDRwAwRAIgJpwOZymT7nzyJvIxhazoHQm7B/TBlR2X
A5NmBOpzKCACIAslvVt01ks2iONwHzG/2OSaDOfzlS4qeBnpgTWrXdZ9
-----END CERTIFICATE-----
"""

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


client = create_client()
registry = create_registry(client, PROJECT, LOCATION, REGISTRY, PUBSUB, CA_CERT)
device = create_or_update_device(client, PROJECT, LOCATION, REGISTRY, DEVICE_ID, DEVICE_CERT)
