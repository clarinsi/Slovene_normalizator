import datetime
import itertools
from locale import normalize
import logging
from typing import List

from slovene_normalizator.utils_helpers import *
from slovene_normalizator import utils, word_type_check
from slovene_normalizator.word import Word
from slovene_normalizator.sentence import Sentence
from re import findall, match, search
import slovene_normalizator.declinator as dcl

from slovene_normalizator.declinator import get_abbreviation_declension_noun, get_abbreviation_declension_adj


decimal_notation = {
    "1": "cela",
    "2": "celi",
    "3": "cele",
    "4": "cele"
}
number_mapping = {
    0: "singular",
    1: "dual",
    2: "plural"
}
case_mapping = {
    0: "nominative",
    1: "genitive",
    2: "dative",
    3: "accusative",
    4: "locative",
    5: "instrumental"
}
gender_mapping = {
    0: "masculine",
    1: "feminine",
    2: "neutral"
}
math_symbols = {
    "+": "plus",
    "-": "minus",
    "/": "deljeno",
    "*": "krat",
    "×": "krat",
    "=": "je enako",
    "<": "je manj kot",
    ">": "je več kot"
}
special_fractions_denominator = {
    "¼": (1, 4), "½": (1, 2),
    "¾": (3, 4), "⅐": (1, 7),
    "⅑": (1, 9), "⅒": (1, 10),
    "⅔": (2, 3), "⅓": (1, 3),
    "⅕": (1, 5), "⅖": (2, 5),
    "⅗": (3, 5), "⅘": (4, 5),
    "⅙": (1, 6), "⅚": (5, 6),
    "⅛": (1, 8), "⅜": (3, 8),
    "⅝": (5, 8), "⅞": (7, 8), "↉": (0, 3)}

fraction_denominator_pronunciation_suffixless = {
    "2": "polovica",
    "3": "tretjina",
    "4": "četrtina",
    "5": "petina",
    "6": "šestina",
    "7": "sedmina",
    "8": "osmina",
    "9": "devetina",
    "10": "desetina"
}

months_to_words={"1": "januar", "2": "februar", "3": "marec", "4": "april", "5": "maj", "6": "junij",
                "7": "julij", "8": "avgust", "9": "september", "10": "oktober", "11": "november", "12": "december"}

#roman to normal, potem pa normaliziraj
def create_roman_numeral(token, declension):
    if token.endswith("."):
        roman_numeral = create_ordinal_number(str(utils.roman_numeral_to_int(token)), declension[0], declension[1], declension[2], None)
    else:
        roman_numeral = create_number(str(utils.roman_numeral_to_int(token)), declension[0], declension[1], declension[2], None)
    return roman_numeral

def create_complex_duration(config, token):
    parts = findall("\d+", token)

    norms=[]
    mins=get_basic_nr(parts[0])
    secs=get_basic_nr(parts[1])
    milis=get_basic_nr(parts[2])
    if mins.endswith("dva"):
        mins=mins[:-3]+"dve"
    if secs.endswith("dva"):
        secs=secs[:-3]+"dve"
    if milis.endswith("dva"):
        milis=milis[:-3]+"dve"
    
    sklon="imenovalnik" if 0<int(parts[0])<5 else "rodilnik"
    norms.extend([mins, create_unit(config, "min", ["ženski", sklon, get_nr_from_int(parts[0])])+","])
    sklon="imenovalnik" if 0<int(parts[1])<5 else "rodilnik"
    norms.extend([secs, create_unit(config, "s", ["ženski", sklon, get_nr_from_int(parts[1])])])
    sklon="imenovalnik" if 0<int(parts[2])<5 else "rodilnik"
    norms.extend(["in", milis, get_correct_form(lema="stotinka", POS="samostalnik", spol="ženski", sklon=sklon, stevilo=get_nr_from_int(parts[1]))])

    return " ".join(norms)


