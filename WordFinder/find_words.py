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

import re
import wordlist
from arcresthelper import securityhandlerhelper
from arcrest.agol import FeatureLayer
##
### ------------------------- SET THESE VALUES -------------------------------- #
##
### URL to the organization hosting the services and credentials to an account in
###   that org that can edit the services
##
##orgURL = 'http://localgovtest.maps.arcgis.com'
##username = 'allison_demo'
##password = 'lgdemo123'
##
### Services to scan for words.
###   - url: the url to the REST endpoint of the service
###   - status field: name of the field containing a status value that indicates
###           the report has not yet been reviewed. Define this value below as status_value
###   - flag: Name of field that contains the visible and hiddlen values specified below
###   - reason: field to populate with the reason the feature was updated
###   - fields: List of names of fields to search for the listed words
##
##services = [{'url': 'http://service.arcgis.com/zawkzYpZ6iH7pevp/arcgis/rest/services/CitizenProblemReportsData/FeatureServer/0',
##             'status field': 'STATUS',
##             'flag field':'PUBLICVIEW',
##             'reason': 'RESOLUTION',
##             'fields': ['NAME','DETAILS']}]
##
### Dual values for field that will be updated. Only fields with the visible
###   value will be processed. Features with listed words will be updated to have
###   the hidden value
##
##visible_value = 'YES'
##hidden_value = 'NO'
##
### Status value indicating the report has not yet been reviewed
##status_value = 'SUBMITTED'
##
### Filter words containing the following character substitutions
### Not case-sensitive
##subs = {'A': '@A',
##        'S': '$5ZS',
##        'O': '0O',
##        'I': '!1I',
##        'T': '+7T',
##        'C': 'CK',
##        'K': 'CK',
##        'E': '3E'}
##
### --------------------------------------------------------------------------- #

def get_shh():
    """Connect to an AGOL organization or Portal"""

    securityinfo = {}
    securityinfo['security_type'] = 'Portal'#LDAP, NTLM, OAuth, Portal, PKI, ArcGIS
    securityinfo['username'] = wordlist.username
    securityinfo['password'] = wordlist.password
    securityinfo['org_url'] = wordlist.orgURL
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
        return shh.message
    else:
        return shh


def build_expression(words, exact_match=False):
    """Build an all-caps regular expression for matching either exact or
    partial strings"""

    re_string = ''

    for word in words:
        new_word = ''
        for char in word.upper():

            # If listed, include substitution characters
            if char in wordlist.subs.keys():
                new_word += "[" + char + wordlist.subs[char] + "]"

            else:
                new_word += "[" + char + "]"

        # Filter using only exact matches of the string
        if exact_match:
            re_string += '\\b{}\\b|'.format(new_word)

        # Filter using all occurances of the letter combinations specified
        else:
            re_string += '.*{}.*|'.format(new_word)

    # Last character will always be | and must be dropped
    return re_string[:-1]


def main():
    """Scan fields in services looking for explicit/sensitive words
    (as defined). Features are updated if content is found so that a map filter
    can be used to hide this content"""

    try:
        # Build regular expression of explicit words (uppercase formatting)
        badwords = list(set([str(word).upper() for word in wordlist.bad_words]))
        badwordsexact = list(set([str(word).upper() for word in wordlist.bad_words_exact]))

        explicit_filter = ''
        if badwords:
            explicit_filter += build_expression(badwords)
            if badwordsexact:
                explicit_filter += '|{}'.format(build_expression(badwordsexact))
        elif badwordsexact:
            explicit_filter += build_expression(badwordsexact)

        # Build regular expression of sensitive words (uppercase formatting)
        sensitivewords = list(set([str(word).upper() for word in wordlist.sensitive_words]))
        sensitive_filter = build_expression(sensitivewords)


        shh = get_shh()

        try:
            if 'error' in shh:
                raise Exception('Could not connect to {}. Please verify paths and credentials.'.format(orgURL))

        except TypeError:
            pass

        # Process each of the services listed above
        for service in wordlist.services:

            try:
                fl= FeatureLayer(url=service['url'],
                                     securityHandler=shh.securityhandler,
                                     proxy_port=None,
                                     proxy_url=None,
                                     initialize=True)
            except URLError:
                raise Exception('Could not connect to service {}. Please verify URL and credentials.'.format(service['url']))

            # Build SQL query to find visible features
            sql = """{} = '{}' AND {} = '{}'""".format(service['flag field'],
                                                       wordlist.visible_value,
                                                       service['status field'],
                                                       wordlist.status_value)

            # Fields that will be returned by query
            out_fields = ['objectid', service['flag field'], service['reason field']] + service['fields to scan']

            # Get publicly visible features of the defined status
            resFeats = fl.query(where=sql, out_fields=",".join(out_fields))

            # For each public feature
            for feat in resFeats:
                explicit_content = False
                sensitive_content = False

                # Check each field listed for explicit or sensitive content
                for field in service['fields to scan']:
                    text = feat.get_value(field)
                    text = text.upper()

                    # Find words from the text that are on the bad words list
                    if explicit_filter:
                        if re.search(explicit_filter, text):
                            explicit_content = True
                            break

                    # Find words from the text that are on the bad words list
                    if sensitive_filter:
                        if re.search(sensitive_filter, text):
                            sensitive_content = True
                            break

                if sensitive_content or explicit_content:
                    reason = ''

                    # Get current reason, if any, and append new reason
                    cur_reason = feat.get_value(service['reason field'])
                    if cur_reason:
                        reason += "{} ".format(cur_reason)

                    if explicit_content:
                        reason += "Explicit content found."

                    elif sensitive_content:
                        reason += "Sensitive content found."

                    # Update reason
                    feat.set_value(service['reason field'], reason)

                    # Mark feature with hidden value
                    feat.set_value(service['flag field'], wordlist.hidden_value)

            # Commit updates and print status
            print(fl.updateFeature(features=resFeats))

    except Exception as ex:
        print('error: {}'.format(ex))

if __name__ == '__main__':
    main()