import arcpy
import json
from os import path
from arcgis.gis import GIS
#from arcgis.apps import workforce
import copy

configuration_file = path.join(path.dirname(__file__), 'WorkforceConnection.json')

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [Workforce]


class Workforce(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Configure Workforce Connection"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        portal_url = arcpy.Parameter(
            displayName='ArcGIS Online organization or ArcGIS Enterprise portal URL',
            name='portal_url',
            datatype='GPString',
            parameterType='Required',
            direction='Input')
        portal_url.filter.type = 'ValueList'
        portal_url.filter.list = arcpy.ListPortalURLs()

        portal_user = arcpy.Parameter(
            displayName='Username',
            name='portal_user',
            datatype='GPString',
            parameterType='Required',
            direction='Input')

        portal_pass = arcpy.Parameter(
            displayName='Password',
            name='portal_pass',
            datatype='GPStringHidden',
            parameterType='Required',
            direction='Input')

        layer = arcpy.Parameter(
            displayName='Layer',
            name='layer',
            datatype='GPFeatureLayer',
            parameterType='Required',
            direction='Input')

        wkfcconfigs = arcpy.Parameter(
            displayName='Workforce configurations',
            name='wkfcconfigs',
            datatype='GPString',
            parameterType='Required',
            direction='Input')
        wkfcconfigs.filter.type = 'ValueList'
        wkfcconfigs.filter.list = ['Add New']
        wkfcconfigs.enabled = 'False'

        project = arcpy.Parameter(
            displayName='Workforce Project',
            name='project',
            datatype='GPString',
            parameterType='Required',
            direction='Input')
        project.filter.type = 'ValueList'
        project.filter.list = ['Provide credentials to see available projects']

        sql = arcpy.Parameter(
            displayName='SQL Query',
            name='sql',
            datatype='GPString',
            parameterType='Optional',
            direction='Input')

        fieldmap = arcpy.Parameter(
            displayName='Field Map',
            name='fieldmap',
            datatype='GPValueTable',
            parameterType='Required',
            direction='Input')
        fieldmap.columns = [['Field', 'Source'],
                            ['GPString', 'Target']]
        fieldmap.parameterDependencies = [layer.name]
        fieldmap.filters[1].type = 'ValueList'
        fieldmap.filters[1].list = ['Description', 'Status', 'Notes', 'Priority', 'Assignment Type', 'WorkOrder ID', 'Due Date', 'WorkerID', 'Location', 'Declined Comment', 'Assigned on Date', 'Assignment Read', 'In Progress Date', 'Completed on Date', 'Declined on Date', 'Paused on Date', 'DispatcherID']

        updatefield = arcpy.Parameter(
            displayName='Update Field',
            name='updatefield',
            datatype='Field',
            parameterType='Required',
            direction='Input')
        updatefield.parameterDependencies = [layer.name]

        updatevalue = arcpy.Parameter(
            displayName='Update Value',
            name='updatevalue',
            datatype='GPString',
            parameterType='Required',
            direction='Input')

        delete = arcpy.Parameter(
            displayName='Delete this workforce configuration for this layer',
            name='delete',
            datatype='Boolean',
            parameterType='Optional',
            direction='Input')
        delete.enabled = "False"

        try:
            with open(configuration_file, 'r') as config_params:
                config = json.load(config_params)
                portal_url.value = config["organization url"]
                portal_user.value = config['username']
                portal_pass.value = config['password']

        except FileNotFoundError:
            newconfig = {'username':'',
                         'organization url':'',
                         'services':[],
                         'password':''}
            with open(configuration_file, 'w') as config_params:
                json.dump(newconfig, config_params)

        if not portal_url.value:
            portal_url.value = arcpy.GetActivePortalURL()

        if portal_url.value and not portal_user.value:
            try:
                portal_user.value = arcpy.GetPortalDescription(portal_url.valueAsText)['user']['username']
            except KeyError:
                pass

        params = [portal_url, portal_user, portal_pass, layer, wkfcconfigs, delete, project, sql, fieldmap, updatefield, updatevalue]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        portal_url, portal_user, portal_pass, layer, wkfcconfigs, delete, project, sql, fieldmap, updatefield, updatevalue = parameters

        if layer.value and not layer.hasBeenValidated:
            try:
                val = layer.value
                srclyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
            except AttributeError:
                srclyr = layer.valueAsText

            with open(configuration_file, 'r') as config_params:
                config = json.load(config_params)
                existing_configs = []
                global config_list
                config_list= []
                for service in config['services']:
                    if service['url'] == str(srclyr):
                        config_str = "{}: {}".format(service['project'], service['sql'])
                        existing_configs.append(config_str)
                        config_list.append(service)

                if existing_configs:
                    wkfcconfigs.value = ""
                    wkfcconfigs.enabled = 'True'
                    existing_configs.insert(0, 'Add New')
                    wkfcconfigs.filter.list = existing_configs
                else:
                    wkfcconfigs.filter.list = ['Add New']
                    wkfcconfigs.value = "Add New"
                    wkfcconfigs.enabled = "False"
                    delete.enabled = "False"

        if portal_user.value and portal_pass.value and portal_url.value and project.filter.list == ['Provide credentials to see available projects']:
            gis = GIS(portal_url.valueAsText, portal_user.valueAsText, portal_pass.valueAsText)
            search_result = gis.content.search(query="owner:{}".format(portal_user.valueAsText), item_type="Workforce Project")
            project.filter.list = ['{} ({})'.format(s.title, s.id) for s in search_result]

        if wkfcconfigs.value and not wkfcconfigs.hasBeenValidated:
            if wkfcconfigs.valueAsText == 'Add New' or wkfcconfigs.valueAsText == '':
                delete.enabled = "False"
                project.value = ''
                sql.value = ''
                fieldmap.value = []
                updatefield.value = ''
                updatevalue.value = ''
            else:
                sql.value = wkfcconfigs.valueAsText.split(':')[1].strip()
                project.value = wkfcconfigs.valueAsText.split(':')[0].strip()
                for service in config_list:
                    if service['project'] == project.value and service['sql'] == sql.value:
                        fieldmap.values = service['fieldmap']
                        updatefield.value = service['update field']
                        updatevalue.value = service['update value']
                        delete.enabled = "True"
                        break
                else:
                    delete.enabled = "False"
                    project.value = ''
                    sql.value = ''
                    fieldmap.value = []
                    updatefield.value = ''
                    updatevalue.value = ''

        if not delete.hasBeenValidated:
            if delete.value:
                projectid = wkfcconfigs.valueAsText.split(':')[1].strip()
                sqlstr = wkfcconfigs.valueAsText.split(':')[0].strip()
                for service in config_list:
                    if service['project'] == projectid and service['sql'] == sqlstr:
                        project.value = projectid
                        sql.value = sqlstr
                        fieldmap.values = service['fieldmap']
                        updatefield.value = service['update field']
                        updatevalue.value = service['update value']
                        break

                fieldmap.enabled = "False"
                updatefield.enabled = "False"
                updatevalue.enabled = "False"
                sql.enabled = "False"
                project.enabled = "False"
            else:
                fieldmap.enabled = "True"
                updatefield.enabled = "True"
                updatevalue.enabled = "True"
                sql.enabled = "True"
                project.enabled = "True"
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        portal_url, portal_user, portal_pass, layer, wkfcconfigs, delete, project, sql, fieldmap, updatefield, updatevalue = parameters

        try:
            val = layer.value
            srclyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
        except AttributeError:
            srclyr = layer.valueAsText

        with open(configuration_file, 'r') as config_params:
            config = json.load(config_params)

        newconfig = copy.deepcopy(config)
        if newconfig['services']:
            sqlstr = wkfcconfigs.valueAsText.split(':')[1].strip()
            projectid = wkfcconfigs.valueAsText.split(':')[0].strip()
        for service in newconfig["services"]:
            if service["url"] == srclyr and service['project'] == projectid and service['sql'] == sqlstr:

                if wkfcconfigs.value != 'Add New':
                    newconfig['services'].remove(service)

                if not delete.value:
                    newconfig["services"].append({"url": srclyr,
                                                  "project": project.valueAsText,
                                                  "sql": sql.valueAsText,
                                                  "fieldmap": fieldmap.valueAsText,
                                                  "update field": updatefield.valueAsText,
                                                  "update value":updatevalue.valueAsText})
                    newconfig['organization url'] = portal_url.valueAsText
                    newconfig['username'] = portal_user.valueAsText
                    newconfig['password'] = portal_pass.valueAsText
                break
        else:
            newconfig["services"].append({"url": srclyr,
                                          "project": project.valueAsText,
                                          "sql": sql.valueAsText,
                                          "fieldmap": fieldmap.valueAsText,
                                          "update field": updatefield.valueAsText,
                                          "update value": updatevalue.valueAsText})
            newconfig['organization url'] = portal_url.valueAsText
            newconfig['username'] = portal_user.valueAsText
            newconfig['password'] = portal_pass.valueAsText

        try:
            with open(configuration_file, 'w') as config_params:
                json.dump(newconfig, config_params)
        except:
            with open(configuration_file, 'w') as config_params:
                json.dump(config, config_params)
            arcpy.AddError('Failed to update configuration file.')

        return