def create_slash(config, sentence, i):
    toks=sentence.tokens
    token=sentence.get_word(i).un_normalized
    parts=token.split("/")
    if any(x in slicer(toks, i) for x in ["RR", "tlak", "tlaka", "mmHg", "Apgar", "Apgarjeva", "Apgarjevi", "Apgarju", "EEG", "številka", "Številka", "številko", "Številko"]):
        return " skozi ".join([create_number(x, None, utils.integer_pronunciation(config, sentence, i, sentence.get_word(i).un_normalized)) for x in parts])
    elif any(x in slicer(toks, i) for x in ["VAS", "lestvica", "lestvici", "jakost", "jakosti", "sistolni", "sistolnega", "jakostjo", "ocenil", "ocenila", "ocenim", "oceni", "ocena", "oceno", "ocene", "točke", "točk", "točki", "Riva-Rocci", "Riva", "Rocci"]):
        return " od ".join([create_number(x, None, utils.integer_pronunciation(config, sentence, i, sentence.get_word(i).un_normalized)) for x in parts])
    else:
        return " skozi ".join([create_number(x, None, utils.integer_pronunciation(config, sentence, i, sentence.get_word(i).un_normalized)) for x in parts])


def create_math_operation(config, token):
    parts = findall("\d+,\d+|\d+|[+\-/*×=<>]", token)
    normalized = []
    after_division = False

    for part in parts:
        if part in math_symbols:
            normalized.append(math_symbols[part])
            after_division = (part == "/")
            continue

        if match("\d+,\d+", part):
            number = create_decimal_number(part)
        elif is_fraction(part):
            number=create_fraction(config, part, None)
        else:
            number = create_number(part, None)

        if after_division:
            if number[0] in ["c", "č", "f", "h", "k", "p", "s", "š", "t"]:
                normalized.append("s")
            else:
                normalized.append("z")
            after_division = False

        normalized.append(number)
    
    return " ".join(normalized)

def create_complex_word(config, token, last_word, default_normalization=False):
    supported_characters = list(config['symbol']['set'].keys())
    parts = findall("[a-zčšćđžA-ZČŠĆĐŽ]+|\d+|[().,\-:?\"!;" + "".join(supported_characters) + "]", token)
    parts_normalized: List[Word] = []
    normalized = ""

    for part_index, part in enumerate(parts):
        part_word = Word(part)
        if len(parts) <= 3 and word_type_check.is_unit(config, part) and part_index > 0 and parts_normalized[part_index - 1].type == "number":
            part_word = create_unit(config, part, parts_normalized[part_index - 1].value)
            normalized += part_word.toString() + " "
        elif match("-", part):
            if len(parts) == 3 and match("\d+", parts[part_index - 1]) and match("[a-zžđšćč]+", parts[part_index + 1]):
                normalized = normalized.replace(" ", "")
            elif len(parts) >= 3 and match("\D+", parts[part_index - 1]) and (part_index<len(parts)-1 and match("\d+", parts[part_index + 1])):
                pass
            elif part_index < len(parts) - 1 and match("[a-z]+", parts[part_index + 1]):
                part_word.normalized = "-"
                normalized = normalized.rstrip() + "-"
            else:
                part_word.normalized = "-"
                normalized = normalized.rstrip() + "-"
        elif match("\d+", part):
            # if number starts with 0, it's probably pronounced number by number
            if match("0.+", part):
                normalized = normalized + create_number(part, pronunciation="digits")+ " "
            else:
                part_word = create_number(part)
                normalized += part_word + " "
        elif match("[@#&]", part):
            char_index = supported_characters.index(part)
            part_word.normalized = config['symbol']['set'][part]
            part_word.type = "symbol"
            normalized += part_word.toString() + " "
        elif match("[.]", part) and not part_index == len(parts) - 1:
            part_word.normalized = "pika"
            part_word.type = "regular"
            normalized += part_word.toString() + " "
        elif match("[.]", part) and part_index == len(parts) - 1 and last_word:
            part_word.type = "punctuation"
            normalized = normalized.rstrip() + "."
        elif match("[/]", part):
            char_index = supported_characters.index(part)
            part_word.normalized = config['symbol']['set'][part]
            part_word.type = "punctuation"
            normalized += part_word.toString() + " "
        elif match("[(),:;?!]", part) and not default_normalization:
             part_word.normalized = part
             normalized = normalized.rstrip() + part + " "
        elif part in supported_characters and default_normalization:
            char_index = supported_characters.index(part)
            part_word.normalized += config['symbol']['set'][part] + " "
            normalized += config['symbol']['set']["part"] + " "
        else:
            part_word.normalized = part
            part_word.type = "regular"
            normalized += part_word.toString() + " "
        parts_normalized.append(part_word)

    return normalized.strip()


