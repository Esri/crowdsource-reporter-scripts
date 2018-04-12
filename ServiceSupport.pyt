import arcpy
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import json
from os import path
import copy

configuration_file = path.join(path.dirname(__file__), 'servicefunctions.json')

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Crowdsource Support Tools"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [General, Moderate, Identifiers, Emails, Enrich]


class General(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Define Connection Settings"
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

        try:
            with open(configuration_file, 'r') as config_params:
                config = json.load(config_params)
                portal_url.value = config["organization url"]
                portal_user.value = config['username']
                portal_pass.value = config['password']

        except FileNotFoundError:
            newconfig = {'username':'',
                         'organization url':'',
                         'moderation settings':{'lists':[],
                                                'substitutions':{}},
                         'email settings':{'smtp username':'',
                                           'smtp server':'',
                                           'smtp password':'',
                                           'reply to':'',
                                           'from address':'',
                                           'use tls': False,
                                           'substitutions': []},
                         'services':[],
                         'password':'',
                         'id sequences':[]}
            with open(configuration_file, 'w') as config_params:
                json.dump(newconfig, config_params)

        if not portal_url.value:
            portal_url.value = arcpy.GetActivePortalURL()

        if portal_url.value and not portal_user.value:
            try:
                portal_user.value = arcpy.GetPortalDescription(portal_url.valueAsText)['user']['username']
            except KeyError:
                pass

        params = [portal_url, portal_user, portal_pass]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        portal_url, portal_user, portal_pass = parameters
        if portal_url.value and portal_user.value and portal_pass.value:
            try:
                GIS(portal_url.value, portal_user.value, portal_pass.value)
            except:
                msg = 'Invalid username or password for this portal or organization'
                portal_url.setErrorMessage(msg)
        return

    def execute(self, parameters, messages):
        """Update the configuration JSON to match the updated properties"""

        portal_url, portal_user, portal_pass = parameters

        # Update credentials
        with open(configuration_file, 'r') as config_params:
            config = json.load(config_params)

        newconfig = copy.deepcopy(config)
        newconfig['username'] = portal_user.value
        newconfig['organization url'] = portal_url.value
        newconfig['password'] = portal_pass.value

        try:
            with open(configuration_file, 'w') as config_params:
                json.dump(newconfig, config_params)
        except:
            with open(configuration_file, 'w') as config_params:
                json.dump(config, config_params)
            arcpy.AddError('Failed to update configuration file.')

        return


class Identifiers(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Generate IDs"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        layer = arcpy.Parameter(
            displayName='Layer',
            name='layer',
            datatype=['GPFeatureLayer'],
            parameterType='Required',
            direction='Input')

        delete = arcpy.Parameter(
            displayName='Delete existing configuration for this layer',
            name='delete',
            datatype='Boolean',
            parameterType='Optional',
            direction='Input')
        delete.enabled = False

        seq = arcpy.Parameter(
            displayName='ID Sequence',
            name='seq',
            datatype='GPString',
            parameterType='Required',
            direction='Input')
        seq.filter.type = 'Value List'

        field = arcpy.Parameter(
            displayName='ID Field',
            name='field',
            datatype='Field',
            parameterType='Required',
            direction='Input')
        field.parameterDependencies = [layer.name]

        sequences = arcpy.Parameter(
            displayName='Identifier Sequences',
            name='sequences',
            datatype='GPValueTable',
            parameterType='Required',
            direction='Input',
            multiValue=True)
        sequences.columns = [['GPString', 'Sequence Name'],
                             ['GPString', 'Pattern'],
                             ['GPLong', 'Next Value'],
                             ['GPLong', 'Interval']]
        sequences.category = "General Identifier Settings"

        try:
            with open(configuration_file, 'r') as config_params:
                config = json.load(config_params)
                sequences.values = [[s['name'],
                                     s['pattern'],
                                     s['next value'],
                                     s['interval']] for s in config['id sequences']]
                seq.filter.list = [s['name'] for s in config['id sequences']]

        except FileNotFoundError:
            newconfig = {'username':'',
                         'organization url':'',
                         'moderation settings':{'lists':[],
                                                'substitutions':{}},
                         'email settings':{'smtp username':'',
                                           'smtp server':'',
                                           'smtp password':'',
                                           'reply to':'',
                                           'from address':'',
                                           'use tls': False,
                                           'substitutions': []},
                         'services':[],
                         'password':'',
                         'id sequences':[]}
            with open(configuration_file, 'w') as config_params:
                json.dump(newconfig, config_params)

        params = [layer, delete, seq, field, sequences]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        layer, delete, seq, field, sequences = parameters

        if delete.value or not sequences.values:
            seq.enabled = False
            field.enabled = False
        else:
            seq.enabled = True
            field.enabled = True

        with open(configuration_file, 'r') as config_params:
            config = json.load(config_params)

        try:
            val = layer.value
            lyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
        except AttributeError:
            lyr = layer.valueAsText

        if layer.value and not layer.hasBeenValidated:
            for service in config['services']:
                if lyr == service['url']:
                    seq.value = service['id sequence']
                    field.value = service["id field"]
                    if seq.value:
                        delete.enabled = True
                    break
            else:
                delete.value = False
                delete.enabled = False
                seq.value = ""
                field.value = ""



        if sequences.value and not sequences.hasBeenValidated:
            seq.filter.list = [s[0] for s in sequences.values]

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        layer, delete, seq, field, sequences = parameters

        if not sequences.values:
            layer.setWarningMessage('Define identifier sequences under General Identifier Settings before proceeding.')

        if layer.value and not layer.hasBeenValidated:
            try:
                val = layer.value
                lyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
            except AttributeError:
                lyr = layer.valueAsText

            if 'http' not in lyr:
                layer.setErrorMessage('Layer must be hosted in an ArcGIS Online organization or ArcGIS Enterprise portal')

        return

    def execute(self, parameters, messages):
        """Update the configuration JSON to match the updated properties"""

        layer, delete, seq, field, sequences = parameters

        with open(configuration_file, 'r') as config_params:
            config = json.load(config_params)

        try:
            val = layer.value
            lyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
        except AttributeError:
            lyr = layer.valueAsText

        newconfig = copy.deepcopy(config)

        newconfig['id sequences'] = [{"pattern": seq[1],
                                   "interval": seq[3],
                                   "next value": seq[2],
                                   "name": seq[0]} for seq in sequences.value]

        for service in newconfig["services"]:
            if service["url"] == lyr:
                if delete.value:
                    service["id sequence"] = ''
                    service["id field"] = ''
                    if service == {"id sequence": '',
                                       "email": [],
                                       "url": lyr,
                                       "id field": '',
                                       "moderation": [],
                                       "enrichment": []}:
                        newconfig['services'].remove(service)

                else:
                    service["id sequence"] = seq.valueAsText
                    service["id field"] = field.valueAsText
                break
        else:
            newconfig["services"].append({"id sequence": seq.valueAsText,
                                       "email": [],
                                       "url": lyr,
                                       "id field": field.valueAsText,
                                       "moderation": [],
                                       "enrichment": []})

        arcpy.AddMessage(config['services'])

        try:
            with open(configuration_file, 'w') as config_params1:
                json.dump(newconfig, config_params1)
        except:
            with open(configuration_file, 'w') as config_params2:
                json.dump(config, config_params2)
            arcpy.AddError('Failed to update configuration file.')

        return


class Moderate(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Moderate Reports"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        layer = arcpy.Parameter(
            displayName='Layer',
            name='layer',
            datatype=['DETable', 'GPFeatureLayer', "GPTableView"],
            parameterType='Required',
            direction='Input')

        add_update = arcpy.Parameter(
            displayName='Add new or update existing configuration',
            name='add_update',
            datatype='GPString',
            parameterType='Required',
            direction='Input')
        add_update.filter.type = 'ValueList'
        add_update.filter.list = ['Add New']
        add_update.value = 'Add New'
        add_update.enabled = False

        delete = arcpy.Parameter(
            displayName='Delete existing configuration for this layer',
            name='delete',
            datatype='Boolean',
            parameterType='Optional',
            direction='Input')
        delete.enabled = False

        modlist = arcpy.Parameter(
            displayName='Moderation List',
            name='modlist',
            datatype='GPString',
            parameterType='Required',
            direction='Input')
        modlist.filter.type = 'ValueList'
        modlist.filter.list = ['configure','moderation','lists']

        mod_fields = arcpy.Parameter(
            displayName='Fields to Monitor',
            name='mod_fields',
            datatype='Field',
            parameterType='Required',
            direction='Input',
            multiValue=True)
        mod_fields.parameterDependencies = [layer.name]

        sql = arcpy.Parameter(
            displayName='SQL Query',
            name='sql',
            datatype='GPString',
            parameterType='Optional',
            direction='Input')

        update_field = arcpy.Parameter(
            displayName='Field to Update',
            name='update_field',
            datatype='Field',
            parameterType='Required',
            direction='Input')
        update_field.parameterDependencies = [layer.name]

        found_value = arcpy.Parameter(
            displayName='Found Value',
            name='found_value',
            datatype='Field',
            parameterType='Required',
            direction='Input')

        modlists = arcpy.Parameter(
            displayName='Moderation Lists',
            name='modlists',
            datatype='GPValueTable',
            parameterType='Required',
            direction='Input')
        modlists.columns = [['GPString', 'List Name'],
                            ['GPString', 'Filter Type'],
                            ['GPString', 'Words and Phrases']]
        modlists.filters[1].type = 'ValueList'
        modlists.filters[1].list = ['FUZZY', 'EXACT']
        modlists.category = 'General Moderation Settings'

        charsubs = arcpy.Parameter(
            displayName='Character Substitutions',
            name='charsubs',
            datatype='GPString',
            parameterType='Optional',
            direction='Input')
        charsubs.columns = [['GPString', 'Letter'],
                            ['GPString', 'Substitutions']]
        charsubs.category = 'General Moderation Settings'

        try:
            with open(configuration_file, 'r') as config_params:
                config = json.load(config_params)
            words = config['moderation settings']['lists']
            subs = config['moderation settings']['substitutions']
            modlists.values = [[lst['filter name'],
                                lst['filter type'],
                                lst['words']] for lst in words]
            charsubs.values = [[val, subs[val]] for val in subs]
            moderation_lists = [lst['filter name'] for lst in words]
            if moderation_lists:
                modlist.filter.list = moderation_lists

        except FileNotFoundError:
            newconfig = {'username': '',
                         'organization url': '',
                         'moderation settings': {'lists': [],
                                                 'substitutions': {}},
                         'email settings': {'smtp username': '',
                                            'smtp server': '',
                                            'smtp password': '',
                                            'reply to': '',
                                            'from address': '',
                                            'use tls': False,
                                            'substitutions': []},
                         'services': [],
                         'password': '',
                         'id sequences': []}
            with open(configuration_file, 'w') as config_params:
                json.dump(newconfig, config_params)

        params = [layer, add_update, delete, modlist, mod_fields, sql, update_field, found_value, modlists, charsubs]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        layer, add_update, delete, modlist, mod_fields, sql, update_field, found_value, modlists, charsubs = parameters

        if modlists.value and not modlists.hasBeenValidated:
            modlist.filter.list = [s[0] for s in modlists.values]

        with open(configuration_file, 'r') as config_params:
            config = json.load(config_params)

        try:
            val = layer.value
            if str(type(val)) == "<class 'geoprocessing value object'>":
                aprx = arcpy.mp.ArcGISProject("CURRENT")
                currmap = aprx.activeMap
                for table in currmap.listTables():
                    if table.name == layer.valueAsText:
                        val = table
                        break
            lyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
        except (AttributeError, KeyError):
            lyr = layer.valueAsText

        if layer.value and not layer.hasBeenValidated:
            if 'http' in lyr:
                for service in config['services']:
                    if lyr == service['url']:
                        query_list = [query['list'] for query in service['moderation']]
                        if query_list:
                            add_update.enabled = True
                            query_list.insert(0, 'Add New')
                            add_update.filter.list = query_list
                            add_update.value = ''
                        else:
                            add_update.enabled = False
                            add_update.value = 'Add New'
                        break


        if add_update.value and not add_update.hasBeenValidated:
            if add_update.valueAsText == 'Add New':
                delete.value = False
                delete.enabled = False
                mod_fields.values = []
                sql.value = ''
                update_field.value = ''
                found_value.value = ''
                modlist.value = ''
            else:
                delete.enabled = True
                for service in config['services']:
                    if lyr == service['url']:
                        for query in service['moderation']:
                            if query['list'] == add_update.valueAsText:
                                modlist.value = query['list']
                                mod_fields.values = query['scan fields']
                                sql.value = query['sql']
                                update_field.value = query['field']
                                found_value.value = query['value']
                                break
                        break

                    else:
                        add_update.value = 'Add New'
                        add_update.enabled = False
                        delete.enabled = False
                        mod_fields.values = []
                        sql.value = ''
                        update_field.value = ''
                        found_value.value = ''
                        modlist.value = ''

        if delete.value or not modlists.values:
            modlist.enabled = False
            mod_fields.enabled = False
            sql.enabled = False
            update_field.enabled= False
            found_value.enabled = False
        else:
            modlist.enabled = True
            mod_fields.enabled = True
            sql.enabled = True
            update_field.enabled= True
            found_value.enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        layer, add_update, delete, modlist, mod_fields, sql, update_field, found_value, modlists, charsubs = parameters

        if not modlists.values:
            layer.setWarningMessage('Define moderation list under General Moderation Settings before proceeding.')

        if layer.value:
            try:
                val = layer.value
                if str(type(val)) == "<class 'geoprocessing value object'>":
                    aprx = arcpy.mp.ArcGISProject("CURRENT")
                    currmap = aprx.activeMap
                    for table in currmap.listTables():
                        if table.name == layer.valueAsText:
                            val = table
                            break
                lyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
            except (AttributeError, KeyError):
                lyr = layer.valueAsText

            if 'http' not in lyr:
                layer.setErrorMessage('Layer must be hosted in an ArcGIS Online organization or ArcGIS Enterprise portal')

            elif sql.value:# and not sql.hasBeenValidated and not layer.hasBeenValidated:

                with open(configuration_file, 'r') as config_params:
                    config = json.load(config_params)

                if config['organization url'] and config['username'] and config['password']:
                    gis = GIS(config['organization url'], config['username'], config['password'])
                    fl = FeatureLayer(lyr, gis)
                    validation = fl.validate_sql(sql.valueAsText)
                    if not validation['isValidSQL']:
                        messages = '\n'.join(['{}: {}'.format(msg['errorCode'], msg['description']) for msg in validation['validationErrors']])
                        sql.setErrorMessage(messages)
                else:
                    sql.setWarningMessage('Cannot validate SQL. Portal/Organization URL and credentials are missing. Run the Define Connection Settings tool to validate this SQL statement.')
        return

    def execute(self, parameters, messages):
        """Update the configuration JSON to match the updated properties"""

        lyr, add_update, delete, modlist, mod_fields, sql, update_field, found_value, modlists, charsubs = parameters

        try:
            val = lyr.value
            layer = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
        except AttributeError:
            layer = lyr.valueAsText

        with open(configuration_file, 'r') as config_params:
            config = json.load(config_params)

        newconfig = copy.deepcopy(config)
        subs = {}
        if charsubs.values:
            for sub in charsubs.values:
                subs[sub[0]] = sub[1]
        newconfig['moderation settings'] = {'lists': [{'filter type': mod[1], 'words': mod[2], 'filter name': mod[0]} for mod in modlists.values],
                                             'substitutions': subs}

        if sql.value:
            query = sql.valueAsText
        else:
            query = '1=1'

        newquery = {"list": modlist.valueAsText,
                    "sql": query,
                    "field": update_field.valueAsText,
                    "value": found_value.valueAsText,
                    'scan fields': mod_fields.valueAsText}

        for service in newconfig["services"]:
            if service["url"] == layer:
                if add_update.value != 'Add New':
                    for query in service['moderation']:
                        if query['list'] == add_update.value:
                            service['moderation'].remove(query)
                            break
                if not delete.value:
                    service['moderation'].append(newquery)
                else:
                    if service == {"id sequence": '',
                                       "email": [],
                                       "url": layer,
                                       "id field": '',
                                       "moderation": [],
                                       "enrichment": []}:
                        newconfig['services'].remove(service)
                break

        else:
            newconfig["services"].append({"id sequence": "",
                                          "email": [],
                                          "url": layer,
                                          "id field": "",
                                          "moderation": [newquery],
                                          "enrichment": []})

        try:
            with open(configuration_file, 'w') as config_params:
                json.dump(newconfig, config_params)
        except TypeError:
            with open(configuration_file, 'w') as config_params:
                json.dump(config, config_params)
            arcpy.AddError('Failed to update configuration file.')

        return


class Emails(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Send Emails"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        layer = arcpy.Parameter(
            displayName='Layer',
            name='layer',
            datatype=['DETable', 'GPFeatureLayer', 'GPTableView'],
            parameterType='Required',
            direction='Input')

        delete = arcpy.Parameter(
            displayName='Delete all existing email configurations for this layer',
            name='delete',
            datatype='Boolean',
            parameterType='Optional',
            direction='Input')
        delete.enabled = False

        email_settings = arcpy.Parameter(
            displayName='Email Settings',
            name='email_settings',
            datatype='GPValueTable',
            parameterType='Required',
            direction='Input')

        email_settings.columns = [['DEFile', 'Email Template'],
                                  ['GPString', 'SQL Query'],
                                  ['GPString', 'Recipient Email Address'],
                                  ['GPString', 'Email Subject'],
                                  ['Field', 'Field to Update'],
                                  ['GPString', 'Sent Value']]
        email_settings.parameterDependencies = [layer.name]
        email_settings.filters[0].list = ['html']

        substitutions = arcpy.Parameter(
            displayName='Email Substitutions',
            name='substitutions',
            datatype='GPValueTable',
            parameterType='Optional',
            direction='Input')
        substitutions.columns = [['GPString', 'Find'],
                                 ['GPString', 'Replace']]
        substitutions.category = 'General Email Settings'

        smtp_username = arcpy.Parameter(
            displayName="SMTP Username",
            name='smtp_username',
            datatype='GPString',
            parameterType='Optional',
            direction='Input')
        smtp_username.category = 'General Email Settings'

        reply_address = arcpy.Parameter(
            displayName="Reply Address",
            name='reply_address',
            datatype='GPString',
            parameterType='Optional',
            direction='Input')
        reply_address.category = 'General Email Settings'

        smtp_server = arcpy.Parameter(
            displayName="SMTP Server",
            name='smtp_server',
            datatype='GPString',
            parameterType='Required',
            direction='Input')
        smtp_server.category = 'General Email Settings'

        smtp_password = arcpy.Parameter(
            displayName="SMTP Password",
            name='smtp_password',
            datatype='GPString',
            parameterType='Optional',
            direction='Input')
        smtp_password.category = 'General Email Settings'

        from_address = arcpy.Parameter(
            displayName="From Address",
            name='from_address',
            datatype='GPString',
            parameterType='Optional',
            direction='Input')
        from_address.category = 'General Email Settings'

        use_tls = arcpy.Parameter(
            displayName="Use TLS",
            name='use_tls',
            datatype='GPBoolean',
            parameterType='Optional',
            direction='Input')
        use_tls.category = 'General Email Settings'

        try:
            with open(configuration_file, 'r') as config_params:
                config = json.load(config_params)
                smtp_server.value = config['email settings']['smtp server']
                smtp_username.value = config['email settings']['smtp username']
                smtp_password.value = config['email settings']['smtp password']
                from_address.value = config['email settings']['from address']
                reply_address.value = config['email settings']['reply to']
                use_tls.value = config['email settings']['use tls']
                substitutions.values = config['email settings']['substitutions']

        except FileNotFoundError:
            newconfig = {'username':'',
                         'organization url':'',
                         'moderation settings':{'lists':[],
                                                'substitutions':{}},
                         'email settings':{'smtp username':'',
                                           'smtp server':'',
                                           'smtp password':'',
                                           'reply to':'',
                                           'from address':'',
                                           'use tls': False,
                                           'substitutions': []},
                         'services':[],
                         'password':'',
                         'id sequences':[]}
            with open(configuration_file, 'w') as config_params:
                json.dump(newconfig, config_params)

        params = [layer, delete, email_settings, smtp_server, smtp_username, smtp_password, from_address, reply_address, use_tls, substitutions]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        layer, delete, email_settings, smtp_server, smtp_username, smtp_password, from_address, reply_address, use_tls, substitutions = parameters

        if layer.value and not layer.hasBeenValidated:
            try:
                val = layer.value
                if str(type(val)) == "<class 'geoprocessing value object'>":
                    aprx = arcpy.mp.ArcGISProject("CURRENT")
                    currmap = aprx.activeMap
                    for table in currmap.listTables():
                        if table.name == layer.valueAsText:
                            val = table
                            break
                lyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
            except (AttributeError, KeyError):
                lyr = layer.valueAsText

            with open(configuration_file, 'r') as config_params:
                config = json.load(config_params)

            for service in config['services']:
                if service['url'] == lyr and service['email']:
                    delete.enabled = True
                    email_settings.value = [[info['template'],
                                             info['sql'],
                                             info['recipient'],
                                             info['subject'],
                                             info['field'],
                                             info['sent value']] for info in service['email']]
                    break
            else:
                delete.enabled = False
                email_settings.value = ""

        if delete.value:
            email_settings.enabled = False
        else:
            email_settings.enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        layer, delete, email_settings, smtp_server, smtp_username, smtp_password, from_address, reply_address, use_tls, substitutions = parameters

        if layer.value and not layer.hasBeenValidated:
            try:
                val = layer.value
                if str(type(val)) == "<class 'geoprocessing value object'>":
                    aprx = arcpy.mp.ArcGISProject("CURRENT")
                    currmap = aprx.activeMap
                    for table in currmap.listTables():
                        if table.name == layer.valueAsText:
                            val = table
                            break
                lyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
            except (AttributeError, KeyError):
                lyr = layer.valueAsText

            if 'http' not in lyr:
                layer.setErrorMessage('Layer must be hosted in an ArcGIS Online organization or ArcGIS Enterprise portal')

        return

    def execute(self, parameters, messages):
        """Update the configuration JSON to match the updated properties"""

        layer, delete, email_settings, smtp_server, smtp_username, smtp_password, from_address, reply_address, use_tls, substitutions = parameters

        try:
            val = layer.value
            lyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
        except AttributeError:
            lyr = layer.valueAsText

        with open(configuration_file, 'r') as config_params:
            config = json.load(config_params)

        newconfig = copy.deepcopy(config)
        newconfig['email settings'] = {'smtp username': smtp_username.valueAsText,
                                        'smtp server': smtp_server.valueAsText,
                                        'smtp password': smtp_password.valueAsText,
                                        'reply to': reply_address.valueAsText,
                                        'from address': from_address.valueAsText,
                                        'use tls': use_tls.value,
                                        'substitutions': substitutions.value}

        emails = [{"field": query[4].value,
                   "sent value": query[5],
                   "sql": query[1],
                   "recipient": query[2],
                   "template": query[0].value,
                   "subject": query[3]} for query in email_settings.values]

        for service in newconfig["services"]:
            if service["url"] == lyr:
                if delete.value:
                    service["email"] = []
                    if service == {"id sequence": '',
                                       "email": [],
                                       "url": lyr,
                                       "id field": '',
                                       "moderation": [],
                                       "enrichment": []}:
                        newconfig['services'].remove(service)
                else:
                    service["email"] = emails
                break
        else:
            newconfig["services"].append({"id sequence": "",
                                       "email": emails,
                                       "url": lyr,
                                       "id field": "",
                                       "moderation": [],
                                       "enrichment": []})

        try:
            with open(configuration_file, 'w') as config_params:
                json.dump(newconfig, config_params)
        except:
            with open(configuration_file, 'w') as config_params:
                json.dump(config, config_params)
            arcpy.AddError('Failed to update configuration file.')

        return


class Enrich(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Enrich Reports"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        layer = arcpy.Parameter(
            displayName='Layer',
            name='layer',
            datatype='GPFeatureLayer',
            parameterType='Required',
            direction='Input')

        polyconfigs = arcpy.Parameter(
            displayName='Enrichment configurations',
            name='polyconfigs',
            datatype='GPString',
            parameterType='Required',
            direction='Input')
        polyconfigs.filter.type = 'ValueList'
        polyconfigs.filter.values = ['Add New']
        polyconfigs.enabled = 'False'

        polylayer = arcpy.Parameter(
            displayName='Enrichment Layer',
            name='polylayer',
            datatype='GPFeatureLayer',
            parameterType='Required',
            direction='Input')

        source = arcpy.Parameter(
            displayName='Source Field',
            name='source',
            datatype='Field',
            parameterType='Required',
            direction='Input')
        source.parameterDependencies = [polylayer.name]

        target = arcpy.Parameter(
            displayName='Target Field',
            name='target',
            datatype='Field',
            parameterType='Required',
            direction='Input')
        target.parameterDependencies = [layer.name]

        priority = arcpy.Parameter(
            displayName='Priority',
            name='priority',
            datatype='GPLong',
            parameterType='Required',
            direction='Input')

        delete = arcpy.Parameter(
            displayName='Delete this enrichment configuration for this layer',
            name='delete',
            datatype='Boolean',
            parameterType='Optional',
            direction='Input')
        delete.enabled = "False"

        params = [layer, polyconfigs, delete, polylayer, source, target, priority]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        layer, polyconfigs, delete, polylayer, source, target, priority = parameters

        if layer.value and not layer.hasBeenValidated:
            try:
                val = layer.value
                srclyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
            except AttributeError:
                srclyr = layer.valueAsText

            try:
                with open(configuration_file, 'r') as config_params:
                    config = json.load(config_params)
                    for service in config['services']:
                        if service['url'] == str(srclyr):

                            existing_configs = ["{}: {} ({}-{})".format(info['priority'], info['url'], info['source'], info['target']) for info in service['enrichment']]
                            if existing_configs:
                                polyconfigs.value = ""
                                polyconfigs.enabled = 'True'
                                existing_configs.insert(0, 'Add New')
                                polyconfigs.filter.list = existing_configs
                            else:
                                polyconfigs.filter.list = ['Add New']
                                polyconfigs.value = "Add New"
                                polyconfigs.enabled = "False"
                                delete.enabled = "False"
                            break
                    else:
                        polyconfigs.filter.list = ['Add New']
                        polyconfigs.value = "Add New"
                        polyconfigs.enabled = "False"
                        delete.enabled = "False"

            except FileNotFoundError:
                newconfig = {'username': '',
                             'organization url': '',
                             'moderation settings': {'lists': [],
                                                     'substitutions': {}},
                             'email settings': {'smtp username': '',
                                                'smtp server': '',
                                                'smtp password': '',
                                                'reply to': '',
                                                'from address': '',
                                                'use tls': False,
                                                'substitutions': []},
                             'services': [],
                             'password': '',
                             'id sequences': []}
                with open(configuration_file, 'w') as config_params:
                    json.dump(newconfig, config_params)

        if polyconfigs.value and not polyconfigs.hasBeenValidated:
            if polyconfigs.valueAsText == 'Add New' or polyconfigs.valueAsText == '':
                delete.enabled = "False"
                priority.value = ''
                polylayer.value = ''
                target.value = ''
                source.value = ''
            else:
                delete.enabled = "True"
                priority.value = int(polyconfigs.valueAsText.split(':')[0])
                polylayer.value = polyconfigs.valueAsText.split(" ")[1]
                fields = polyconfigs.valueAsText.split('(')[1].strip(')')
                target.value = fields.split('-')[-1]
                source.value = fields.split('-')[0]

        if not delete.hasBeenValidated:
            if delete.value:
                priority.value = int(polyconfigs.valueAsText.split(':')[0])
                polylayer.value = polyconfigs.valueAsText.split(" ")[1]
                fields = polyconfigs.valueAsText.split('(')[1].strip(')')
                target.value = fields.split('-')[-1]
                source.value = fields.split('-')[0]
                priority.enabled = "False"
                polylayer.enabled = "False"
                target.enabled = "False"
                source.enabled = "False"
            else:
                priority.enabled = "True"
                polylayer.enabled = "True"
                target.enabled = "True"
                source.enabled = "True"

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        layer, polyconfigs, delete, polylayer, source, target, priority = parameters

        if polylayer.value:
            try:
                val = polylayer.value
                lyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
            except AttributeError:
                lyr = polylayer.valueAsText

            if 'http' not in lyr:
                polylayer.setErrorMessage('Layer must be hosted in an ArcGIS Online organization or ArcGIS Enterprise portal')

        if layer.value:
            try:
                val = layer.value
                lyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
            except AttributeError:
                lyr = layer.valueAsText

            if 'http' not in lyr:
                layer.setErrorMessage('Layer must be hosted in an ArcGIS Online organization or ArcGIS Enterprise portal')

        return

    def execute(self, parameters, messages):
        """Update the configuration JSON to match the updated properties"""

        layer, polyconfigs, delete, polylayer, source, target, priority = parameters

        try:
            val = layer.value
            srclyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
        except AttributeError:
            srclyr = layer.valueAsText

        try:
            val = polylayer.value
            tarlyr = val.connectionProperties['connection_info']['url'] + '/' + val.connectionProperties['dataset']
        except AttributeError:
            tarlyr = polylayer.valueAsText

        with open(configuration_file, 'r') as config_params:
            config = json.load(config_params)

        newconfig = copy.deepcopy(config)

        for service in newconfig["services"]:
            if service["url"] == srclyr:
                if polyconfigs.value != 'Add New':
                    fields = polyconfigs.valueAsText.split('(')[1].strip(')')
                    original_vals = {"url": polyconfigs.valueAsText.split(" ")[1],
                                     "source": fields.split('-')[0],
                                     "target": fields.split('-')[-1],
                                     "priority": int(polyconfigs.valueAsText.split(':')[0])}
                    service['enrichment'].remove(original_vals)

                if not delete.value:
                    service["enrichment"].append({"url": str(tarlyr),
                                                 "source": source.valueAsText,
                                                 "target": target.valueAsText,
                                                 "priority": priority.value})
                else:
                    if service == {"id sequence": '',
                                       "email": [],
                                       "url": str(srclyr),
                                       "id field": '',
                                       "moderation": [],
                                       "enrichment": []}:
                        newconfig['services'].remove(service)
                break
        else:
            newconfig["services"].append({"id sequence": "",
                                          "email": [],
                                          "url": str(srclyr),
                                          "id field": "",
                                          "moderation": [],
                                          "enrichment": [{"url": str(tarlyr),
                                                 "source": source.valueAsText,
                                                 "target": target.valueAsText,
                                                 "priority": priority.value}]})

        try:
            with open(configuration_file, 'w') as config_params:
                json.dump(newconfig, config_params)
        except:
            with open(configuration_file, 'w') as config_params:
                json.dump(config, config_params)
            arcpy.AddError('Failed to update configuration file.')

        return

