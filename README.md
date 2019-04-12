# crowdsource-reporter-scripts
This repository contains a series of tools that can be used to extend the functionality of editable feature layers published to an ArcGIS Online organization or an ArcGIS portal. The scripts can be scheduled using an application such as Windows Tasks to scan the feature layers for new content.

[New to Github? Get started here.]: http://htmlpreview.github.com/?https://github.com/Esri/esri.github.com/blob/master/help/esri-getting-to-know-github.html
[ArcGIS for Local Government maps and apps]: http://solutions.arcgis.com/local-government
[Local Government GitHub repositories]: http://esri.github.io/#Local-Government
[guidelines for contributing]: https://github.com/esri/contributing
[LICENSE]: https://github.com/ArcGIS/crowdsource-reporter-scripts/blob/master/LICENSE.txt
[Automated Moderation]: http://solutions.arcgis.com/local-government/help/crowdsource-reporter/get-started/automated-moderation/
[Generate IDs]: http://solutions.arcgis.com/local-government/help/crowdsource-reporter/get-started/generate-ids/
[Email Notifications]: http://solutions.arcgis.com/local-government/help/crowdsource-reporter/get-started/email-notification/
[Download a supported version of the Automated Moderation script here]: http://links.esri.com/localgovernment/download/AutomatedModerationScript/
[Download a supported version of the Email Notification script here]: http://links.esri.com/localgovernment/download/EmailNotificationScript/
[Download a supported version of the Generate IDs script here]: http://links.esri.com/localgovernment/download/GenerateIDScript/



## Automated Moderation

A script to filter features based on lists of explicit and sensitive words. The script updates a flag field when a word on these lists is detected so that the feature no longer meets the requirements of a filter on a layer in a web map. 

##### Requirements
Python 2.7, ArcPy

##### Configuration
For more information on configuring this script, see the documentation: [Automated Moderation][]

[Download a supported version of the Automated Moderation script here][]

## Generate IDs

A script to generate identifiers for features using a defined sequence and a value that increments on a defined interval.

##### Requirements
Python 2.7, ArcPy
##### Configuration
For more information on configuring this script, see the documentation: [Generate IDs][]

[Download a supported version of the Generate IDs script here][]

## Email Notifications

Send emails to specific email addresses, or to addresses in fields in the data. Multiple messages can be configured for each layer based on attribute values. The script updates a flag field to indicate that each message has been sent.

##### Requirements
Python 3, ArcGIS API for Python

##### Configuration
For more information on configuring this script, see the documentation: [Email Notifications][]

[Download a supported version of the Email Notification script here][]


## Calculate Nearby Values

Calculate feature attributes based on the attributes of co-incident features.

##### Requirements
Python 3, ArcGIS API for Python

##### Configuration
For more information on configuring this script, see the documentation: [Calculate Nearby Values][]

[Download a supported version of the Calculate Nearby Values script here][]


## Workforce Connection

Create workforce assignments from incomming Crowdsource REporter, GeoForm, and Survey 123 reports.

##### Requirements
Python 3, ArcGIS API for Python

##### Configuration
For more information on configuring this script, see the documentation: [Workforce Connection][]

[Download a supported version of the Workforce Connection script here][]


## Cityworks Connection (Beta)

A script to pass data from editable ArcGIS feature layers to Cityworks tables, including related records and attachments. The script also passes the Cityworks Request ID and open date back to the ArcGIS feature. 

The script assumes that the data is being collected using the Crowdsource Reporter application. For input, it requires the group containing the maps that are visible in the Crowdsource Reporter app.

Note: This integration requires specific versions of the Cityworks platform and integration with existing service request content.
If you would like to integrate Cityworks / Citizen Problem Reporter then please reach out to your Cityworks account representative, who can get you connected with the technical resources inside of Cityworks to do the integration. 

##### Requirements
ArcGIS Pro 1.4+ Python 3.5+, ArcGIS API for Python 1.2.5+