def create_date_without_year(config, token, declension):
    if isinstance(token, str):
        dot_position = token.find('.')
        day = token[:dot_position]
        month=token[dot_position + 1:]
    elif isinstance(token, list):
        day, month = token

    if day[0] == "0":
            day = day[1:]
    if month[0] == "0":
            month = month[1:]
    if config["num"]["subtypes"]['date']['pronunciation_month'] == "month":
        month=get_correct_form(months_to_words[str(int(month.replace(".", "")))], "samostalnik", spol=declension[1], sklon=declension[0], stevilo=declension[2])
    else:
        month=get_correct_form(get_nr_lemma(month.replace(".","")+"."), "števnik", spol=declension[1], sklon=declension[0], stevilo=declension[2])

    if day[0] == "0":
            day = day[1:]
    day=get_correct_form(get_nr_lemma(day.replace(".", "")+".", False), "števnik", spol=declension[1], sklon=declension[0], stevilo=declension[2])
        
    if isinstance(token, str):
        return " ".join([day, month])
    else:
        return [day, month]

def create_date_with_year(config, token, declension, year_only=False):
    if year_only:
        if config["num"]["subtypes"]['date']['pronunciation_year'] == "special" and match("(15\d{2})|(16\d{2})|(17\d{2})|(18\d{2})|(19\d{2})", str(token)):
            year = get_nr_lemma(year[:2]) + "sto " + get_nr_lemma(year[2:], True)
            return year
        else:
            year=get_nr_lemma(token, True)
            return year
    else:
        if isinstance(token, str):
            first_dot_position = token.find('.')
            second_dot_position = token.find('.', first_dot_position + 1)

            day = token[:first_dot_position]
            month=token[first_dot_position + 1:second_dot_position]
            year=token[second_dot_position + 1:]
        elif isinstance(token, list):
            day, month, year = token
        if day[0] == "0":
            day = day[1:]
        if month[0] == "0":
            month = month[1:]
        day=create_ordinal_number(day.replace(".","")+".", [declension[1], declension[0], declension[2]])
        
        if config["num"]["subtypes"]['date']['pronunciation_month'] == "month":
            month=get_correct_form(months_to_words[str(int(month.replace(".", "")))], "samostalnik", spol=declension[1], sklon=declension[0], stevilo=declension[2])
        else:
            month=create_ordinal_number(month.replace(".","")+".", [declension[1], declension[0], declension[2]])
        if config["num"]["subtypes"]['date']['pronunciation_year'] == "special" and match("(15\d{2})|(16\d{2})|(17\d{2})|(18\d{2})|(19\d{2})", year):
            year = get_nr_lemma(year[:2]) + "sto " + get_nr_lemma(year[2:], True)
        else:
            year=get_nr_lemma(year, True)
    if isinstance(token, str):
        return " ".join([day, month, year])
    else:
        return [day, month, year]
    

def create_symbol(config, token):
    symbol_set = config["symbol"]["set"]
    symbols = list(token)
    norms=[]
    for s in symbols:
        if s in symbol_set:
            norms.append(symbol_set[s])
        else:
            norms.append(s)
        
        return " ".join(norms)

