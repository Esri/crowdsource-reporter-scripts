# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------

import re
from datetime import datetime as dt
from os import path
import wordlist
from arcresthelper import securityhandlerhelper
from arcrest.agol import FeatureLayer

m1 = 'Could not connect to {}. Please verify paths and credentials.'
m2 = 'Explicit content found.'
m3 = 'Sensitive content found.'

def get_shh():
    """Connect to an AGOL organization or Portal"""

    securityinfo = {}
    securityinfo['security_type'] = 'Portal'  # LDAP, NTLM, OAuth, Portal, PKI, ArcGIS
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

    try:
        shh = securityhandlerhelper.securityhandlerhelper(securityinfo=securityinfo)

        if not shh.valid:
            return shh.message
        else:
            return shh
    except:
        return 'error'


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

    filter_log = path.join(sys.path[0], 'filter_log.log')
    with open(filter_log, 'a') as log:
        log.write('\n{}\n'.format(dt.now()))

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

            if isinstance(shh, str) or isinstance(shh, dict):
                raise Exception(m1.format(wordlist.orgURL))


            # Process each of the services listed above
            for service in wordlist.services:

                try:
                    fl = FeatureLayer(url=service['url'],
                                      securityHandler=shh.securityhandler,
                                      proxy_port=None,
                                      proxy_url=None,
                                      initialize=True)
                except:
                    raise Exception(m1.format(service['url']))

                # Build SQL query to find visible features
                sql = """{} = '{}' AND {} = '{}'""".format(service['flag field'],
                                                           wordlist.visible_value,
                                                           service['status field'],
                                                           wordlist.status_value)

                # Fields that will be returned by query
                out_fields = ['objectid', service['flag field'],
                              service['reason field']] + service['fields to scan']

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

                        # Find words that are on the bad words list
                        if explicit_filter:
                            if re.search(explicit_filter, text):
                                explicit_content = True
                                break

                        # Find words that are on the sensitive words list
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
                            reason += m2

                        elif sensitive_content:
                            reason += m3

                        # Update reason
                        feat.set_value(service['reason field'], reason)

                        # Mark feature with hidden value
                        feat.set_value(service['flag field'], wordlist.hidden_value)

                # Commit updates and print status
                status = fl.updateFeature(features=resFeats)
                log.write('{}\n'.format(status))

        except Exception as ex:
            log.write('{}\n'.format(ex))

if __name__ == '__main__':
    main()
