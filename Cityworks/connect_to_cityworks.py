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

from arcgis.gis import GIS, Group, Layer
from arcgis.features import FeatureLayer, Table
from arcgis.features.managers import AttachmentManager

import configparser
import json
import six
from os import path, sys, remove
from datetime import datetime as dt

cityworksfields = ['RequestId', 'DomainId', 'ProjectSid', 'ProblemCode', 'Details', 'ReqCategory', 'Description', 'Priority', 'ProblemSid', 'ReqCustFieldCatId', 'ProbAddress', 'ProbCity', 'ProbZip', 'ProbAddType', 'InitiatedBy', 'ProjectName', 'ProbAptNum', 'ProbLandmark', 'ProbDistrict', 'ProbState', 'ProbLocation', 'InitiatedByApp']

layer_fields = []
table_fields = []
groupid = ''
agol_user = ''
agol_pass = ''
agol_org = ''
layer_list = ''
table_list = ''
gis = ''
flag_field = ''
cw_token = ""
baseUrl = ""

def get_response(url):
    http_response = six.moves.urllib.request.urlopen(url)
    decoded = http_response.read().decode('utf-8')

    return json.loads(decoded.strip())


def get_cw_token(user, pwd):
    """Retrieve a token for CityWorks access"""
    data = {"LoginName": user, "Password": pwd}
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


def submit_to_cw(row, prob_types, fields, oid, typefields):

    attrs = row.attributes
    geometry = row.geometry

    try:
        prob_sid = prob_types[attrs[typefields[1]].upper()]

    except KeyError:
        if attrs[typefields[1]].strip() == '':
            return 'WARNING: No problem type provided. Record {} not exported.\n'.format(oid)
        else:
            return 'WARNING: Problem type {} not found in Cityworks. Record {} not exported.\n'.format(attrs[typefields[1]], oid)

    except AttributeError:
        return 'WARNING: Record {} not exported due to missing value in field {}\n'.format(oid, typefields[1])

    # Build dictionary of values to submit to CW
    values = {}
    for fieldset in fields:
        c_field, a_field = fieldset
        values[c_field] = str(attrs[a_field])
    values["X"] = geometry['x']
    values["Y"] = geometry['y']
    values[typefields[0]] = prob_sid

    # Convert dict to pretty print json
    json_data = six.moves.urllib.parse.quote(json.dumps(values, separators=(',', ':')))

    # Submit report to CityWorks. Encode chars
    url = '{}/Services/AMS/ServiceRequest/Create?data={}&token={}'.format(baseUrl, json_data, cw_token)
    response = get_response(url)

    return response['Value']['RequestId']


def copy_attachment(lyr, oid, requestid):

    attachmentmgr = AttachmentManager(lyr)
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


def copy_comments(lyr, pkey_fld, record, fkey_fld, fields, ids):

    try:
        sql = "{} = '{}'".format(pkey_fld, record.attributes[fkey_fld])
        parents = lyr.query(where=sql)

    except Exception:
        sql = "{} = '{}'".format(pkey_fld, record.attributes[fkey_fld])
        parents = lyr.query(where=sql)

    parent = parents.features[0]
    if not parent.attributes[ids[1]]:
        return ""

    values = {id_fields[0]: parent.attributes[ids[1]]}
    for field in fields:
        values[field[0]] = record.attributes[field[1]]

    json_data = six.moves.urllib.parse.quote(json.dumps(values, separators=(',', ':')))
    url = '{}/Services/AMS/CustomerCall/AddToRequest?data={}&token={}'.format(baseUrl, json_data, cw_token)
    response = get_response(url)

    return response