def create_abbreviation(config, token, declension):
    abbrs=config["abbr"]["set"]
    if token in abbrs and list(abbrs[token].values())[0] in ["FIXED", "ADV"]:
        return list(abbrs[token].keys())[0]
    lema, tempdict = make_lemma_and_tempdict(config, token)
    try:
        POS=sync_names[list(abbrs[token].values())[0]]
        živost=declension[3] if len(declension)==4 else None
        normalized_word=get_correct_form(lema, POS, spol=declension[0], sklon=declension[1], stevilo=declension[2], živost=živost, minidict=tempdict)
    except NotImplementedError:
        normalized_word=last_resort(lema, tempdict)
    return normalized_word

def create_hour(token, declension):
    separator_index = token.find(":")
    if separator_index == -1:
        separator_index = token.find(".")
    hour = token[:separator_index]
    minute = token[separator_index + 1:]
    hour_part = (create_number(hour.replace(".", ""), declension) if isinstance(declension, list) else get_nr_lemma(hour.replace(".", ""), True)) if hour not in ["24", "00"] else get_correct_form("polnoč", "samostalnik", spol="ženski", sklon=declension[1], stevilo="ednina")
    
    if minute.startswith("0"):
        minute_part="nič "+get_basic_nr(str(int(minute)))
    elif int(minute)==0:
        minute_part=""
    else:
        minute_part = get_basic_nr(minute)

    normalized=" ".join([hour_part, minute_part])

    return normalized

def create_number(token, declension=None, pronunciation="regular", basic=None):
    if basic!=None: return get_nr_lemma(token, basic)
    predznaki={"+": "plus", "-": "minus", "–": "minus", "±": "plus minus"}
    normalized=[]
    if any(token.startswith(sign) for sign in predznaki):
        normalized=[predznaki[char] for char in token if char in predznaki]
        token=token[len(normalized):]
    if pronunciation=="digits":
        normalized+=[get_nr_lemma(char, True) for char in token]
        return " ".join(normalized)
    if declension==None:
        " ".join(normalized+[get_nr_lemma(token, True)])

    lema=get_nr_lemma(token)
    
    if token=="0":
        return lema
    tempdict={}
    if lema in sloleks_forms_dict:
        tempdict[lema]=sloleks_forms_dict[lema].copy()
    else:
        lema=get_nr_lemma(token, False)
        tempdict=instant_tempdict(token)
    if declension:
        try:
            POS="števnik"
            try:
                normalized_word=get_correct_form(lema, POS, spol=declension[0], sklon=declension[1], stevilo=get_nr_from_int(token), minidict=tempdict)
            except KeyError:
                try:
                    normalized_word=get_correct_form(lema, "pridevnik", spol=declension[0], sklon=declension[1], stevilo=get_nr_from_int(token), minidict=tempdict)
                except (KeyError, IndexError) as e:
                    #milijon
                    try:
                        normalized_word=get_correct_form(lema, "samostalnik", spol=declension[0], sklon=declension[1], stevilo=declension[2], minidict=tempdict)
                    except KeyError:
                        normalized_word=get_correct_form(lema, "samostalnik", spol=declension[0], sklon=declension[1], stevilo=get_nr_from_int(token), minidict=tempdict)

        except NotImplementedError:
            normalized_word=get_nr_lemma(token, True)
    else:
        normalized_word=get_nr_lemma(token, True)

    return " ".join(normalized+[normalized_word])

def number_creator(tok, declension=None, pronunciation="regular", basic=None):
    tok=tok.replace(".", "")
    if is_decimal(tok): return create_decimal_number(tok)
    if is_numeric(tok): return create_number(tok, declension, pronunciation, basic)

