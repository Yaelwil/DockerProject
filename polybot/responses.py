import json

"""

The responses.json file contains several cases-
"greetings"- The user greets the bot.
"well_being"- The user asks the bot for well being.
"thanks"- The user thanks the Bot for his job.
"filter" ("intro" + "options")- The user asks for info about the available filters (intro- chooses random sentence,
options- are static).
"default"- The default message when the user's input is not recognize.
"photo_errors" ("no_cation")- The user sent a photo but with no captions.
"photo_errors" ("permissions_error")- The user sent a message but can't be edited due to permissions error.
"help"- explanation about the bot.

"""


def load_responses():
    with open('responses.json', 'r') as file:
        return json.load(file)