def main(cwUser, cwPwd, orgUrl, username, password, layers, tables, layerfields, tablefields, fc_flag, flag_values, ids, probtypes):

    id_log = path.join(sys.path[0], 'cityworks_log.log')
    with open(id_log, 'a') as log:
        log.write('\n\n{}\n'.format(dt.now()))

        try:
            # Connect to org/portal
            gis = GIS(orgUrl, username, password)

            # Get token for CW
            status = get_cw_token(cwUser, cwPwd)


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

            for layer in layers:
                lyr = FeatureLayer(layer, gis=gis)
                oid_fld = lyr.properties.objectIdField

                # Get related table URL
                reltable = ''
                for relate in lyr.properties.relationships:
                    url_pieces = layer.split('/')
                    url_pieces[-1] = str(relate['relatedTableId'])
                    table_url = '/'.join(url_pieces)

                    if table_url in tables:
                        reltable = table_url
                        break

                # query reports
                sql = "{}='{}'".format(fc_flag, flag_values[0])
                rows = lyr.query(where=sql, out_sr=sr)
                updated_rows = []

                for row in rows.features:
                    oid = row.attributes[oid_fld]
                    print(oid)

                    # Submit feature to the Cityworks database
                    requestid = submit_to_cw(row, prob_types, layerfields, oid, probtypes)

                    try:
                        if 'WARNING' in requestid:
                            log.write('Warning generated while copying record to Cityworks: {}\n'.format(requestid))
                            continue
                        else:
                            pass  # requestID is str = ok
                    except TypeError:
                        pass  # requestID is a number = ok

                    # attachments
                    # response = copy_attachment(lyr, oid, requestid)
                    # print(response)

                    # update the record in the service so that it evaluates falsely against sql
                    row.attributes[fc_flag] = flag_values[1]
                    try:
                        row.attributes[ids[1]] = requestid
                    except TypeError:
                        row.attributes[ids[1]] = str(requestid)

                    updated_rows.append(row)

                # apply edits to updated features
                if updated_rows:
                    status = lyr.edit_features(updates=updated_rows)
                    log.write('Status of updates to ArcGIS layers: {}\n'.format(status))

                # related records
                rellyr = FeatureLayer(reltable, gis=gis)

                pkey_fld = lyr.properties.relationships[0]['keyField']
                fkey_fld = rellyr.properties.relationships[0]['keyField']
                sql = "{} IS NULL".format(fc_flag, None)
                rel_records = rellyr.query(where=sql)
                updated_rows = []
                for record in rel_records:
                    response = copy_comments(lyr, pkey_fld, record, fkey_fld, tablefields, ids)
                    if response:
                        record.attributes[fc_flag] = flag_values[1]
                        log.write('Status of updates to Cityworks comments: {}\n'.format(response))
                        updated_rows.append(record)

                # apply edits to updated records
                if updated_rows:
                    status = rellyr.edit_features(updates=updated_rows)
                    log.write('Status of updates to ArcGIS comments: {}\n'.format(status))

                print('Done')

        except Exception as ex:
            print('error: ' + str(ex))


if __name__ == '__main__':
    configfile = r'C:\Users\alli6394\Desktop\arcgis_cw_config.ini'

    config = configparser.ConfigParser()
    config.read(configfile)

    # Cityworks settings
    global baseUrl
    baseUrl = config['cityworks']['url']
    cwUser = config['cityworks']['username']
    cwPwd = config['cityworks']['password']

    # ArcGIS Online/Portal settings
    orgUrl = config['arcgis']['url']
    username = config['arcgis']['username']
    password = config['arcgis']['password']
    # proxy_port = None
    # proxy_url = None
    layers = [url for url in config['arcgis']['layers'].split(',')]
    tables = [url for url in config['arcgis']['tables'].split(',')]
    layerfields = [pair.split(',') for pair in config['fields']['layers'].split(';')]
    tablefields = [pair.split(',') for pair in config['fields']['tables'].split(';')]
    fc_flag = config['flag']['field']
    flag_values = [config['flag']['on'], config['flag']['off']]
    id_fields = [field for field in config['fields']['ids'].split(',')]
    probtypes = [field for field in config['fields']['type'].split(',')]
    main(cwUser, cwPwd, orgUrl, username, password, layers, tables, layerfields, tablefields, fc_flag, flag_values, id_fields, probtypes)