def create_alnum_word(token):
    if "-" in token:
        toks=token.split("-")
        if len(toks)==2 and toks[0].isnumeric() and toks[1].isalpha():
            if toks[0]=="1":
                nr="eno"
            elif toks[0]=="2":
                nr="dvo"
            else:
                nr=get_nr_lemma(toks[0], True)
            return "".join([nr.replace(" ", ""), toks[1]])
        elif len(toks)==2 and toks[0].isalpha() and toks[1].isnumeric():
            nr=get_nr_lemma(toks[1], True)
            return " ".join([toks[0], nr])
        elif len(toks)==2 and is_decimal(toks[0]) and toks[1].isalpha():
            return create_decimal_number(toks[0])+toks[1]
        else: #npr. 'D-4D'
            return " ".join([create_alnum_word(x) if word_type_check.is_alnum(x) else create_number(x, None, "digits") if word_type_check.is_numeric(x) else x for x in toks])
    else:
        parts=[]
        part_token=token
        while search("\d+", part_token):
            S=search("\d+", part_token).span(0)
            parts.extend([part_token[:S[0]], part_token[S[0]:S[1]]])
            part_token=part_token[S[1]:]
        if part_token:
            parts.append(part_token)
        normalized=" ".join([get_nr_lemma(p, True) if p.isnumeric() and len(p)<4 else " ".join([get_nr_lemma(char, True) for char in p]) if p.isnumeric() and len(p)>3 else p for p in parts])
        return normalized

def create_decimal_number(token):
    sign = ""
    if token[0] == "-" or token[0] == "–":
        sign = "minus"
        token = token[1:]
    elif token[0] == "+":
        sign = "plus"
        token = token[1:]
    nr, decimal = token.split(",")
    whole_part = get_nr_lemma(nr, True)
    if nr=="2":
        whole_part="dve"
    
    if decimal.startswith("0") or len(decimal)>2:
        decimal_part=" ".join([get_nr_lemma(char, True) for char in decimal])
    else:
        decimal_part=get_nr_lemma(decimal, True)
    #cela
    if nr=="1" or (len(nr)>2 and int(nr[-2:])==1):
        comma="cela"
    elif nr=="2" or (len(nr)>2 and int(nr[-2:])==2):
        comma="celi"
    elif nr in ["3", "4"] or (len(nr)>2 and int(nr[-2:]) in [3, 4]):
        comma="cele"
    else:
        comma="celih"
    normalized = " ".join([sign, whole_part, comma, decimal_part])
    return normalized.strip()

def create_unit(config, token, declension, lema=None, tempdict=None):
    if not (lema and tempdict):
        Unt=get_basic_unit(config, token)
        lema=get_basic_unit(config, token, False)
        tempdict=instant_tempdict(Unt)
    POS="samostalnik"
    return get_correct_form(lema, POS, spol=declension[0], sklon=declension[1], stevilo=declension[2], minidict=tempdict)

def create_unit_adj(config, token, declension, lema=None, tempdict=None):
    if not (lema and tempdict):
        Unt=get_basic_unit(config, token)
        lema=get_basic_unit(config, token, False)
        tempdict=instant_tempdict(Unt)
    POS="pridevnik"
    return get_correct_form(lema, POS, spol=declension[0], sklon=declension[1], stevilo=declension[2], minidict=tempdict)

def create_complex_unit_1(config, token):
    left_side, unit = token.split("/")

    if "-" in left_side or "–" in left_side and config["interval"]["normalize"] == "true":
        left_side = create_interval(config, left_side, "number")
    elif word_type_check.is_decimal_number(left_side) and config["num"]["subtypes"]["decimal_number"]["normalize"] == "true":
        left_side = create_decimal_number(left_side)
    elif left_side.isnumeric() and not word_type_check.is_special_fraction(left_side) and config["num"]["subtypes"]["number"]["normalize"] == "true":
        left_side = create_number(left_side)
    elif word_type_check.is_times(left_side):
        left_side=create_times(left_side)
    else:
        raise NotImplementedError("complex unit with unknown type")

    if config["unit"]["normalize"] == "true":
        lema, tempdict= make_lemma_and_tempdict(config, unit)
        unit = create_unit(config, unit, [None, "tožilnik", "ednina"], lema, tempdict)

    return " na ".join([left_side, unit]) if config["unit"]["normalize"]=="true" else "/".join([left_side, unit])


