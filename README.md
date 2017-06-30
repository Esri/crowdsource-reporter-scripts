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

A script to filter features based on lists of explicit and sensitive words. The script updates a flag field when a word on these lists is detected so that the feature no longer meets the requirements of a filter on a layer in a web map. The script also compares words against a list of good words to avoid accidental filtering.

##### Requirements
Python 2.7, ArcPy

##### Configuration
For more information on configuring this script, see the documentation: [Automated Moderation][]

[Download a supported version of the Automated Moderation script here][]

## Generate IDs

A script to generate identifiers for features based on a defined sequence and that increment based on a defined interval.

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
