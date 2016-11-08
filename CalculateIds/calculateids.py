# ------------------------------------------------------------------------------
# Name:        calculateids.py
# Purpose:     generates identifiers for features

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
from os import path, sys
from datetime import datetime as dt

# Data Store
server_type = "AGOL"  # "PORTAL", "SERVER"

# Credentials for AGOL/Portal
orgURL = ''
username = ''
password = ''

# Services/feature classes to update
#   data path: REST endpoint of AGOL/Portal service layer (including index
#       number), or feature class path. Add r to the front of feature class path.
#   field name: Name of field to contain identifier
#   sequence name: the name of the sequence to use. This should correspond to
#       the first value of a line in the ids.csv file
#   pattern: the identifier sequence, with the section to increment marked
#       with {}. Python string formatting applies within the {}. For example,
#       use {:04d}'to pad the incrementing value with 4 zeros.
data = [{'data path': '',
         'field name': '',
         'sequence name': '',
         'pattern': ''},

         {'data path': '',
         'field name': '',
         'sequence name': '',
         'pattern': ''}]

if server_type in ['AGOL', 'Portal']:

    from arcresthelper import securityhandlerhelper
    from arcrest.agol import FeatureLayer

else:
    import arcpy

# Path to file use to track the identifiers. First line is headers
#   one identifier per line with the following comma separated values:
#       the name of the id value,
#       the interval to use to increment the values,
#       the id value that will be used for the next feature
id_file_path = path.join(path.dirname(sys.argv[0]), 'ids.csv')


def read_values(f):
    """Read in the settings from the csv file and
    return the same in list format"""

    with open(f, 'r') as f_open:
        values = {}
        f_content = f_open.read()
        f_lines = f_content.split('\n')
        for category in f_lines[1:]:
            if category:
                cat, intvl, num = category.split(',')
                if cat:
                    try:
                        values[cat] = [int(intvl), int(num)]
                    except TypeError, ValueError:
                        return 'Could not find a category name, interval, and sequence value in {}.'.format(category)
    return f_lines[0], values


def update_agol(url, fld, sequence_value, interval, seq_format='{}'):
    """Update fetures in an agol/portal service with id values
    Return next valid sequence value"""

    # Connect to org
    securityinfo = {}
    securityinfo['security_type'] = 'Portal'  # LDAP, NTLM, OAuth, Portal, PKI, ArcGIS
    securityinfo['username'] = username
    securityinfo['password'] = password
    securityinfo['org_url'] = orgURL
    securityinfo['proxy_url'] = None
    securityinfo['proxy_port'] = None
    securityinfo['referer_url'] = None
    securityinfo['token_url'] = None
    securityinfo['certificatefile'] = None
    securityinfo['keyfile'] = None
    securityinfo['client_id'] = None
    securityinfo['secret_id'] = None

    shh = securityhandlerhelper.securityhandlerhelper(securityinfo=securityinfo)

    if not shh.valid:
        return 'Could not connect to {}. Please verify paths and credentials.'.format(url)

    fl = FeatureLayer(url=url,
                      securityHandler=shh.securityhandler,
                      proxy_port=None,
                      proxy_url=None,
                      initialize=True)

    # Build SQL query to find features missing id
    sql = """{} is null""".format(fld)

    out_fields = ['objectid', fld]

    # Get features without id
    resFeats = fl.query(where=sql, out_fields=','.join(out_fields))

    # For each feature
    for feat in resFeats:
        id_value = seq_format.format(sequence_value)

        # Update id
        feat.set_value(fld, id_value)

        # Increment sequence value
        sequence_value += interval

    update_results = fl.updateFeature(features=resFeats)

    for res in update_results['updateResults']:
        if res['success'] == False:
            return 'error {}: {}'.format(res['error']['code'], res['error']['description'])

    return sequence_value


def update_fc(data_path, fld, sequence_value, interval, seq_format='{}'):
    """Update fetures in a server service with id values
    Return next valid sequence value"""

    # Get workspace of fc
    dirname = path.dirname(arcpy.Describe(data_path).catalogPath)
    desc = arcpy.Describe(dirname)
    if hasattr(desc, "datasetType") and desc.datasetType == 'FeatureDataset':
        dirname = path.dirname(dirname)

    # Start edit session
    edit = arcpy.da.Editor(dirname)
    edit.startEditing(False, True)
    edit.startOperation()

    # find and update all features that need ids
    sql = """{} is null""".format(fld)
    with arcpy.da.UpdateCursor(data_path, fld, where_clause=sql) as fcrows:

        for row in fcrows:

            # Calculate a new id value from a string and the current id value
            row[0] = seq_format.format(sequence_value)

            try:

                fcrows.updateRow(row)

            except RuntimeError:
                return 'error: The value type is incompatible with the field type. [{}]'.format(fld)

            # increment the sequence value by the specified interval
            sequence_value += interval

    return sequence_value


def main():

    id_log = path.join(sys.path[0], 'id_log.log')
    with open(id_log, 'a') as log:
        log.write('\n{}\n'.format(dt.now()))

        try:
            # Get all id settings
            header, id_settings = read_values(id_file_path)

            if not isinstance(id_settings, dict):
                raise Exception(id_settings)

            for d in data:
                data_path = d['data path']
                id_field = d['field name']
                inc_type = d['sequence name']
                seq_format = d['pattern']

                # Get settings for current category
                try:
                    interval, sequence_value = id_settings[inc_type]

                except KeyError:
                    raise Exception('Specified sequence name not found')

                # Assign ids to features
                if server_type == 'AGOL' or server_type == 'PORTAL':
                    new_sequence_value = update_agol(data_path,
                                                     id_field,
                                                     sequence_value,
                                                     interval,
                                                     seq_format)

                elif server_type == 'SERVER':
                    new_sequence_value = update_fc(data_path,
                                                   id_field,
                                                   sequence_value,
                                                   interval,
                                                   seq_format)


                # handle errors writing values to fields
                if type(new_sequence_value) == str:
                    raise Exception(new_sequence_value)

                # Update the settings with the latest sequence values
                elif sequence_value != new_sequence_value:

                    # Look for error messages
                    if not isinstance(new_sequence_value, (int, float)):
                        raise Exception(new_sequence_value)

                    # update stored sequence value
                    id_settings[inc_type][1] = new_sequence_value

            # Save updated settings to file
            new_settings = header

            for vals in id_settings:
                id_settings[vals].insert(0, vals)
                new_settings += "\n{}".format(','.join([str(v) for v in id_settings[vals]]))

            with open(id_file_path, 'w') as f:
                f.writelines(new_settings)

        except Exception as ex:
            print(ex)
            log.write('{}\n'.format(ex))

if __name__ == '__main__':
    main()
