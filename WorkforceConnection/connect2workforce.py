# ------------------------------------------------------------------------------
# Name:        connect2workforce.py
# Purpose:     generates identifiers for features

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

from datetime import datetime as dt
from os import path, sys
from arcgis.gis import GIS
from arcgis.features import FeatureLayer

orgURL = ''     # URL to ArcGIS Online organization or ArcGIS Portal
username = ''   # Username of an account in the org/portal that can access and edit all services listed below
password = ''   # Password corresponding to the username provided above

# Specify the services/ layers to monitor for reports to pass to Workforce
# [{'source url': 'Reporter layer to monitor for new reports',
#              'target url': 'Workforce layer where new assignments will be created base on the new reports',
#              'query': 'SQL query used to identify the new reports that should be copied',
#              'fields': {
#                  'Name of Reporter field': 'Name of Workforce field',
#                  'Another Reporter field to map':'to another workforce field'},
#              'update field': 'Name of field in Reporter layer tracking which reports have  been copied to Workforce',
#              'update value': 'Value in update field indicating that a report has already been copied.'
#              },
# {'source url': 'Another Reporter layer to monitor for new reports',
#              'target url': '',
#              'query': '',
#              'fields': {},
#              'update field': '',
#              'update value': ''
#              }]

services = [{'source url': '',
             'target url': '',
             'query': '1=1',
             'fields': {
                 '': ''},
             'update field': '',
             'update value': ''
             }]

def main():
    # Create log file
    with open(path.join(sys.path[0], 'attr_log.log'), 'a') as log:
        log.write('\n{}\n'.format(dt.now()))

        # connect to org/portal
        gis = GIS(orgURL, username, password)

        for service in services:
            try:
                # Connect to source and target layers
                fl_source = FeatureLayer(service['source url'], gis)
                fl_target = FeatureLayer(service['target url'], gis)

                # get field map
                fields = [[key, service['fields'][key]] for key in service['fields'].keys()]

                # Get source rows to copy
                rows = fl_source.query(service['query'])
                adds = []
                updates = []

                for row in rows:
                    # Build dictionary of attributes & geometry in schema of target layer
                    # Default status and priority values can be overwritten if those fields are mapped to reporter layer
                    attributes = {'status': 0,
                                  'priority': 0}

                    for field in fields:
                        attributes[field[1]] = row.attributes[field[0]]

                    new_request = {'attributes': attributes,
                                   'geometry': {'x': row.geometry['x'],
                                                'y': row.geometry['y']}}
                    adds.append(new_request)

                    # update row to indicate record has been copied
                    if service['update field']:
                        row.attributes[service['update field']] = service['update value']
                        updates.append(row)

                # add records to target layer
                if adds:
                    add_result = fl_target.edit_features(adds=adds)
                    for result in add_result['updateResults']:
                        if not result['success']:
                            raise Exception('error {}: {}'.format(result['error']['code'],
                                                                  result['error']['description']))

                # update records:
                if updates:
                    update_result = fl_source.edit_features(updates=updates)
                    for result in update_result['updateResults']:
                        if not result['success']:
                            raise Exception('error {}: {}'.format(result['error']['code'],
                                                                  result['error']['description']))

            except Exception as ex:
                msg = 'Failed to copy feature from layer {}'.format(service['url'])
                print(ex)
                print(msg)
                log.write('{}\n{}\n'.format(msg, ex))

if __name__ == '__main__':
    main()
