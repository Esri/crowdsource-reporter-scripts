#-------------------------------------------------------------------------------
# Name:        wordlist.py
# Purpose:     Lists of words to use to screen public comments.
#              Words are not case sensitive.
#
#-------------------------------------------------------------------------------


# List of words to screen for explicit content.
bad_words = ['goose', 'gull']
bad_words_exact = ['duck']

# List of words to use to screen for sensitive content.
sensitive_words = ['perch', 'carp', 'lobster']

### List of words that should not be filtered out.
##good_words = ['duckling']