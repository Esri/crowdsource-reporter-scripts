#-------------------------------------------------------------------------------
# Name:        wordlist.py
# Purpose:     Lists of words to use to screen public comments.
#              Words are not case sensitive.

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

# URL to the organization hosting the services and credentials to an account in
#   that org that can edit the services

orgURL = ''
username = ''
password = ''

# Services to scan for words.
#   - url: the url to the REST endpoint of the service
#   - status field: name of the field containing a status value that indicates
#           the report has not yet been reviewed. Define this value below as status_value
#   - flag: Name of field that contains the visible and hiddlen values specified below
#   - reason: field to populate with the reason the feature was updated
#   - fields: List of names of fields to search for the listed words

services = [{'url':            '',
             'status field':   '',
             'flag field':     '',
             'reason field':   '',
             'fields to scan': ['','']},
            {'url':            '',
             'status field':   '',
             'flag field':     '',
             'reason field':   '',
             'fields to scan': ['','']}
           ]

# Value of the status field indicating the report should be reviewed
status_value = 'SUBMITTED'

# Dual values for the flag field. Only fields with the visible value will be
#   processed.
# Features with explicit or sensitive words will be updated to have the
#   hidden value

visible_value = 'YES'
hidden_value = 'NO'

# List of words considered explicit.
# All words containing these patterns of letters will be considered explicit.
bad_words = ['goose', 'gull']

# Only words that are exact matches to these words will be considered explicit.
bad_words_exact = ['duck']

# List of words to use to screen for sensitive content.
# All words containing these patterns of letters will be considered sensitive.
sensitive_words = ['perch', 'carp', 'lobster']

# Also filter explicit and sensitive words that contain the following character
#   substitutions
# Case insensitive letters on the right will be considered equal to the
#   case-insensitive letter on the left.
subs = {'A': '@',
        'C': 'K',
        'E': '3',
        'I': '!1',
        'K': 'C',
        'O': '0',
        'S': '$5Z',
        'T': '+7'
        }