def create_number_and_unit(config, token, sentence, word_index):
    r = match(r'^(\d+)(\D+)$', token)
    
    number_part = r.group(1)
    unit = r.group(2)
    
    if config["unit"]["normalize"] == "true":
        lema, tempdict= make_lemma_and_tempdict(config, unit)
        minidicts=[word.tag for word in sentence.words]
        N = next_whole(word_index, minidicts)
        if N and minidicts[N] and minidicts[N]["upos"] in ['NOUN'] and minidicts[N]["feats"].split('|')[0] in ["Case=Ins"]:
            update_minidict(sentence, word_index, lema + 'ski',  POS="pridevnik")  # this word is adjective
            main_declension=get_abbreviation_declension_adj(config, sentence, word_index, lema, tempdict) # figure out the correct form (this checks the next word mostly)
            tempdict[lema+"ski"] = sloleks_forms_dict[lema + "ski"].copy()
            unit = create_unit_adj(config, unit, main_declension, lema + "ski", tempdict) # this returns None ....
            number_part = create_number(number_part, [None, "imenovalnik", "ednina"])
            if number_part.endswith("ena"): number_part = number_part[:-3] + "en"
            if number_part.endswith("dva"): number_part = number_part[:-3] + "dvo"
            return "".join([number_part, unit])
        else:
            try:
                
                main_declension = get_abbreviation_declension_noun(config, sentence, word_index, lema, tempdict)
                main_declension[2] = get_nr_from_int(number_part)

                declension = [main_declension[0], main_declension[1], main_declension[2]]

                if len(str(number_part))>2: nr=int(str(number_part)[-2:])
                else: nr = int(number_part)
                if nr > 4 and declension[1] in ["imenovalnik", "tožilnik"]:
                    declension[1] = "rodilnik"
            except NotImplementedError:
                main_declension=[get_gen(lema, tempdict), "rodilnik", get_nr_from_int(number_part)]
                declension = [main_declension[0], main_declension[1], main_declension[2]]
            unit = create_unit(config, unit, declension, lema, tempdict)
            number_part = create_number(number_part, main_declension)

    
    return " ".join([number_part, unit])

def create_ordinal_number(token, declension):
    lema=get_nr_lemma(token, False)
    tempdict={}
    if lema in sloleks_forms_dict:
        temp=sloleks_forms_dict[lema].copy()
        tempdict[lema]=dict([(k, temp[k]) for k in temp if k[0] in ["števnik", "pridevnik"]])
    else:
        tempdict=instant_tempdict(token)
    
    if declension:
        try:
            POS="števnik"
            živost=declension[3] if len(declension)==4 else None
            normalized_word=get_correct_form(lema, POS, spol=declension[0], sklon=declension[1], stevilo=declension[2], živost=živost, minidict=tempdict)
        except NotImplementedError:
            normalized_word=get_nr_lemma(token, True)
    else:
        normalized_word=get_basic_nr(token)
    return normalized_word

def create_phone_number(token):
    if isinstance(token, str):
        parts=[token]
    else:
        parts=token
    N=[]
    for part in parts:
        normalized = []
        for char in part:
            if char == "+":
                normalized.append("plus")
            elif char in ["(", ")"]:
                normalized.append(char)
            elif char.isdigit():
                normalized.append(get_nr_lemma(char, True))
        N.append(" ".join(normalized))

    if isinstance(token, str):
        return N[0]
    else:
        return N


def create_result(token):
    if isinstance(token, str):
        Split = token.split(":")
        home = get_nr_lemma(Split[0], True)
        away = get_nr_lemma(Split[1], True)
        return " proti ".join([home, away])
    else:
        home = get_nr_lemma(token[0], True)
        away = get_nr_lemma(token[2], True)
        return [home, "proti", away]

def create_section(token):
    return " pika ".join([get_nr_lemma(p, True) for p in token.split(".") if p!=""])

