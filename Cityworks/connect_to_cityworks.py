# ------------------------------------------------------------------------------
# Name:        connect_to_cityworks.py
# Purpose:     Pass reports from esri to cityworks
#
# Author:      alli6394
#
# Created:     31/10/2016
#
# Version: Unreleased

# Copyright 2016 Esri

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

""" TODO:
        - Build UI
"""

import arcgis
import json
import six

from os import path, sys, remove
from datetime import datetime as dt

# Cityworks settings
baseUrl = "https://cloud01.cityworks.com/_DEMO_KSMMS_15-1_EsriAppsDemo"
cwUser = "water"
cwPwd = "water"

# ArcGIS Online/Portal settings
orgUrl = "http://arcgis4localgov2.maps.arcgis.com"
username = "amuise_lg"
password = "pigsfly"
proxy_port = None
proxy_url = None
services = [['http://services.arcgis.com/b6gLrKHqgkQb393u/arcgis/rest/services/cw2/FeatureServer/0',
             'http://services.arcgis.com/b6gLrKHqgkQb393u/arcgis/rest/services/cw2/FeatureServer/1']]

# Esri field names
fc_type = 'PROBTYPE'        # Values in this field must match Cityworks ProblemCode values
fc_address = 'ADDRESS'      # Street Address of the reporter
fc_city = 'CITY'            # City of the reporter
fc_state = 'STATE'          # State of the reporter
fc_zip = 'ZIP'              # ZIP fo the reporter
fc_fname = 'FNAME'          # First name of the reporter
fc_lname = 'LNAME'          # Last name of the reporter
fc_phone = 'PHONE'          # Phone number of the reporter
fc_email = 'EMAIL'          # Email of the reporter
fc_description = 'DETAILS'  # Report details
fc_location = 'LOCATION'    # Captured location of the report (app must be configured for this)
fc_reportid = 'REPORTID'    # Field to store Cityworks report ID value
fc_flag = "STATUS"          # Field used to identify reports to be pushed to CW
flag_values = ['Submitted', 'Received']  # Value of reports to push, value of processed reports

cm_fname = 'FNAME'
cm_lname = 'LNAME'
cm_addr = 'ADDRESS'
cm_city = 'CITY'
cm_zip = 'ZIP'
cm_state = 'STATE'
cm_phone = 'PHONENUM'
cm_email = 'EMAIL'
cm_subdt = 'CreationDate'
cm_comments = 'COMMENT'

# Global vars
cw_token = ""


def get_response(url):
    http_response = six.moves.urllib.request.urlopen(url)
    decoded = http_response.read().decode('utf-8')

    return json.loads(decoded.strip())


def get_cw_token():
    """Retrieve a token for CityWorks access"""
    data = {"LoginName": cwUser, "Password": cwPwd}
    json_data = six.moves.urllib.parse.quote(json.dumps(data, separators=(',', ':')))
    url = '{}/Services/authentication/authenticate?data={}'.format(baseUrl, json_data)

    response = get_response(url)

    if response == "error":
        return 'error: {}: {}'.format(response["Status"],
                                      response["Message"])

    elif response["Status"] == 0:
        global cw_token
        cw_token = six.moves.urllib.parse.quote(response["Value"]["Token"])

        return 'success'


def get_wkid():
    """Retrieve the WKID of the cityworks layers"""

    url = '{}/Services/AMS/Preferences/User?token={}'.format(baseUrl, cw_token)
    response = get_response(url)

    try:
        return response['Value']['SpatialReference']

    except KeyError:
        return 'error'


def get_problem_types():
    """Retrieve a dict of problem types from cityworks"""

    data = {"ForPublicOnly": 'true'}
    json_data = six.moves.urllib.parse.quote(json.dumps(data, separators=(',', ':')))
    url = '{}/Services/AMS/ServiceRequest/Problems?data={}&token={}'.format(baseUrl, json_data, cw_token)

    try:
        response = get_response(url)
        values = {}
        for val in response['Value']:
            values[val['ProblemCode'].upper()] = int(val['ProblemSid'])

        return values

    except Exception as error:
        return 'error: ' + str(error)


def submit_to_cw(row, prob_types):

    attrs = row.attributes
    geometry = row.geometry

    try:
        prob_sid = prob_types[attrs[fc_type].upper()]

    except KeyError:
        if attrs[fc_type].strip() == '':
            return 'WARNING: No problem type provided. Record {} not exported.\n'.format(attrs['OBJECTID'])
        else:
            return 'WARNING: Problem type {} not found in Cityworks. Record {} not exported.\n'.format(attrs[fc_type],
                                                                                                       attrs['OBJECTID'])

    except AttributeError:
        return 'WARNING: Record {} not exported due to missing value in field {}\n'.format(attrs['OBJECTID'], fc_type)

    # Build dictionary of values to submit to CW
    values = {"CallerAddress": str(attrs[fc_address]),
              "CallerCity": str(attrs[fc_city]),
              "CallerState": str(attrs[fc_state]),
              "CallerZip": str(attrs[fc_zip]),
              "CallerFirstName": str(attrs[fc_fname]),
              "CallerLastName": str(attrs[fc_lname]),
              "CallerHomePhone": str(attrs[fc_phone]),
              "CallerEmail": str(attrs[fc_email]),
              "Details": str(attrs[fc_description]),
              "InitiatedByApp": 'Crowdsource Reporter',
              "Location": str(attrs[fc_location]),
              "ProblemSid": prob_sid,
              "X": geometry['x'],
              "Y": geometry['y']}

    # Convert dict to pretty print json
    json_data = six.moves.urllib.parse.quote(json.dumps(values, separators=(',', ':')))

    # Submit report to CityWorks. Encode chars
    url = '{}/Services/AMS/ServiceRequest/Create?data={}&token={}'.format(baseUrl, json_data, cw_token)
    response = get_response(url)

    return response['Value']['RequestId']


