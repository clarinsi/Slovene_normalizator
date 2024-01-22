"""
Methods for checking if a string is one of supported types of words
"""

from re import match, search

from normalizator import sentence
from normalizator.sentence import Sentence
from normalizator.util import json_reader
from normalizator.utils_helpers import dot_in_the_middle, is_decimal, is_fraction, is_numeric, isordinal
from normalizator.word import Word

from normalizator.super_tools.slicer import slicer

# global number, for single json reading
prefixes = {'': '', 'p': 'piko', 'n': 'nano', 'μ': 'mikro', 'µ': 'mikro', 'm': 'mili', 'c': 'centi', 'd': 'deci', 'dc': 'deci', 'da': 'deka', 'dk': 'deka', 'h': 'hekto', 'k': 'kilo', 'M': 'mega', 'G': 'giga', 'T': 'tera'}

bag_of_words_result = json_reader.readJson('bagOfWords', 'Rezultat')
bag_of_words_date_year = json_reader.readJson('bagOfWords', 'Leto')
bag_of_words_hour_left_side = json_reader.readJson('bagOfWords', "Ura/Levo")
bag_of_words_hour_right_side = json_reader.readJson('bagOfWords', "Ura/Desno")



def is_regular_word(word: str):
    return bool(match("[a-zčšćđžA-ZČŠĆĐŽ]+", word))

def is_complex_duration(config, sentence: Sentence, word_index):
    word = sentence.get_word(word_index).un_normalized
    return bool(match("\d+:\d+,\d+", word))


def is_math_operation(word: Word):
    word = word.un_normalized
    return bool(match("^[(:\"']*(\d+(,\d+)?[+\-*/=×<>])+\d+(,\d+)?[)!?.:,'‘»”\"]*$", word))

def is_slash(word: Word):
    token=word.un_normalized
    if "/" in token and len([x for x in token.split("/") if x.strip()!=""])==2 and all(x.isnumeric() for x in token.split("/")): return True
    return False


# returns 0 if complex and needs default normalization (part by part), 1 if special and -1 if nothing
def is_complex(config, word: Word, last_word):
    un_normalized = word.un_normalized
    if len(un_normalized) > 1 and un_normalized[-1] == "." and last_word:
        un_normalized = un_normalized[:-1]
    sloLetters = "[a-zčšćđžA-ZČŠĆĐŽ]"

    # words like in/ali are ok (not complex)
    if match("^" + sloLetters + "+[/]" + sloLetters + "+$", un_normalized):
        return False

    return bool(match("[(:\"']*(" + sloLetters + "+[&/.@-]" + sloLetters + "+)[)!?:,'‘»”\"]*", un_normalized)) or \
           bool(match(
               "[(:\"']*((" + sloLetters + "+[-/&]?\d+)|(\d+[&/@-]?" + sloLetters + "+)|(\d+[&/@-]\d+)|(" + sloLetters + "+[&/@-]" + sloLetters + "+))+[)!?.:,'‘»”\"]*",
               un_normalized))


# returns true if number string is decimal, integer or ordinal number
def is_number(sentence: Sentence, word_index, word):
    return is_decimal_number(word) or is_whole_number(word, False, sentence) or is_ordinal_number(sentence, word_index)


def is_date_without_year(word: str):
    if search("^[0-9]{1,2}[.][0-9]{1,2}[.]$", word):
        dot_index = word.index('.')
        day = int(word[:dot_index])
        month = int(word[dot_index + 1:dot_index + 3].replace(".", ""))
        return (32 > day > 0) and (13 > month > 0)
    else:
        return False


def is_date_with_year(word: str):
    if search("^[0-9]{1,2}[.][0-9]{1,2}[.]([0-9]{2}|[1-9][0-9]{3})$", word):
        dot_index = word.index('.')
        day = int(word[:dot_index])
        month = int(word[dot_index + 1:dot_index + 3].replace(".", ""))
        return (32 > day > 0) and (13 > month > 0)
    else:
        return False


# returns true if date, but only year
def is_date_year(config, sentence: Sentence, word_index, is_last_word):
    token = sentence.get_word(word_index).un_normalized
    if not is_whole_number(token, is_last_word, sentence) or len(token)>4 or dot_in_the_middle(token):
        return False

    prev_words = get_previous_words(sentence, 2, word_index)
    match_count = bag_of_words_matches(prev_words, bag_of_words_date_year)

    if match_count > 0 or (word_index > 0 and sentence.get_word(word_index - 1).type == "date"):
        return True
    else:
        return False