def create_interval(config, token, interval_type, prev_word=None, declension=None):
    split = token.split("-") if "-" in token else token.split("–")
    prev_token=prev_word.un_normalized if prev_word else None
    if interval_type == "number":
        if prev_token and (prev_token.lower().startswith("obdobj") or prev_token.lower().startswith("let")):
            return "od "+" do ".join([number_creator(x) for x in split])    
        return " do ".join([number_creator(x) for x in split])
    elif interval_type == "ordinal_number":
        return " do ".join([create_ordinal_number(x, declension) for x in split])
    elif interval_type == "hour":
        if (prev_token and prev_token.lower() not in ["od", "med"]) or not prev_token:
            return "od "+" do ".join([create_hour(x, ["ženski", "mestnik", "množina"]) for x in split])
        if prev_token and prev_token.lower() in ["od"]:
            return " do ".join([create_hour(x, ["ženski", "mestnik", "množina"]) for x in split])
        if prev_token and prev_token.lower() in ["med"]:
            return " in ".join([create_hour(x, ["ženski", "tožilnik", "ednina"]) for x in split])
        
    elif interval_type == "date":
        
        if prev_token and prev_token.lower() in ["med"]:
            declension=["orodnik","moški", "ednina"]
            glue=" in "
            pref=""
        else:
            declension=["rodilnik", "moški", "ednina"] 
            glue=" do "
            if prev_token and prev_token.lower() in ["od"]:
                pref=""
            else:
                pref="od "
        if match("^\d{1,2}[.]$", split[0]):
            left_part=create_ordinal_number(split[0], [declension[1], declension[0], declension[2]])
        elif match("^[0-9]{1,2}[.][0-9]{1,2}[.]$", split[0]):
            left_part = create_date_without_year(config, split[0], declension)
        else:
            left_part = create_date_with_year(config, split[0], declension)

        if match("^[0-9]{1,2}[.][0-9]{1,2}[.]$", split[1]):
            right_part = create_date_without_year(config, split[1], declension)
        
        else:
            right_part = create_date_with_year(config, split[1], declension)
        return pref+glue.join([left_part, right_part])
    elif interval_type == "times":
        return " do ".join([create_times(x) if word_type_check.is_times(x) else number_creator(x) for x in split])
    else:
        raise ValueError("OH NO. Something is wrong with this interval.")


def create_times(token):
    if token.endswith("x") or token.endswith("×") and (is_decimal(token[:-1]) or is_numeric(token[:-1])):
        if token[:-1]!="1":
            return number_creator(token[:-1], basic=True)+"krat"
        else:
            return "enkrat"
    else:
        raise ValueError("WRONG! [times]")

def create_multiplication(config, token, declension):
    split = token.split("×") if "×" in token else token.split("x")
    return " krat ".join([number_creator(x) for x in split])
    
def create_email(config, token):
    parts = findall("[a-zčšćđžA-ZČŠĆĐŽ]+|\d+|[-()@&#_/.,:?\"!;]", token)
    symbols = list(config['symbol']['set'].keys())
    normalized = ""
    for part in parts:
        if part == ".":
            normalized += "pika "
        elif part == "-":
            normalized += "minus "
        elif part in symbols:
            normalized += config['symbol']['set'][part] + " "
        elif part.isnumeric():
            if int(part)<=100 and not part.startswith("0"):
                normalized+=get_nr_lemma(part, True)+" "
            else:
                normalized+=" ".join([get_nr_lemma(d, True) for d in part])+" "
                
        else:
            normalized += part + " "

    return normalized.strip()

# for normalizing special fraction symbols
def create_fraction(config, token, declension=None):
    norm=[]
    if token[0] in ["+", "-"]:
        norm.append(math_symbols[token[0]])
        token=token[1:]
    numerator, denominator = special_fractions_denominator[token]
    sklon=declension[1] if declension else "imenovalnik"
    norm.append(create_number(str(numerator), ["ženski", sklon, get_nr_from_int(str(numerator))]))
    norm.append(get_correct_form(fraction_denominator_pronunciation_suffixless[str(denominator)], POS="samostalnik", spol="ženski", sklon=sklon, stevilo=get_nr_from_int(str(numerator))))
    return " ".join(norm)