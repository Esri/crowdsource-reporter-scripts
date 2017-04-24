# ------------------------------------------------------------------------------
# Name:        email_notifications.py
# Purpose:     sends email notifications to users and internal staff when a new report is submitted

# Copyright 2017 Esri

#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# ------------------------------------------------------------------------------
from os import path, sys
from datetime import datetime as dt
from arcgis import gis
from arcgis.features import FeatureLayer
from send_email import EmailServer

# Credentials for AGOL/Portal
orgURL = 'http://www.arcgis.com/'
username = ''
password = ''

# SMTP information
smtp_server = ''
smtp_username = ''
smtp_password = ''
use_tls = True
from_address = ''
reply_to = ''

# Status field
emails_sent_text = 'Yes'

# Services to send e-mail notifications for. Repeat for each service to send e-mails for.
#   service url: URL of the AGOL/Portal service layer (including index number)
#   user email field: Field in the service containing the submitter's e-mail address
#   internal email address: E-mail address of the person or alias inside the organization
#       to notify when a new report is submitted
#   email status field: Text status field used to determine if e-mails have already been
#       sent for the report. The emails_sent_text variable determines the value used to
#       query for to find records that have not yet had e-mail notifications sent
#   user email body template: Relative path to html to include in the body of the e-mail
#       sent to the user.
#   user email subject: Subject of the e-mail sent to the user.
#   internal email body template: Relative path to html to include in the body of the e-mail
#       sent to the person or alias inside the organization.
#   internal email subject: Subject of the e-mail sent to the person or alias inside the organization.
email_services = [
        {'service url': '',
         'user email field': '',
         'internal email address': '',
         'email status field': '',
         'user email body template': './user_email_template.html',
         'user email subject': 'Thank you for your submission',
         'internal email body template': './internal_email_template.html',
         'internal email subject': 'New problem report submitted'},

        {'service url': '',
         'user email field': '',
         'internal email address': '',
         'email status field': '',
         'user email body template': './user_email_template.html',
         'user email subject': 'Thank you for your submission',
         'internal email body template': './internal_email_template.html',
         'internal email subject': 'New problem report submitted'},
        ]

def _get_features(feature_layer, where_clause):
    """Get the features for the given feature layer of a feature service. Returns a list of json features.
    Keyword arguments:
    feature_layer - The feature layer to return the features for
    where_clause - The expression used in the query"""
      
    total_features = []
    max_record_count = feature_layer.properties['maxRecordCount']
    if max_record_count < 1:
        max_record_count = 1000
    offset = 0
    while True:
        features = feature_layer.query(where=where_clause, return_geometry=False, result_offset=offset, result_record_count=max_record_count).features
        total_features += features
        if len(features) < max_record_count:
            break
        offset += len(features)
    return total_features

def main():
    log = path.join(sys.path[0], 'email_log.log')
    with open(log, 'a') as log:
        try:
            with EmailServer(smtp_server, smtp_username, smtp_password, use_tls) as email_server:
                target = gis.GIS(orgURL, username, password)

                for email_service in email_services:
                    try:
                        if email_service['service url'] == '':
                            continue

                        user_email_field = email_service['user email field']
                        internal_email_address = email_service['internal email address']

                        feature_layer = FeatureLayer(email_service['service url'], target)
                        features = _get_features(feature_layer, "{0} IS NULL OR {0} != '{1}'".format(email_service['email status field'], emails_sent_text))
                        for feature in features:
                            if user_email_field in feature.fields:
                                html = path.join(path.dirname(__file__), email_service['user email body template'])
                                with open(html) as file:
                                    email_body = file.read()
                                    email_server.send(from_address=from_address, reply_to=reply_to, 
                                                      to_addresses=[feature.attributes[user_email_field]], 
                                                      subject=email_service['user email subject'],
                                                      email_body=email_body)

                            if internal_email_address != "":
                                html = path.join(path.dirname(__file__), email_service['internal email body template'])
                                with open(html) as file:
                                    email_body = file.read()
                                    email_server.send(from_address=from_address, reply_to=reply_to, 
                                                      to_addresses=[internal_email_address], 
                                                      subject=email_service['internal email subject'],
                                                      email_body=email_body)

                            feature.attributes[email_service['email status field']] = emails_sent_text
                        
                        if len(features) > 0:
                            feature_layer.edit_features(updates=features)
                
                    except Exception as ex:
                        print(ex)
                        log.write('{0} - {1}\n'.format(dt.now(), ex))

        except Exception as ex:
            print(ex)
            log.write('{0} - {1}\n'.format(dt.now(), ex))

if __name__ == '__main__':
    main()
