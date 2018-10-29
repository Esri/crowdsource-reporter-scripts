# ------------------------------------------------------------------------------
# Name:        connect_to_cityworks.pyt
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

import arcpy
from arcgis.gis import GIS, Group, Layer
from arcgis.mapping import WebMap
from arcgis.features import FeatureLayer, Table

import json
from pytz import common_timezones

timezones = common_timezones
cityworksfields = ['AcctNum', 'Address', 'Answers', 'AptNum', 'CallerAcctNum', 'CallerAddress', 'CallerAptNum', 'CallerCallTime', 'CallerCellPhone', 'CallerCity', 'CallerComments', 'CallerDistrict', 'CallerEmail', 'CallerFax', 'CallerFirstName', 'CallerHomePhone', 'CallerIsFollowUpCall', 'CallerIsOwner', 'CallerLastName', 'CallerMiddleInitial', 'CallerOtherPhone', 'CallerState', 'CallerText1', 'CallerText2', 'CallerText3', 'CallerText4', 'CallerText5', 'CallerTitle', 'CallerType', 'CallerWorkPhone', 'CallerZip', 'Cancel', 'CancelReason', 'CancelledBy', 'CancelledBySid', 'Ccx', 'Ccy', 'CellPhone', 'City', 'ClosedBy', 'ClosedBySid', 'Comments', 'CustAddType', 'CustAddress', 'CustCallback', 'CustCity', 'CustContact', 'CustDistrict', 'CustState', 'CustZip', 'CustomFieldValues', 'Date1', 'Date2', 'Date3', 'Date4', 'Date5', 'DateCancelled', 'DateDispatchOpen', 'DateDispatchTo', 'DateInvtDone', 'DateSubmitTo', 'DateSubmitToOpen', 'DateTimeCall', 'DateTimeCallback', 'DateTimeClosed', 'DateTimeContact', 'DateTimeInit', 'Description', 'Details', 'DispatchOpenBy', 'DispatchOpenBySid', 'DispatchTo', 'DispatchToSid', 'DispatchToUseDispatchToSid', 'District', 'DomainId', 'Effort', 'Email', 'EmployeeSid', 'Excursion', 'Fax', 'FieldInvtDone', 'FirstName', 'HomePhone', 'InitiatedBy', 'InitiatedByApp', 'InitiatedBySid', 'IsClosed', 'IsFollowUpCall', 'IsResident', 'LaborCost', 'Landmark', 'LastName', 'Location', 'LockedByDesktopUser', 'MapPage', 'MiddleInitial', 'Num1', 'Num2', 'Num3', 'Num4', 'Num5', 'OtherPhone', 'OtherSystemCode', 'OtherSystemDesc', 'OtherSystemDesc2', 'OtherSystemId', 'OtherSystemStatus', 'Priority', 'PrjCompleteDate', 'ProbAddType', 'ProbAddress', 'ProbAptNum', 'ProbCity', 'ProbDetails', 'ProbDistrict', 'ProbLandmark', 'ProbLocation', 'ProbState', 'ProbZip', 'ProblemCode', 'ProblemSid', 'ProjectName', 'ProjectSid', 'ReqCategory', 'ReqCustFieldCatId', 'RequestId', 'Resolution', 'SRX', 'SRY', 'Shop', 'State', 'Status', 'StreetName', 'SubmitTo', 'SubmitToEmail', 'SubmitToOpenBy', 'SubmitToOpenBySid', 'SubmitToPager', 'SubmitToPhone', 'SubmitToSid', 'SubmitToUseSubmitToSid', 'Text1', 'Text10', 'Text11', 'Text12', 'Text13', 'Text14', 'Text15', 'Text16', 'Text17', 'Text18', 'Text19', 'Text2', 'Text20', 'Text3', 'Text4', 'Text5', 'Text6', 'Text7', 'Text8', 'Text9', 'TileNo', 'Title', 'WONeeded', 'WorkOrderId', 'WorkPhone', 'X', 'Y', 'Zip']

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


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Tool"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        cw_url = arcpy.Parameter(
            displayName="Cityworks URL",
            name="cityworks_url",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        cw_user = arcpy.Parameter(
            displayName="Cityworks Username",
            name="cityworks_user",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        cw_pw = arcpy.Parameter(
            displayName="Cityworks Password",
            name="cityworks_password",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        cw_timezone = arcpy.Parameter(
            displayName="Timezone of the Cityworks server",
            name="cw_timezone",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        cw_cwol = arcpy.Parameter(
            displayName="Cityworks Online Site?",
            name="cityworks_cwol",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input"
        )
        portal_url = arcpy.Parameter(
            displayName="ArcGIS URL",
            name="portal_url",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        portal_user = arcpy.Parameter(
            displayName="ArcGIS Username",
            name="portal_user",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        portal_pw = arcpy.Parameter(
            displayName="ArcGIS Password",
            name="portal_password",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        group = arcpy.Parameter(
            displayName="Reporter Group",
            name="group",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        flayers = arcpy.Parameter(
            displayName="Layers",
            name="layers",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True
        )
        ftables = arcpy.Parameter(
            displayName="Tables",
            name="tables",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True
        )
        cw_id = arcpy.Parameter(
            displayName="Cityworks Report ID Field",
            name="cw_id",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        report_id = arcpy.Parameter(
            displayName="ArcGIS Report ID Field",
            name="report_id",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        cw_probtype = arcpy.Parameter(
            displayName="Cityworks Report Type Field",
            name="cw_probtype",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        report_type = arcpy.Parameter(
            displayName="ArcGIS Report Type Field",
            name="report_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        cw_opendate = arcpy.Parameter(
            displayName="Cityworks Open Date Field",
            name="cw_opendate",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        report_opendate = arcpy.Parameter(
            displayName="ArcGIS Open Date Field",
            name="report_opendate",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        fl_flds = arcpy.Parameter(
            displayName="Report Layer Field Map",
            name="feature_fields",
            datatype="GPValueTable",
            parameterType="Required",
            direction="Input"
        )
        tb_flds = arcpy.Parameter(
            displayName="Comment Table Field Map",
            name="comment_fields",
            datatype="GPValueTable",
            parameterType="Optional",
            direction="Input"
        )
        flag_fld = arcpy.Parameter(
            displayName="Flag Field",
            name="flag_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        flag_on = arcpy.Parameter(
            displayName="Flag On Value",
            name="flag_on",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        flag_off = arcpy.Parameter(
            displayName="Flag Off Value",
            name="flag_off",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        config_path = arcpy.Parameter(
            displayName="Save a Configuration File",
            name="configuration_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output"
        )

        cw_cwol.value = False

        group.filter.type = 'ValueList'
        group.filter.list = ['Provide ArcGIS credentials to see group list']

        fl_flds.columns = [['GPString', 'ArcGIS Field'], ['GPString', 'Cityworks Field']]
        fl_flds.filters[1].type = 'ValueList'
        fl_flds.filters[1].list = cityworksfields
        fl_flds.filters[0].type = 'ValueList'
        fl_flds.filters[0].list = ['Provide credentials and select a group to see field list']

        flag_fld.filter.type = 'ValueList'
        flag_fld.filter.list = ['Provide credentials and select a group to see field list']

        tb_flds.columns = [['GPString', 'ArcGIS Field'], ['GPString', 'Cityworks Field']]
        tb_flds.filters[1].type = 'ValueList'
        tb_flds.filters[1].list = cityworksfields
        tb_flds.filters[0].type = 'ValueList'
        tb_flds.filters[0].list = ['1', '2']

        flayers.filter.type = 'ValueList'
        flayers.filter.list = ['Provide credentials and select a group to see field list']

        ftables.filter.type = 'ValueList'
        ftables.filter.list = ['Provide credentials and select a group to see table list']

        cw_id.filter.type = 'ValueList'
        cw_id.filter.list = cityworksfields

        report_id.filter.type = 'ValueList'
        report_id.filter.list = ['Select layers to see field list']

        cw_probtype.filter.type = 'ValueList'
        cw_probtype.filter.list = cityworksfields

        report_type.filter.type = 'ValueList'
        report_type.filter.list = ['Select layers to see field list']

        cw_opendate.filter.type = 'ValueList'
        cw_opendate.filter.list = cityworksfields

        report_opendate.filter.type = 'ValueList'
        report_opendate.filter.list = ['Select layers to see field list']

        cw_timezone.filter.type = 'ValueList'
        cw_timezone.filter.list = timezones

        params = [portal_url, portal_user, portal_pw, cw_url, cw_user, cw_pw, cw_timezone, cw_cwol, group, flayers, cw_id, report_id,
                  cw_probtype, report_type, cw_opendate, report_opendate, flag_fld, flag_on, flag_off, fl_flds, ftables, tb_flds, config_path]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        portal_url, portal_user, portal_pw, cw_url, cw_user, cw_pw, cw_timezone, cw_cwol, group, flayers, cw_id, report_id, cw_probtype, report_type, cw_opendate, report_opendate, flag_fld, flag_on, flag_off, fl_flds, ftables, tb_flds, config_path = parameters

        global agol_user
        global agol_pass
        global agol_org
        global groupid
        global layer_list
        global table_list
        global layer_fields
        global table_fields
        global gis
        global flag_field

        # Get list of groups available to the user
        if not portal_url.value or not portal_pw.value or not portal_user.value:  # or not cw_url.value or not cw_pw.value or not cw_user.value:
            group.value = ''
            group.enabled = False
            agol_org = ''
            agol_pass = ''
            agol_user = ''

        elif portal_url.valueAsText != agol_org or portal_pw.valueAsText != agol_pass or portal_user.valueAsText != agol_user:
            group.enabled = True

            agol_org = portal_url.valueAsText
            agol_pass = portal_pw.valueAsText
            agol_user = portal_user.valueAsText

            gis = GIS(agol_org, agol_user, agol_pass)
            group.filter.list = ['{} ({})'.format(group.title, group.id) for group in gis.groups.search()]

        # Get list of layers in all maps shared with the group
        if not group.value:
            flayers.value = []
            flayers.enabled = False
            ftables.value = []
            ftables.enabled = False
            groupid = ''

        elif group.valueAsText != groupid:
            flayers.enabled = True
            ftables.enabled = True

            groupid = group.valueAsText
            layer_urls = []
            table_urls = []

            # Get group
            agolgroup = Group(gis, groupid.split(' ')[-1][1:-1])

            # Get maps in group
            maps = [item for item in agolgroup.content() if item.type == 'Web Map']

            for mapitem in maps:
                webmap = WebMap(mapitem)

                for layer in webmap.definition['operationalLayers']:
                    lyr = FeatureLayer(layer['url'], gis)

                    if 'Create' in lyr.properties.capabilities:  # Reports layer must have 'create' capabilities
                        try:
                            for field in layer['popupInfo']['fieldInfos']:
                                # reports layer must have at least one editable field
                                if field['isEditable'] and 'relationships/' not in field['fieldName']:
                                    layer_urls.append('{} ({})'.format(lyr.properties.name, layer['url']))
                                    break

                        except KeyError:
                            pass  # if no popup, layer can't be reports layer

                try:
                    for table in webmap.definition['tables']:
                        tab = Table(table['url'], gis)

                        for field in table['popupInfo']['fieldInfos']:
                            if field['isEditable'] and 'relationships/' not in field['fieldName']:
                                # comment table must have at least one editable field
                                table_urls.append('{} ({})'.format(tab.properties.name, table['url']))
                                break

                except KeyError:
                    pass  # if no table/popup, no comments layer

            layer_urls = list(set(layer_urls))
            if len(table_urls) > 0:
                table_urls = list(set(table_urls))
            flayers.filter.list = layer_urls
            flayers.value = layer_urls
            ftables.filter.list = table_urls
            ftables.value = table_urls

        # If layers are changed
        if not flayers.value:
            layer_list = ''
            flag_field = ''
            cw_id.filter.list = []
            cw_id.value = ''
            cw_id.enabled = False
            report_id.value = ''
            report_id.filter.list = []
            report_id.enabled = False
            cw_probtype.value = ''
            cw_probtype.filter.list = []
            cw_probtype.enabled = False
            report_type.value = ''
            report_type.filter.list = []
            report_type.enabled = False
            cw_opendate.value = ''
            cw_opendate.filter.list = []
            cw_opendate.enabled = False
            report_opendate.value = ''
            report_opendate.filter.list = []
            report_opendate.enabled = False
            flag_fld.value = ''
            flag_fld.filter.list = []
            flag_fld.enabled = False
            flag_on.value = ''
            flag_on.filter.list = []
            flag_on.enabled = False
            flag_off.value = ''
            flag_off.filter.list = []
            flag_off.enabled = False
            fl_flds.filters[0].list = ['Provide credentials and select a group to see field list']
            fl_flds.value = ''
            fl_flds.enabled = False
            flag_fld.filter.list = table_fields

        elif flayers.valueAsText != layer_list:
            cw_id.enabled = True
            report_id.enabled = True
            cw_probtype.enabled = True
            report_type.enabled = True
            cw_opendate.enabled = True
            report_opendate.enabled = True
            flag_fld.enabled = True
            flag_on.enabled = True
            flag_off.enabled = True
            fl_flds.enabled = True

            layer_fields = []
            layer_list = flayers.valueAsText

            # If layers are updated
            services = [item.split(' ')[-1][1:-2] for item in str(flayers.value).split(';')]

            for url in services:
                lyr = FeatureLayer(url, gis)
                new_fields = [field['name'] for field in lyr.properties.fields]

                if layer_fields:
                    layer_fields = list(set(new_fields) & set(layer_fields))
                else:
                    layer_fields = new_fields

            fl_flds.filters[0].list = layer_fields
            report_id.filter.list = layer_fields
            report_type.filter.list = layer_fields
            report_opendate.filter.list = layer_fields

            if 'RequestId' in cityworksfields:
                cw_id.value = 'RequestId'
            if 'ProblemSid' in cityworksfields:
                cw_probtype.value = 'ProblemSid'
            if 'DateTimeInit' in cityworksfields:
                cw_opendate.value = 'DateTimeInit'

            if 'REPORTID' in layer_fields:
                report_id.value = 'REPORTID'
            if 'PROBTYPE' in layer_fields:
                report_type.value = 'PROBTYPE'
            if 'submitdt' in layer_fields:
                report_opendate.value = 'submitdt'

            if ftables.value:
                flag_fld.filter.list = list(set(layer_fields) & set(table_fields))
            else:
                flag_fld.filter.list = layer_fields

        # If tables are changed
        if not ftables.value:
            tb_flds.enabled = False
            table_fields = []

        elif ftables.valueAsText != table_list:
            tb_flds.enabled = True
            table_fields = []
            table_list = ftables.valueAsText
            flag_fld.filter.list = layer_fields

            services = [item.split(' ')[-1][1:-2] for item in str(ftables.value).split(';')]

            for url in services:
                tab = FeatureLayer(url, gis)
                new_fields = [field['name'] for field in tab.properties.fields]

                if table_fields:
                    table_fields = list(set(new_fields) & set(table_fields))
                else:
                    table_fields = new_fields

                tb_flds.filters[0].list = table_fields

            if flayers.value:
                flag_fld.filter.list = list(set(table_fields) & set(layer_fields))
            else:
                flag_fld.filter.list = table_fields

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        portal_url, portal_user, portal_pw, cw_url, cw_user, cw_pw, cw_timezone, cw_cwol, group, flayers, cw_id, report_id, cw_probtype, report_type, cw_opendate, report_opendate, flag_fld, flag_on, flag_off, fl_flds, ftables, tb_flds, config_path = parameters

        layer_urls = [item.split(' ')[-1][1:-2] for item in str(flayers.value).split(';')]
        table_urls = [item.split(' ')[-1][1:-2] for item in str(ftables.value).split(';')]
        layer_fields = [[field[1], field[0]] for field in fl_flds.value]
        table_fields = []
        if tb_flds.value != None:
            table_fields = [[field[1], field[0]] for field in tb_flds.value]
        
        if table_urls[0] == 'o':
            table_urls = []
        cfg = {}
        cfg['cityworks'] = {'url': cw_url.value,
                            'username': cw_user.value,
                            'password': cw_pw.value,
                            'timezone': cw_timezone.value,
                            'isCWOL': cw_cwol.value}
        cfg['arcgis'] = {'url': portal_url.value,
                         'username': portal_user.value,
                         'password': portal_pw.value,
                         'layers': layer_urls,
                         'tables': table_urls}
        cfg['fields'] = {'layers': layer_fields,
                         'tables': table_fields,
                         'ids': [cw_id.value, report_id.value],
                         'type': [cw_probtype.value, report_type.value],
                         'opendate': [cw_opendate.value, report_opendate.value]}
        cfg['flag'] = {'field': flag_fld.value,
                       'on': flag_on.value,
                       'off': flag_off.value}
        with open(config_path.valueAsText, 'w') as cfgfile:
            json.dump(cfg, cfgfile, indent=4)

        return
