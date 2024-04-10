import json

# Load JSON data from file


def load_responses():
    with open('responses.json', 'r') as file:
        responses = json.load(file)
