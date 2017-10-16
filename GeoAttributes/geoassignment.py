# ------------------------------------------------------------------------------
# Name:        geoassignment.py
# Purpose:     to populate attributes on a feature based on attributes of a coincident features
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

from datetime import datetime as dt
from os import path, sys
from arcgis.gis import GIS
from arcgis.features import FeatureLayer

orgURL = ''     # URL to ArcGIS Online organization or ArcGIS Portal
username = ''   # Username of an accoun in the org/portal that can access and edit all services listed below
password = ''   # Password corresponding to the username provided above


# Specify services/layers to process and the content that wil be used to enrich them

# [
#    {'url': 'URL of an editable feature service/layer that is to be enriched',
#     'enrichment layers':[{'url':'URL of the highest-priority polygon layer to be used to enrich the layer listed above',
#                          'query': 'SQL query used to idenetify which features in this layer should be enriched by this polygon layer',
#                          'source field': 'Field in the polygon layer containing values to be copied to any intersecting input features',
#                          'target field': 'Field in the input layer into which values will be copied from the intersecting polygon feature'},
#
#                         {'url':'URL of the SECOND highest-priority polygon layer to be used to enrich the layer listed above',
#                          'query': 'Additional enrichment layers can be added by adding additional copies of this block',
#                          'source field': '',
#                          'target field': ''}
#                         ]
#     },
#
#    {'url': 'URL of a SECOND editable feature service/layer that is to be enriched.',
#     'enrichment layers':[{'url':'',
#                          'query': '',
#                          'source field': '',
#                          'target field': ''},
#
#                         {'url':'',
#                          'query': '',
#                          'source field': '',
#                          'target field': ''},
#
#                         {'url':'',
#                          'query': '',
#                          'source field': '',
#                          'target field': ''}
#                         ]
#     }
# ]

services = [
    {'url': '',
     'enrichment layers': [{'url':'',
                            'query': '',
                            'source field': '',
                            'target field': ''}]
    }]


def main():
    # Create log file
    with open(path.join(sys.path[0], 'attr_log.log'), 'a') as log:
        log.write('\n{}\n'.format(dt.now()))

        # connect to org/portal
        gis = GIS(orgURL, username, password)

        for service in services:
            try:
                # Connect to target layer
                fl = FeatureLayer(service['url'], gis)
                fl_fields = [field['name'] for field in fl.properties.fields]

                # get wkid of target layer for spatial queries
                wkid = fl.properties.extent.spatialReference.wkid

                for reflayer in reversed(service['enrichment layers']):  # reversed so the top llayer is processed last
                    # Connect to source layer
                    polyfeats = FeatureLayer(reflayer['url'], gis)

                    # test that source and target fields exist in source and target layers
                    poly_fields = [field['name'] for field in polyfeats.properties.fields]
                    if not reflayer['source field'] in poly_fields:
                        raise Exception(
                            'Source field {} not found in layer {}'.format(reflayer['source field'], reflayer['url']))

                    if not reflayer['target field'] in fl_fields:
                        raise Exception(
                            'Target field {} not found in layer {}'.format(reflayer['target field'], service['url']))

                    # Query for target features
                    try:
                        rows = fl.query(reflayer['query'])
                    except:
                        raise Exception('Failed to execute query {}. Please verify the syntax. Layer: {}'.format(reflayer['query'], service['url']))

                    for feat in rows:
                        # Perform spatial query to get attributes of intersecting feature
                        ptgeom = {'geometry': feat.geometry,
                                  'spatialRel': 'esriSpatialRelIntersects',
                                  'geometryType': 'esriGeometryPoint',
                                  'inSR': wkid
                                  }
                        poly = polyfeats.query(geometry_filter=ptgeom)

                        try:
                            # Only first feature is processed
                            source_val = poly.features[0].attributes[reflayer['source field']]
                            feat.attributes[reflayer['target field']] = source_val
                        except IndexError:
                            continue  # no intersecting feature found

                    results = fl.edit_features(updates=rows)

                    for result in results['updateResults']:
                        if not result['success']:
                            raise Exception('error {}: {}'.format(result['error']['code'],
                                                                  result['error']['description']))
            except Exception as ex:
                msg = 'Failed to enrich layer {}'.format(service['url'])
                print(ex)
                print(msg)
                log.write('{}\n{}\n'.format(msg, ex))


if __name__ == '__main__':
    main()