def is_decimal_number(word: str):
    if match("^.+[,].+$", word) and not (word.endswith("-") or word.endswith("–")):
        separator_index = word.find(',')
        return (word[:separator_index].replace("+", "").replace("-", "").replace("–", "").isnumeric() and not is_fraction(word[:separator_index].replace("+", "").replace("-", "").replace("–", ""))) and bool(match("^[0-9]+([-–]\D*)?$", word[separator_index + 1:]))
    return False


def is_decimal_number_additions(sentence, i):
    word=sentence.get_word(i).un_normalized
    if i<sentence.length()-1 and (word.endswith("-") or word.endswith("–")) and is_decimal_number(word[:-1]) and sentence.get_word(i+1).un_normalized.isalpha(): return True
    return False

# returns true if integer
def is_whole_number(word: str, last_word: bool, sentence: Sentence, next_word=None, tokenize_sentence=False):
    if not sentence.tags:
        sentence.tag()
    if len(word) > 0 and word[-1] == "." and next_word and next_word.tag["upos"] == "ADP" and next_word.un_normalized.istitle():
        return True
    if not last_word and not tokenize_sentence and len(word) > 0 and word[-1] == ".":
        return False
    elif next_word and len(word) > 0 and word[-1] == "." and next_word.tag["upos"] != "PROPN":
        return False
    
    return bool(match("(^[-+–]?([1-9]|[1-9][0-9]|[1-9][0-9][0-9])([.]\d{3})*$)|(^[-+–]?\d+$)", word))


def is_ordinal_number(sentence: Sentence, word_index):
    if not sentence.tags:
        sentence.tag()
    word=sentence.get_word(word_index).un_normalized
    if not bool(match("^\d+[.]$", word)):
        return False

    next_word = sentence.get_word(word_index + 1) if not sentence.is_last_word(word_index) else None

    if next_word:
        if (next_word.tag["upos"] == "NOUN" and not next_word.un_normalized.istitle()) or \
                next_word.tag["upos"] == "PROPN" or \
                (next_word.tag["upos"] == "ADJ" and not next_word.un_normalized.istitle()):
            return True
        elif next_word.un_normalized.istitle():
            return False
    return True


def is_unit(config, token):
    units_with_prefixes = [prefix + unit for prefix in prefixes.keys() for unit in config['unit']['set']]
    if token in units_with_prefixes or ("/" in token and all(p in units_with_prefixes for p in token.split("/"))): return True
    return False

def is_number_with_unit(config, token):
    # Attempt to match the pattern to the input string
    r = match(r'^(\d+)(\D+)$', token)
    
    if r:
        # If the pattern matches, extract the number and text parts
        number_part = r.group(1)
        text_part = r.group(2)

        return is_unit(config, text_part)

    return False

def is_symbol(config, word: str):
    symbols = set(config['symbol']['set'].keys()) - {",", ".", ":", "!", '"', "?"}
    return word in symbols


def is_abbreviation(config, sentence: Sentence, token, word_index):
    if token.lower() in config["abbr"]["set"].keys():
        return True
    return False    

def is_acronym(config, sentence: Sentence, word_index):
    word = sentence.get_word(word_index).un_normalized
    for acr in [d['regex'] for d in config['acronym']['set']]:
        if match("^[(]?" + acr + "[,.?!;)]*$", word):
            return True
    return False


def is_hour(sentence: Sentence, word_index):
    word = sentence.get_word(word_index).un_normalized
    prev_word = sentence.get_word(word_index - 1)
    prev_prev_word = sentence.get_word(word_index - 2)

    if word_index > 1 and \
            sentence.get_word(word_index - 1).un_normalized == "in" and sentence.get_word(word_index - 2).type == "date":
        return False

    words_prev = get_previous_words(sentence, 2, word_index)
    words_after = get_next_words(sentence, 3, word_index)
    match_count_prev = bag_of_words_matches(words_prev, bag_of_words_hour_left_side)
    match_count_after = bag_of_words_matches(words_after, bag_of_words_hour_right_side)

    if prev_word and match("([Ii]n)|[-–]", prev_word.un_normalized) and prev_prev_word and prev_prev_word.type == "hour":
        pass
    elif match_count_prev == 0 and match_count_after == 0:
        return False

    return bool(match("^((([0-1]?[0-9]|2[0-3])[:.][0-5][0-9])|24[:.]00)$", word))


# def is_preposition(word: str):
#     for case in prepositions:
#         for preposition in case:
#             if match("^" + preposition + "$", word):
#                 return True
#     return False


