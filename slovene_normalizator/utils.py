"""
This file includes various helper methods
"""

import nltk

from slovene_normalizator import word_type_check
from slovene_normalizator.word import Word
from slovene_normalizator.sentence import Sentence
from copy import deepcopy

from re import match
from os.path import dirname

# adding nltk data folder to nltk data path
nltk.data.path.append(dirname(__file__) + "/util/nltk_data")

roman_numerals = {'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000, 'IV': 4, 'IX': 9, 'XL': 40, 'XC': 90, 'CD': 400, 'CM': 900}

prefixes = {'': '', 'p': 'piko', 'n': 'nano', 'μ': 'mikro', 'µ': 'mikro', 'm': 'mili', 'c': 'centi', 'd': 'deci', 'dc': 'deci', 'da': 'deka', 'dk': 'deka', 'h': 'hekto', 'k': 'kilo', 'M': 'mega', 'G': 'giga', 'T': 'tera'}

punctuations_set = {'\\', '[', '(', '»', '«', '"', "'", '“', '”', '‘', ',', '.', ':', ';', '!', '?', ']', ')', "-", "–"}

def pika(t):
    if t[-1] == ".":
        return t
    else:
        return t + "."

def standardize_quotes(sent):
    types_of_quotes=["»", "«", "“", "‘‘", "‘", "„", "``", "`", "''", "”", "’’", "’"]
    for q in types_of_quotes:
        sent=sent.replace(q, '"')
    return sent


# return true if a word starts with capital letter
def starts_with_capital(word: str):
    return word[0].isupper()


# splits word, consisting separator +, - or /
def split_word(word: str):
    separator_index = 0
    separator = ""
    separator_to_word = {"+": "plus", "-": "minus", "/": "skozi"}

    for char_index, char in enumerate(word):
        if char == '+' or char == '-' or char == '/':
            separator_index = char_index
            separator = separator_to_word[char]
            break

    number_1 = word[:separator_index]
    number_2 = word[separator_index + 1:]
    return [number_1, separator, number_2]

# converts roman numeral to integer
def roman_numeral_to_int(roman_string):
    suffix = ""
    if roman_string[-1] == ".":
        roman_string = roman_string[:-1]
        suffix = "."

    rom_val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    int_val = 0
    for i in range(len(roman_string)):
        if i > 0 and rom_val[roman_string[i]] > rom_val[roman_string[i - 1]]:
            int_val += rom_val[roman_string[i]] - 2 * rom_val[roman_string[i - 1]]
        else:
            int_val += rom_val[roman_string[i]]

    return str(int_val) + suffix


def tokenize(sent):
    toks = nltk.word_tokenize(sent)
    trutoks = []
    for i in range(len(toks)):
        t = toks[i]
        if t == "." and 0 < i < len(toks):
            new = trutoks[-1] + t
            trutoks = trutoks[:-1]
            trutoks.append(new)
        elif t in ['``', "''"]:
            trutoks.append('"')
        else:
            trutoks.append(t)
    return trutoks


def isabbr(tok, regexes, last_token):
    if last_token:
        return any(match("^" + regex + "$", tok) for regex in regexes)
    else:
        return tok[-1] == "." and tok[-2].isalpha()


def skip_normalization(config, text: str):
    symbols = set(config['symbol']['set'].keys()) - punctuations_set
    abbr=list(config["abbr"]["set"].keys())

    if any(char.isnumeric() for char in text):
        return False

    tokens = tokenize(text)
    if any(t.lower() in abbr for t in tokens): return False
    if any(ab in text.lower() for ab in [x for x in abbr if " " in x]): return False

    if any(char in text for char in symbols) \
            or any([match("^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})[.]{0,3}$", word) and len(word) >= 2 for word in text.split(" ")]):
        return False

    if any(word_type_check.is_link(config, token) for token in tokens):
        return False

    return True

# if by digits or regular
def integer_pronunciation(config, sentence: Sentence, word_index, word: str):
    prev_word = sentence.get_word(word_index - 1)
    prev_prev_word=sentence.get_word(word_index - 2)
    
    if prev_word and match("(([Ss]klic.{0,3})|([Rr]ačun.{0,3})|([Tt]rr)|(TRR)|[Ii][Dd])", prev_word.un_normalized):
        return "digits"
    elif prev_prev_word and prev_word.un_normalized==":" and match("(([Ss]klic.{0,3})|([Rr]ačun.{0,3})|([Tt]rr)|(TRR)|[Ii][Dd])", prev_prev_word.un_normalized):
        return "digits"
    # if number starts with 0 its likely that it is pronounced digit by digit
    if match("0.*", word):
        return "digits"

    return "regular"


def space(needs_space=False):
    if needs_space: return " "
    return ""
