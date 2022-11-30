import json
import os

"""
This scripts is used to read from expression database json by path
"""

expressionJsonpath = os.path.dirname(__file__) + '/expressions_and_declensions.json'
expressionJson = json.load(open(expressionJsonpath, encoding='utf-8'))

bagOfWordsJsonPath = os.path.dirname(__file__) + '/bag_of_words.json'
bagOfWordsJson = json.load(open(bagOfWordsJsonPath, encoding='utf-8'))

declensionsJsonpath = os.path.dirname(__file__) + '/declensions.json'
declensionsJson = json.load(open(declensionsJsonpath, encoding='utf-8'))

medConfigJsonPath = os.path.dirname(__file__) + '/config/basic_config.json'
medConfigJson = json.load(open(medConfigJsonPath, encoding='utf-8'))

basicConfigJsonPath = os.path.dirname(__file__) + '/config/basic_config.json'
basicConfigJson = json.load(open(basicConfigJsonPath, encoding='utf-8'))


def readJson(file: str, path: str):

    if file == "basic_config":
        return basicConfigJson
    if file == "med_config":
        return medConfigJson

    if path:
        parts = path.split('/')
    else:
        parts = []

    if file == "expressions":
        jsonFile = expressionJson
    elif file == "declensions":
        jsonFile = declensionsJson
    else:
        jsonFile = bagOfWordsJson

    for part in parts:
        jsonFile = jsonFile[part]
    return jsonFile
