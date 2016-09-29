#-------------------------------------------------------------------------------
# Name:        find_words.py
# Purpose:     updates an indicator field when specific words are found in
#              specific fields of hosted services

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

#-------------------------------------------------------------------------------

""" Minimally tested, totally unsupported, alpha script! Proof of concept for testing only"""

import string
import arcpy
import wordlist

from arcresthelper import securityhandlerhelper
from arcrest.agol import FeatureLayer

# ------------------------- SET THESE VALUES -------------------------------- #

# URL to the organization hosting the services and credentials to an account in
#   that org that can edit the services

orgURL = ''
username = ''
password = ''

# Services to scan for words.
#   - url: the url to the REST endpoint of the service
#   - flag: Name of field that contains the visible and hiddlen values specified below
#   - reason: field to populate with the reason the feature was updated
#   - fields: List of names of fields to search for the listed words

services = [{'url': '',
             'flag':'',
             'reason': '',
             'fields': ['','']},

             {'url': '',
             'flag':'',
             'reason': '',
             'fields': ['','']}]

# Dual values for field that will be updated. Only fields with the visible
#   value will be processed. Features with listed words will be updated to have
#   the hidden value

visible_value = 'YES'
hidden_value = 'NO'

# --------------------------------------------------------------------------- #

# Get lists of words from companion file (uppercase formatting)
badwords = set([word.upper() for word in wordlist.bad_words])
sensitivewords = set([word.upper() for word in wordlist.sensitive_words])
goodwords = [word.upper() for word in wordlist.good_words]

# Connect to org
securityinfo = {}
securityinfo['security_type'] = 'Portal'#LDAP, NTLM, OAuth, Portal, PKI, ArcGIS
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
if shh.valid == False:
    print shh.message

# Process each of the services listed above
for service in services:

    fl= FeatureLayer(
    url=service['url'],
    securityHandler=shh.securityhandler,
    proxy_port=None,
    proxy_url=None,
    initialize=True)

    # Build SQL query to find visible features
    sql = """{} = '{}'""".format(service['flag'], visible_value)

    # Fields that will be returned by query
    out_fields = ['objectid', service['flag'], service['reason']] + service['fields']

    # Get publicly visible features
    resFeats = fl.query(where=sql, out_fields=",".join(out_fields))

    # For each public feature
    for feat in resFeats:
        explicit_content = False
        sensitive_content = False

        # Check each field listed for explicit or sensitive content
        for field in service['fields']:
            text = feat.get_value(field)
            text = text.upper()

            # Remove punctionation from the field text
            text.translate({ord(c): None for c in string.punctuation})

            # Build a case-insensitive list of all words used that aren't already in the 'goodwords' list
            text = set(filter(lambda word: word not in goodwords, text.split(" ")))

            # Find words from the text that are on the bad words list
            if text & badwords:
                explicit_content = True
                break

            # Find words from the text that are on the sensitive words list
            if text & sensitivewords:
                sensitive_content = True
                break

        if sensitive_content or explicit_content:
            reason = ''

            # Get current reason, if any
            cur_reason = feat.get_value(service['reason'])
            if cur_reason:
                reason += "{} ".format(cur_reason)

            if explicit_content:
                reason += "Explicit content found. "

            elif sensitive_content:
                reason += "Sensitive content found. "

            # Update reason
            feat.set_value(service['reason'], reason)

            # Mark feature with hidden value
            feat.set_value(service['flag'], hidden_value)

    # Commit updates and print status
    print fl.updateFeature(features=resFeats)