def is_special_unit(config, sentence: Sentence, word_index):
    word = sentence.get_word(word_index).un_normalized
    units_with_prefixes_regex = "|".join([prefix + unit if unit not in ["$", "."] else prefix + "\\" + unit for prefix in prefixes.keys() for unit in config['unit']['set']])
    # e.g. 100/min
    return bool(match("^\d+(,\d+)?([-–]\d+(,\d+)?)?([x×])?[/](" + units_with_prefixes_regex + ")$", word))

# returns number of parts or -1, if not a phone number
def is_phone_number(sentence: Sentence, word_index):
    concat = ""
    # phone numbers consisting of 2 parts
    if word_index + 1 < sentence.length():
        concat += sentence.get_word(word_index).un_normalized + " " + sentence.get_word(word_index + 1).un_normalized
        if match("^\d{3} \d{4}$", concat):
            return 2  # nnn nnnn
    else:
        return -1

    # phone numbers consisting of 3 words
    if word_index + 2 < sentence.length():
        concat += " " + sentence.get_word(word_index + 2).un_normalized
        if match("(^\d{3} \d{3} \d{3}$)|"
                 "(^\d{2} \d{4} \d{3}$)|"
                 "(^\d{3} \d{2} \d{2}$)", concat):
            return 3  # nnn nnn nnn | nn nnnn nnn | nnn nn nn
    else:
        return -1

    # phone numbers consisting of 4 words
    if word_index + 3 < sentence.length():
        concat += " " + sentence.get_word(word_index + 3).un_normalized
        if match("(^\\d{2} \\d{3} \\d{2} \\d{2}$)|"
                 "(^[+]\d{3} \d{2} \d{3} \d{3}$)|"
                 "(^[+]\d{3} \d{2} \d{4} \d{3}$)|"
                 "(^\d{5} \\d{2} \\d{3} \\d{3}$)|"
                 "(^[+]+\d{3} \\(\d\\)\\d{2} \\d{3} \\d{3}$)", concat):
            return 4  # nn nnn nn nn | +nnn nn nnn nnn | +nnn nn nnnn nnn | nnnnn nn nnn nnn | +nnn (n)nn nnn nnn
    else:
        return -1

    # phone numbers consisting of 5 words
    if word_index + 4 < sentence.length():
        concat += " " + sentence.get_word(word_index + 4).un_normalized
        if match("(^[+]\d{3} \\d \\d{3} \\d{2} \\d{2}$)|"
                 "(^\d{5} \\d \\d{3} \\d{2} \\d{2}$)|"
                 "(^[+]\d{3} \\(\d\\)\\d \\d{3} \\d{2} \\d{2}$)", concat):
            return 5  # +nnn n nnn nn nn | nnnnn n nnn nn nn | +nnn (n)n nnn nn nn
    else:
        return -1

    return -1

def is_result(sentence: Sentence, word_index: int):
    token=sentence.get_word(word_index).un_normalized
    surrounding_tokens=slicer([x.un_normalized for x in sentence.words], word_index, context=10)
    surrounding_types=slicer([x.type for x in sentence.words], word_index, context=10)
    match_count = bag_of_words_matches(surrounding_tokens, bag_of_words_result)
    if (":" in token and all(p.isnumeric() and not is_fraction(p) for p in token.split(":"))) and (match_count or "result" in surrounding_types):
        return 1
    elif word_index<sentence.length()-2 and (token.isnumeric() and not is_fraction(token) and sentence.get_word(word_index+1).un_normalized==":" and sentence.get_word(word_index+2).un_normalized.isnumeric() and not is_fraction(sentence.get_word(word_index+2).un_normalized)) and (match_count or "result" in surrounding_types):
        return 2
    return False


def is_section(token):
    return bool(match("^\d+([.]\d+)+$", token))


def is_email(token):
    email_regex = "^(?:[a-zA-Z0-9!#$%&'*+\\/=?^_`{|}~-]+(?:\\.[a-z0-9!#$%&'*+\\/=?^_`{|}~-]+)*" \
                  "|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]" \
                  "|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?" \
                  "|\\[(?:(?:25[0-5]|2[0-4][0-9]" \
                  "|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?" \
                  "|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]" \
                  "|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\\])$"
    return bool(match(email_regex, token))