def copy_attachment(lyr, oid, requestid):

    attachmentmgr = arcgis.features.managers.AttachmentManager(lyr)
    attachments = attachmentmgr.get_list(oid)

    for attachment in attachments:
        # download attachment
        attpath = attachmentmgr.download(oid, attachment['id'])

        # upload attachment
        values = {"Filename": attpath, "WorkOrderId": requestid}
        json_data = six.moves.urllib.parse.quote(json.dumps(values, separators=(',', ':')))
        url = '{}/Services/AMS/Attachments/AddWorkOrderAttachment?data={}&token={}'.format(baseUrl, json_data, cw_token)
        response = get_response(url)

        # delete downloaded file
        remove(attpath)

        return response


def copy_comments(lyr, pkey_fld, record, fkey_fld):

    try:
        sql = "{} = {}".format(pkey_fld, record.attributes[fkey_fld])
        parents = lyr.query(where=sql)

    except Exception:
        sql = "{} = '{}'".format(pkey_fld, record.attributes[fkey_fld])
        parents = lyr.query(where=sql)

    parent = parents.features[0]
    if not parent.attributes[fc_reportid]:
        return ""

    values = {"RequestId": parent.attributes[fc_reportid],
              "FirstName": record.attributes[cm_fname],
              "LastName": record.attributes[cm_lname],
              "CustAddress": record.attributes[cm_addr],
              "CustCity": record.attributes[cm_city],
              "CustZip": record.attributes[cm_zip],
              "CustState": record.attributes[cm_state],
              "OtherPhone": record.attributes[cm_phone],
              "Email": record.attributes[cm_email],
              "ProbDetails": record.attributes[cm_comments],
              "CallerType": "CS Reporter"}

    json_data = six.moves.urllib.parse.quote(json.dumps(values, separators=(',', ':')))
    url = '{}/Services/AMS/CustomerCall/AddToRequest?data={}&token={}'.format(baseUrl, json_data, cw_token)
    response = get_response(url)

    return response


def main():

    id_log = path.join(sys.path[0], 'cityworks_log.log')
    with open(id_log, 'a') as log:
        log.write('\n\n{}\n'.format(dt.now()))

        try:
            # Connect to org/portal
            gis = arcgis.gis.GIS(orgUrl, username, password)

            # Get token for CW
            status = get_cw_token()

            if 'error' in status:
                log.write('Failed to get Cityworks token. {}\n'.format(status))
                raise Exception('Failed to get Cityworks token.  {}'.format(status))

            # get wkid
            sr = get_wkid()

            if sr == 'error':
                log.write('Spatial reference not defined\n')
                raise Exception('Spatial reference not defined')

            # get problem types
            prob_types = get_problem_types()

            if prob_types == 'error':
                log.write('Problem types not defined\n')
                raise Exception('Problem types not defined')

            # connect to reporting services
            for service, reltable in services:
                lyr = arcgis.features.FeatureLayer(service, gis=gis)
                oid_fld = lyr.properties.objectIdField

                # query reports
                sql = "{}='{}'".format(fc_flag, flag_values[0])
                rows = lyr.query(where=sql, out_sr=sr)
                updated_rows = []

                for row in rows.features:
                    oid = row.attributes[oid_fld]
                    print(oid)

                    # Submit feature to the Cityworks database
                    print('submitting to cw')
                    requestid = submit_to_cw(row, prob_types)

                    try:
                        if 'WARNING' in requestid:
                            print(requestid)
                            log.write(requestid)
                            continue
                        else:
                            pass  # requestID is str = ok
                    except TypeError:
                        pass  # requestID is a number = ok

                    # attachments
                    print('adding attachments')
                    response = copy_attachment(lyr, oid, requestid)

                    # update the record in the service so that it evaluates falsely against sql
                    print('updating service')
                    row.attributes[fc_flag] = flag_values[1]
                    try:
                        row.attributes[fc_reportid] = requestid
                    except TypeError:
                        row.attributes[fc_reportid] = str(requestid)

                    updated_rows.append(row)

                # apply edits to updated features
                if updated_rows:
                    lyr.edit_features(updates=updated_rows)

                # related records
                rellyr = arcgis.features.FeatureLayer(reltable, gis=gis)

                pkey_fld = lyr.properties.relationships[0]['keyField']
                fkey_fld = rellyr.properties.relationships[0]['keyField']
                sql = "{} IS NULL".format(fc_flag, None)
                rel_records = rellyr.query(where=sql)
                updated_rows = []
                for record in rel_records:
                    print('updating related records')
                    response = copy_comments(lyr, pkey_fld, record, fkey_fld)
                    if response:
                        record.attributes[fc_flag] = flag_values[1]

                        updated_rows.append(record)

                # apply edits to updated records
                if updated_rows:
                    rellyr.edit_features(updates=updated_rows)

                print('Done')

        except Exception as ex:
            print('error: ' + str(ex))


if __name__ == '__main__':
    main()
