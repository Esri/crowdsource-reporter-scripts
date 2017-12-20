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

# Update 7/17/2017: corrected SQL syntax in comments

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

# Services to send e-mail notifications for. Repeat for each service to send e-mails for.
# Each service can have multiple messages
#   service url: URL of the AGOL/Portal service layer (including index number)
#   query: SQL where clause used to identify which features require each message.
#           For example, use "STATUS = 'Submitted' AND PRIORITY = 1" to only send this message for reports that have
#           both the value 'Submitted' in the text field 'STATUS' and the value 1 in the numeric field 'PRIORITY'.
#           *** Pay close attention to the use of double quotes to surround the entire clause, single quotes around the
#           text field values, and no quotes around values from numeric fields.
#           All field names and values are case-sensitive.***
#   email address: E-mail address, or name of the field containing the email address, where the notification should be sent.
#   email body template: Relative path to html to include in the body of the e-mail sent to the user.
#   email subject: Subject of the e-mail sent to the user.
#   body substitutions: Pairs of strings and values or strings and field names used to customize the text in the body
#           of the email. It is strongly recommended to use special characters in these strings to avoid
#           accidentally substituting the wrong content
#           For example, include include the string Hello, {name} in the email template and set the body substitution
#           value to '{name}': 'NAME' to replace the characters {name} with the value in the NAME field of the report.
#   status field: Text field used to determine if this message has already been sent for the report.
#           The emails_sent_text variable determines the value used to query for to find records that have not yet
#           had e-mail notifications sent
#   completed value: Value in the status field that indicates that this message has already been sent for this report.

email_services = [
        {'service url': 'http://services.arcgis.com/b6gLrKHqgkQb393u/arcgis/rest/services/allisontest/FeatureServer/0',
         'messages': [
                 {'query': "",
                  'email address': '',
                  'email body template': '',
                  'email subject': '',
                  'body substitutions': {'': ''},
                  'status field': '',
                  'completed value': ''}
         ]}
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
        features = feature_layer.query(where=where_clause,
                                       return_geometry=False,
                                       result_offset=offset,
                                       result_record_count=max_record_count).features
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

                        for message in email_service['messages']:

                            # build sql
                            sql = "{} <> '{}'".format(message['status field'], message['completed value'])
                            sql += " AND {}".format(message['query'])

                            feature_layer = FeatureLayer(email_service['service url'], target)
                            features = _get_features(feature_layer, sql)

                            for feature in features:
                                if message['email address']:
                                    if message['email address'] in feature.fields:
                                        email = feature.attributes[message['email address']]
                                    else:
                                        email = message['email address']

                                if email:
                                    try:
                                        html = path.join(path.dirname(__file__), message['email body template'])
                                        with open(html) as file:
                                            email_body = file.read()
                                            for sub in message['body substitutions']:
                                                if message['body substitutions'][sub] in feature.fields:
                                                    email_body = email_body.replace(sub, feature.attributes[message['body substitutions'][sub]])
                                                else:
                                                    email_body = email_body.replace(sub, message['body substitutions'][sub])

                                            email_server.send(from_address=from_address,
                                                              reply_to=reply_to,
                                                              to_addresses=[email],
                                                              subject=message['email subject'],
                                                              email_body=email_body)
                                    except Exception as ex:
                                        print(ex)
                                        log.write('{0} - {1}\n'.format(dt.now(), ex))

                                feature.attributes[message['status field']] = message['completed value']

                            if len(features) > 0:
                                status = feature_layer.edit_features(updates=features)
                                for value in status['updateResults']:
                                    if not value['success']:
                                        log.write(value)
                
                    except Exception as ex:
                        print(ex)
                        log.write('{0} - {1}\n'.format(dt.now(), ex))

        except Exception as ex:
            print(ex)
            log.write('{0} - {1}\n'.format(dt.now(), ex))

if __name__ == '__main__':
    main()