# returns 0 if integer, 1 if ordinal number and -1 if neither
def is_roman_numeral(sentence: Sentence, word_index: int):
    word=sentence.get_word(word_index).un_normalized
    previous_word: Word = sentence.get_word(word_index - 1) if word_index > 0 else None
    if bool(match("^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", word[:-1])) or bool(match("^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", word)):
        if not sentence.tags:
            sentence.tag()
        if previous_word and word[-1] == "." and len(word) > 1 and previous_word.tag["upos"] == "PROPN" and bool(
                match("^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", word[:-1])):
            return 1
        elif sentence.is_last_word(word_index) and word[-1] == "." and len(word) > 3 and bool(match("^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", word[:-1])) or \
                previous_word and len(word) >= 3 and bool(match("^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", word)):
            return 0
        else:
            return -1
    else:
        return -1

def is_interval(config, sentence: Sentence, word_index: int):
    # hour / date / number interval
    token=sentence.get_word(word_index).un_normalized
    interval_type = None

    if (not ("-" in token or "–" in token)) or (len([x for x in token.replace("–", "-").split("-") if x!=""])!=2): return False

    parts=[x for x in token.replace("–", "-").split("-") if x!=""]

    if all((is_numeric(x) or is_decimal(x)) for x in parts):
        return "number"
        
    if all(isordinal(x) for x in parts):
        return "ordinal_number"
    
    if match("^[0-9]{1,2}[.][0-9]{1,2}[.]([0-9]{2}|[1-9][0-9]{3})?[-–][0-9]{1,2}[.][0-9]{1,2}[.]([0-9]{2}|[1-9][0-9]{3})?$", token) or \
       match("^[0-9]{1,2}[.][-–][0-9]{1,2}[.][0-9]{1,2}[.]([0-9]{2}|[1-9][0-9]{3})?$", token):
        return "date"
    
    if match("^((([0-1]?[0-9]|2[0-3])[:.][0-5][0-9])|24[:.]00)[-–]((([0-1]?[0-9]|2[0-3])[:.][0-5][0-9])|24[:.]00)$", token):
        return "hour"
    if all(is_times(part) for part in parts) or (is_times(parts[-1]) and all((is_numeric(part) or is_decimal(part)) for part in parts[:-1])):
        return "times"

    else:
        return False

def is_times(token):
    if (token.endswith("x") or token.endswith("×")) and (token[:-1].isnumeric() or is_decimal(token[:-1])): return True
    return False

def is_multiplication(token):
    if (not ("x" in token or "×" in token)) or (len([x for x in token.replace("×", "x").split("x") if x!=""])!=2): return False
    parts=[x for x in token.replace("×", "x").split("x") if x!=""]
    if all((is_numeric(x) or is_decimal(x)) for x in parts): return True
    return False


def is_link(config, word: str):
    return bool(match("^((https?://www\.)|(https?://)|(www\.))[^\s.]+\.[a-z]+(/\D+)*$", word))


def is_special_fraction(word: str):
    return bool(match("[+-]?(↉|⅒|½|⅓|¼|⅕|⅙|⅐|⅛|⅑|⅔|⅖|¾|⅗|⅜|⅘|⅚|⅝|⅞)", word))


def is_alnum(token):
    if token.replace("-", "").isalnum() and not token.replace("-", "").isalpha() and not token.replace("-", "").isnumeric():
        return True
    elif "-" in token and is_decimal(token.split("-")[0]) and token.split("-")[1].isalpha():
        return True
    return False

"""
vvvv HELPER METHODS vvvv
"""


# returns number of matches between words ang bag
def bag_of_words_matches(words, bag):
    matches = 0
    for regex in bag:
        for word in words:
            if match("[('\":;\[]*" + regex + "[!?,:)'\";]*", word):
                matches += 1
                break
    return matches


def contains_number(word: str):
    return bool(match("^.*\d+.*$", word))


def get_previous_words(sentence: Sentence, lookback, word_index):
    if lookback > word_index:
        return [word.un_normalized for word in sentence.words[:word_index]]
    else:
        return [word.un_normalized for word in sentence.words[(word_index - lookback):word_index]]


def get_next_words(sentence: Sentence, lookahead, word_index):
    if lookahead + word_index > sentence.length():
        return [word.un_normalized for word in sentence.words[word_index + 1:]]
    else:
        return [word.un_normalized for word in sentence.words[word_index + 1:word_index + 1 + lookahead]]


def is_nr_unit_combo(i, toks, config):
    tok=toks[i]
    if i<len(toks)-1 and (is_numeric(tok) or is_decimal(tok) or is_fraction(tok)) and is_unit(config, toks[i+1]): return True
    return False