##### Configuration
1. If not previously installed, use the Python Package Manager in ArcGIS Pro to install the ArcGIS API for Python (package name: arcgis)
2. In ArcGIS Pro, install the [Solutions Deployment Tool](http://solutions.arcgis.com/shared/help/deployment-tool/), and use it to deploy the Citizen Problem Reporter solution to your portal or organization. If necessary, use this tool to add fields to the layers and to update the domains to match the report types found in Cityworks.
3. In ArcGIS Pro, add the Connect2Cityworks toolbox to your current project.
4. Open the tool contained in the toolbox.
5. Provide the connection information for both Cityworks and ArcGIS Online/ArcGIS Enterprise.
6. Choose the group used to configure the Crowdsource Reporter application being used to collect the data.
7. Choose the layers that the tool should process. These parameters will list all layers from the maps in the group that have at least one editable field configured in the popup.
8. Choose the Cityworks field that contains the Request ID, and the ArcGIS field where this value should be recorded. Only ArcGIS fields found in all selected layers will be options for the ArcGIS Report ID Field parameter.
9. Choose the Cityworks field that contains the open date of the service request, and the ArcGIS field where this value should be recorded. Only ArcGIS fields found in all selected layers will be options for the ArcGIS Open Date Field parameter.
10. Choose the Cityworks field and the ArcGIS field that contains the type of request generated by the report. Both fields must support identical values. Only ArcGIS fields found in all selected layers will be options for the ArcGIS Report Type Field parameter.
11. Choose the field used to indicate the status of the report with regards to being transferred to Cityworks. Specify the value of this field when the report needs to be transferred in the Flag On Value parameter, and the value once the transfer is complete in the Flag Off Value parameter.
12. Map other field pairs to transfer additional information received with the report to Cityworks. Some Cityworks fields you will want to consider are: CallerFirstName, CallerLastName, CallerAddress, CallerCity, CallerState, CallerZip, CallerHomePhone, CallerEmail, Details, Address. Map an unused Cityworks Universal Custom Field to the ArcGIS field OBJECTID. For example Num5 to OBJECTID.
13. Optionally, choose editable tables from the maps to process as well as the layers. These related records will be copied to Cityworks as additional information on the report. As with the layers, map the ArcGIS and Cityworks fields to specify which data should be transferred. To transfer comments, map the following Cityworks fields: FirstName, LastName, Comments.
14. Finally, choose a location to save out this information in a configuration file. This configuration file will be read by the script that will handle the transfer of information between ArcGIS and Cityworks.

The following is an example of what a config file might look like:
```
{
    "cityworks": {
        "username": "apiuser",
        "password": "apipassword",
        "url": "https://cityworks.your-org.com/CityworksSite",
        "timezone": "America/Denver",
        "isCWOL": false
    },
    "fields": {
        "ids": [
            "RequestId",
            "REPORTID"
        ],
        "type": [
            "ProblemSid",
            "PROBTYPE"
        ],
        "opendate": [
            "DateTimeInit",
            "submitdt"
        ],
        "layers": [
            [
                "CallerAddress",
                "ADDRESS"
            ],
            [
                "CallerCity",
                "CITY"
            ],
            [
                "CallerState",
                "STATE"
            ],
            [
                "CallerZip",
                "ZIP"
            ],
            [
                "CallerFirstName",
                "FNAME"
            ],
            [
                "CallerLastName",
                "LNAME"
            ],
            [
                "CallerHomePhone",
                "PHONE"
            ],
            [
                "CallerEmail",
                "EMAIL"
            ],
            [
                "Details",
                "DETAILS"
            ],
            [
                "Address",
                "LOCATION"
            ],
            [
                "Num5",
                "OBJECTID"
            ]
        ],
        "tables": [
            [
                "FirstName",
                "FNAME"
            ],
            [
                "LastName",
                "LNAME"
            ],
            [
                "Comments",
                "COMMENT"
            ]
        ]
    },
    "flag": {
        "field": "processed",
        "on": "No",
        "off": "Yes"
    },
    "arcgis": {
        "username": "ArcGISUser",
        "password": "ArcGISPassword",
        "layers": [
            "https://services.arcgis.com/5555555555555555/arcgis/rest/services/Citizen_Request_Portal/FeatureServer/2",
            "https://services.arcgis.com/5555555555555555/arcgis/rest/services/Citizen_Request_Portal/FeatureServer/1",
            "https://services.arcgis.com/5555555555555555/arcgis/rest/services/Citizen_Request_Portal/FeatureServer/0"
        ],
        "tables": [
            "https://services.arcgis.com/5555555555555555/arcgis/rest/services/Citizen_Request_Portal/FeatureServer/4",
            "https://services.arcgis.com/5555555555555555/arcgis/rest/services/Citizen_Request_Portal/FeatureServer/3",
            "https://services.arcgis.com/5555555555555555/arcgis/rest/services/Citizen_Request_Portal/FeatureServer/5"
        ],
        "url": "https://yourorg.maps.arcgis.com"
    }
}
```

To execute the script that transfers data between ArcGIS and Cityworks, configure an application such as Windows Task Scheduler.

1. Open Windows Task Scheduler
2. Click Action > Create Task and provide a name for the task.
3. Click the Action tab and click New.
4. Set Action to Start a Program.
5. Browse to the location of your Python 3 installation (for example, <default directory>\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-python3\python.exe).
6. In the Add arguments text box, copy the name of the script (connect_to_cityworks.py) and the path to the configuration file save from running the tool in ArcGIS Pro.The script name and the configuration file path must be separated by a script, and the configuration file path must be surrounded with double quotes if it contains any spaces.
7. In the Start in text box, type the path to the folder containing the scripts and email templates and click OK.
8. Click the Trigger tab, click New, and set a schedule for your task.
9. Click OK.


## General Help
* [New to Github? Get started here.][]

## Resources

Learn more about Esri's [ArcGIS for Local Government maps and apps][].

Show me a list of other [Local Government GitHub repositories][].

## Issues

Find a bug or want to request a new feature?  Please let us know by submitting an issue.

## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing][].

## Licensing

Copyright 2016 Esri

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

A copy of the license is available in the repository's [LICENSE][] file.
