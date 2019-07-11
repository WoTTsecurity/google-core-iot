## Automatic enrolling/updating script

This script is a continuation of the instructions given by the link

https://wott.io/blog/tutorials/2019/06/14/google-core-iot 

But if you have a fleet of devices, it is difficult to perform the above steps from time to time to renew the certificates or upload new ones to just created devices.
It would be right to have a script that allows you to perform all these tasks, as well as register new devices in the Google IoT registry, according to the list of devices in WoTT Dash.
The following example script allows you to do this. This works in the following scenario.

- Retrieve all devices from WoTT Dash
- Retrieve all devices from Google IoT Registry.
- Check all" Google devices " for updated certificates in the WoTT list. And update if so.
- Enroll devices that are present in the WoTT Dash and not in the Google Registry  
- All devices with expired certificates in WoTT Dash will be skipped.
  
For script working you need:

- To get WoTT API token. You can get it from the WoTT Dash profile page. (On the upper right corner, click by your username, and select the `Profile` menu. In profile settings select `API token` and press `Create`)
- To get the Google service account secret JSON. You need to open your project on Google Cloud Platform, and in `IAM & Admon`/`Service accounts` menu select `+CREATE SERVICE ACCOUNT`. For created service account you need to select two roles `Cloud IoT Device Controller` and `Cloud IoT Provisioner`.  
  After the account was created press on the `Create Key` button and save the JSON file.
- Install requirements.

```shell
python3 -m venv ~/.gc-rt-venv
source ~/.gc-rt-venv/bin/activate
pip install -r requirements.txt
```

Set the `PROJECT_ID`, `CLOUD_REGION`, `REGISTRY_ID` environment variables to project settings. 
Set `GOOGLE_APPLICATION_CREDENTIALS` environment variables to your google service account JSON file path.
Set `WOTT_API_TOKEN` environment variable to your WoTT API token string. 
  
Now you can run it as follows  
```
python cert-rotate.py
```  
