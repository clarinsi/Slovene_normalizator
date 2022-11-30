import logging
import datetime
from re import match
import json

from copy import deepcopy
from normalizator.configatron import boolify

from normalizator.declinator import get_abbreviation_declension, get_abbreviation_declension_adj, get_abbreviation_declension_noun, get_number_declension, date_declension, get_hour_case
from normalizator.utils_helpers import *
import normalizator.creator as creator
import normalizator.utils as utils
import normalizator.word_type_check as word_type_check

from normalizator.word import Word
from normalizator.sentence import Sentence

from super_tools.word_tokenizer import word_tokenizer, spans
import super_tools.sent_split as splitter
from normalizator.configatron import *

# normalizes input text sentence by sentence and returns normalized text as string
def normalize_text(text: str, custom_config=None):
    with open(r"normalizator/util/config/basic_config.json", encoding="utf-8") as json_file:
        base_config=json.load(json_file)

    text = utils.standardize_quotes(' '.join(text.split()))
    if custom_config and custom_config!=base_config:
        config=configatron(base_config, custom_config)
    else:
        config=base_config
    # Skip normalization, if needed
    if not text or utils.skip_normalization(config, text):
        return {"input_text": text, "normalized_text": text, "status": 0, "logs": []}

    tokenize_sentences=boolify(config["tokenize_sentences"])
    
    normalized_text = []
    if tokenize_sentences:
        try:
            sentences=splitter.split_sent(text)
        except:  # if error during normalization, do not normalize that word
            try:
                sentences=splitter.split_sent_temp(text)
            except Exception as e:
                logging.error(" " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Error when normalizing sentence: " + text)
            sentences=[text]
    else:
        sentences=[text]
    lowest_status=None
    chng=[]
    for sentence in sentences:
        if not utils.skip_normalization(config, sentence):
            try:
                sentence = Sentence(sentence)
                normalized_text.append(normalize_sentence(config, sentence))
                
                if not lowest_status:
                    lowest_status=sentence.status
                elif sentence.status!=lowest_status:
                    if sentence.status<0:
                        if sentence.status<lowest_status:
                            lowest_status=sentence.status
                        else:
                            lowest_status=sentence.status
                chng.extend(sentence.track_changes())
            except Exception as e:  # if error during normalization, do not normalize that word
                logging.error(" " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Error when normalizing sentence: " + sentence.text)
                sentence.status=-2
        else:
            normalized_text.append(sentence)
    if lowest_status==1 and any(char.isnumeric() for char in " ".join(normalized_text)):
        return {"input_text": text, "normalized_text": " ".join(normalized_text), "status": 2, "logs": chng}
    return {"input_text": text, "normalized_text": " ".join(normalized_text), "status": lowest_status, "logs": chng}

def normalize_sentence(config, sentence: Sentence):
    sentence_length = sentence.length()
    toks=sentence.tokens
    sep_abbrs=dict(pair for d in [{tuple(x.split()): config["abbr"]["set"][x]}  for x in config["abbr"]["set"] if " " in x] for pair in d.items())
    if config["abbr"]["normalize"]=="true" and any(is_sublist(list(key), lower_list(toks)) for key in sep_abbrs):
        Ks=[K for K in sep_abbrs if is_sublist(list(K), lower_list(toks))]
        for K in Ks:
            Indexes=where_sublist(list(K), lower_list(toks))
            for inst in Indexes:
                if list(sep_abbrs[K].values())[0] in ["FIXED"]:
                    el=list(sep_abbrs[K].keys())[0].split("_")
                    for i in range(len(inst)):
                        word=sentence.get_word(inst[0]+i)
                        word.normalized=el[i]
                        word.status="normalized"
                        word.type="abbr"
                else:
                    tempdict={}
                    i=inst[0]
                    el=list(sep_abbrs[K].keys())[0].split("_")
                    Poses=list(sep_abbrs[K].values())[0].split("_")
                    M=get_main_abbr(config, list(sep_abbrs[K].values())[0])
                    if "+" not in el[M[0]]:
                        lema=el[M[0]]
                        tempdict[lema]=sloleks_forms_dict[lema].copy()
                    else:
                        lemmas=el[M[0]].split("+")
                        lema=lemmas[0]
                        tempdict[lema]=sloleks_forms_dict[lema].copy()
                        for l in lemmas[1:]:
                            tempdict[lema]={**tempdict[lema], **sloleks_forms_dict[l]}
                    POS=M[1]
                    try:
                        if POS=="samostalnik":
                            F=get_abbreviation_declension_noun(config, sentence, i+M[0])
                        else:
                            F=get_abbreviation_declension_adj(config, sentence, i+M[0], lema, tempdict)
                    except NotImplementedError:
                        F=[get_gen(lema, tempdict), "imenovalnik", get_nr(lema, tempdict)]
                    word=sentence.get_word(i+M[0])
                    word.normalized=get_correct_form(lema, POS, spol=F[0], sklon=F[1], stevilo=F[2], minidict=tempdict)
                    word.status="normalized"
                    word.type="abbr"
                    for ind in range(len(el)):
                        tempdict={}
                        if ind!=M[0]:
                            if "+" not in el[ind]:
                                lema=el[ind]
                                tempdict[lema]=sloleks_forms_dict[lema]
                            else:
                                lemmas=el[ind].split("+")
                                lema=lemmas[0]
                                tempdict[lema]=sloleks_forms_dict[lema].copy()
                                for l in lemmas[1:]:
                                    tempdict[lema]={**tempdict[lema], **sloleks_forms_dict[l]}
                            POS=sync_names[Poses[ind]]
                            word=sentence.get_word(i+ind)
                            word.normalized=get_correct_form(lema, POS, spol=F[0], sklon=F[1], stevilo=F[2], minidict=tempdict)
                            word.type="abbr"
                            word.status="normalized"
    i = 0
    while i < sentence_length:
        tok=toks[i]
        try:
            if config["abbr"]["normalize"]=="true" and is_abbr_chain(i, [x.normalized for x in sentence.words], config=config) and get_main_abbr(config, is_abbr_chain(i, [x.normalized for x in sentence.words], True)):
                main=get_main_abbr(config, is_abbr_chain(i, [x.normalized for x in sentence.words], True))
                before=main[1]
                I=i+before
                i-=1
                classified_word = classify_word(config, sentence, I)
            elif sentence.get_word(i+1) and sentence.get_word(i+1).processed!=True and (boolify(config["unit"]["normalize"]) and (is_numeric(tok) or is_decimal(tok)) and word_type_check.is_nr_unit_combo(i, [x.normalized for x in sentence.words], config)) \
                or (isordinal(tok) and (config["abbr"]["normalize"]=="true" and is_abbr(sentence.get_word(i+1).normalized, config))):
                i-=1
                classified_word = classify_word(config, sentence, i+2)
                
            else:
                classified_word = classify_word(config, sentence, i)
            
        except Exception as e:  # if error during normalization, do not normalize that word
            logging.error(" " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Error when normalizing word: " +
                          sentence.get_word(i).un_normalized + " EXCEPTION: " + str(e) + " IN SENTENCE: " + sentence.text)
            sentence.status=-1
        i+=1
    return make_final_sentence(config, sentence)


def classify_word(config, sentence: Sentence, word_index):

    word: Word = sentence.get_word(word_index)
    if word.status!="Normal":
        return word
    previous_word: Word = sentence.get_word(word_index - 1)  # sentence returns None if word does not exist
    next_word: Word = sentence.get_word(word_index + 1)
    after_next_word: Word = sentence.get_word(word_index + 2)
    is_last_word = sentence.is_last_word(word_index)
    word.processed=True

    if word_type_check.is_email(word.un_normalized):
        word.type = "email"
        if boolify(config[word.type]["normalize"]):
            word.normalized=creator.create_email(config, word.un_normalized)
            word.status="normalized"
        return word

    # LINK
    if word_type_check.is_link(config, word.un_normalized):
        config_modified = deepcopy(config)
        config_modified['symbol']['set']["/"] = "poševnica"
        word.type = "link"
        if boolify(config[word.type]["normalize"]):
            word.normalized = creator.create_complex_word(config_modified, word.un_normalized, is_last_word, default_normalization=True)
            word.status = "normalized"
        return word

    interval_type = word_type_check.is_interval(config, sentence, word_index)
    if interval_type:
        word.type="num"
        word.subtype=interval_type
        if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
            declension=get_abbreviation_declension_adj(config, sentence, word_index) if interval_type=="ordinal_number" else None
            word.normalized=creator.create_interval(config, word.un_normalized, interval_type, sentence.get_word(word_index-1), declension)
            word.status="normalized"
        return word
        
    if word_type_check.is_multiplication(word.un_normalized):
        word.type="num"
        word.subtype="number"
        if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
            declension=get_abbreviation_declension_adj(config, sentence, word_index) if interval_type=="ordinal_number" else None
            word.normalized=creator.create_multiplication(config, word.un_normalized, declension)
            word.status="normalized"
        return word

    if word_type_check.is_slash(word):
        word.type="complex"
        word.subtype="slash"
        if boolify(config[word.type]["normalize"]):
            word.normalized=creator.create_slash(config, sentence, word_index)
            word.status="normalized"
        return word


    if word_type_check.is_math_operation(word):
        word.type="complex"
        word.subtype="math_operation"
        if boolify(config[word.type]["normalize"]):
            word.normalized=creator.create_math_operation(config, word.un_normalized)
            word.status="normalized"
        return word
    
    if word.un_normalized.endswith("-") and word.un_normalized[:-1].isnumeric():
        word.type="complex"
        word.subtype="number"
        if boolify(config[word.type]["normalize"]) and boolify(config["num"]["normalize"]):
            word.normalized=creator.create_number(word.un_normalized[:-1], None, utils.integer_pronunciation(config, sentence, word_index, word.un_normalized[:-1]))+"-"
            word.status="alert"
        return word


    #SPECIAL FRACTION SYMBOLS
    if word_type_check.is_special_fraction(word.un_normalized):
        word.type="num"
        word.subtype="fraction"
        if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
            try:
                declension=get_abbreviation_declension_adj(config, sentence, word_index)
                word.normalized=creator.create_fraction(config, word.un_normalized, declension)
                word.status="normalized"
            except NotImplementedError:
                word.normalized=creator.create_fraction(config, word.un_normalized)
                word.status="tried"
        
        return word

    #COMPLEX DURATION (e.g. 2:15,23)
    if word_type_check.is_complex_duration(config, sentence, word_index):
        word.type="num"
        word.subtype="complex_duration"
        if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
            word.normalized = creator.create_complex_duration(config, word.un_normalized)
            word.status="normalized"
        return word

    # UNIT
    if word_type_check.is_unit(config, word.un_normalized) and previous_word and (is_numeric(previous_word.un_normalized) or is_decimal(previous_word.un_normalized) or is_interval(previous_word.un_normalized) or word_type_check.is_multiplication(previous_word.un_normalized)):
        word.type="unit"
        token=word.un_normalized
        postf=""
        if "/" in token and all(part in config["unit"]["set"] for part in token.split("/")):
            postf="na "+"na".join([creator.create_unit(config, part, [None, "tožilnik", "ednina"]) for part in token.split("/")[1:]])
        if token in config[word.type]["set"] and config[word.type]["set"][token]==token:
            word.normalized=word.un_normalized
        elif config[word.type]["normalize"]=="true":
            try:
                lema, tempdict=make_lemma_and_tempdict(config, token.split("/")[0], postf)
                declension=get_abbreviation_declension_noun(config, sentence, word_index, lema, tempdict)
                word.status="normalized"
            except NotImplementedError:
                declension=[get_gen(lema, tempdict), "rodilnik", get_nr_from_int(previous_word.un_normalized)]
                word.status="tried"
            word.normalized=creator.create_unit(config, word.un_normalized, declension, lema, tempdict)
            update_minidict(sentence, word_index, word.normalized, declension, "samostalnik")
        return word

    # SYMBOL
    if word_type_check.is_symbol(config, word.un_normalized):
        word.type="symbol"
        if boolify(config[word.type]["normalize"]):
            word.normalized=creator.create_symbol(config, word.un_normalized)
            word.status="normalized"
        return word

    # COMPLEX UNIT 1 e.g. 100/min
    if word_type_check.is_special_unit(config, sentence, word_index):
        word.type="complex_unit"
        if boolify(config["unit"]["normalize"]):
            word.normalized=creator.create_complex_unit_1(config, word.un_normalized)
            word.status="normalized"
        return word

    elif word_type_check.is_alnum(word.un_normalized):
        word.type="num"
        word.subtype = "alnum"
        if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
            word.normalized=creator.create_alnum_word(word.un_normalized)
            word.status="alert"
        return word

    #za slabo tokenizirane povedi
    elif word.un_normalized.endswith(".") and word_type_check.is_alnum(word.un_normalized[:-1]):
        word.type="num"
        word.subtype = "alnum"
        if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
            word.normalized=creator.create_alnum_word(word.un_normalized[:-1])+"."
            word.status="alert"
        return word

    # ONE WORD ABBREVIATION
    if word_index==sentence.length()-2 and word_type_check.is_abbreviation(config, sentence, word.un_normalized+".", word_index):
        word.un_normalized=word.un_normalized+"."

    if word_type_check.is_abbreviation(config, sentence, word.un_normalized, word_index):
        word.type = "abbr"
        if boolify(config[word.type]["normalize"]):
            word.un_normalized=word.un_normalized.lower()
            if word.un_normalized in config["abbr"]["set"] and list(config["abbr"]["set"][word.un_normalized].values())[0] in ["FIXED", "ADV"]:
                declension=None
                word.normalized=creator.create_abbreviation(config, word.un_normalized, declension)
                word.status="normalized"

            elif word.un_normalized in ["g."]:
                if not is_last_word and sentence.get_word(word_index+1).un_normalized.istitle():
                    declension=get_abbreviation_declension(config, sentence, word_index)
                    word.normalized=creator.create_abbreviation(config, word.un_normalized, declension)
                    word.status="normalized"
                else:
                    declension=None
            else:
                titulas=["prof.", "dr.", "mag.", "asist.", "doc.", "ing."]
                try:
                    declension=get_abbreviation_declension(config, sentence, word_index)
                    word.normalized=creator.create_abbreviation(config, word.un_normalized, declension)
                    word.status="normalized"
                    if word.un_normalized in titulas:
                        word_index+=1
                        while word_index<sentence.length() and sentence.get_word(word_index).un_normalized.lower() in titulas:
                            word=sentence.get_word(word_index)
                            word.type="abbr"
                            word.normalized=creator.create_abbreviation(config, word.un_normalized.lower(), declension)
                            word.status="normalized"
                            word_index+=1
                

                except NotImplementedError:
                    declension=None
                    lema, tempdict=make_lemma_and_tempdict(config, word.un_normalized)
                    word.normalized=last_resort(lema, tempdict)
                    word.status="tried"
                    word.tag["text"]=word.normalized
            if declension:
                POS=sync_names[list(config["abbr"]["set"][word.un_normalized].values())[0]]
                update_minidict(sentence, word_index, word.normalized, declension, POS)
        return word
    
    
    # COMPLEX WORD (words consisting of letters, numbers, symbols, ...)
    elif word_type_check.is_complex(config, word, is_last_word):
        word.type="complex"
        word.subtype="complex"
        if boolify(config[word.type]["normalize"]):
            word.normalized = creator.create_complex_word(config, word.un_normalized, is_last_word)
            word.status="normalized"
        return word
    
    # ROMAN NUMERAL
    roman_numeral_type = word_type_check.is_roman_numeral(sentence, word_index)
    if roman_numeral_type != -1:
        word.type="roman_numeral"
        sentence.get_word(word_index).un_normalized=utils.roman_numeral_to_int(sentence.get_word(word_index).un_normalized)
        if boolify(config[word.type]["normalize"]):
            try:
                declension=get_abbreviation_declension_adj(config, sentence, word_index)
                word.normalized=creator.create_ordinal_number(word.un_normalized, declension) if word.un_normalized.endswith(".") else creator.create_number(word.un_normalized, declension)
                word.status="normalized"
            except NotImplementedError:
                word.normalized=get_nr_lemma(word.un_normalized, True)
                word.status="tried"
        return word

    if word_type_check.contains_number(word.un_normalized):
        number_of_parts = word_type_check.is_phone_number(sentence, word_index)

        if number_of_parts != -1:
            norms=creator.create_phone_number(sentence.tokens[word_index:word_index+number_of_parts])
            for i in range(number_of_parts):
                word=sentence.get_word(word_index+i)
                word.type="num"
                word.subtype="phone_number"
                if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                    word.normalized=norms[i]
                    word.status="normalized"
            return word
        
        # DATE WITH YEAR (with whitespaces)
        if next_word and word_index + 2 < sentence.length() and word_type_check.is_date_with_year(
                (word.un_normalized + next_word.un_normalized + sentence.get_word(word_index + 2).un_normalized).replace(" ", "")):
            declension = date_declension(sentence, word_index)
            normalized=creator.create_date_with_year(config, [word.un_normalized, next_word.un_normalized, sentence.get_word(word_index + 2).un_normalized], declension)
            for i in range(len(normalized)):
                W=sentence.get_word(word_index+i)
                W.type="num"
                W.subtype="date"
                if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                    W.normalized=normalized[i]
                    W.status="normalized"
            return word

        # DATE WITHOUT YEAR (with whitespaces)
        if next_word and next_word.text!="." and word_type_check.is_date_without_year((word.un_normalized + next_word.un_normalized).replace(" ", "")):
            declension = date_declension(sentence, word_index)
            normalized = creator.create_date_without_year(config, [word.un_normalized, next_word.un_normalized], declension)
            for i in range(len(normalized)):
                W=sentence.get_word(word_index+i)
                W.normalized=normalized[i]
                W.type="num"
                W.subtype="date"
                W.status="normalized"
            return word

        # DATE YEAR (year only)
        if word_type_check.is_date_year(config, sentence, word_index, is_last_word):
            word.type="num"
            word.subtype="date"
            if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                word.normalized=creator.create_date_with_year(config, word.un_normalized, declension=None, year_only=True)
                word.status="normalized"
            return word

        result_type=word_type_check.is_result(sentence, word_index)
        if result_type==1:
            word.type="num"
            word.subtype="result"
            if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                word.normalized=creator.create_result(word.un_normalized)
                word.status="normalized"
            return word
        elif result_type==2:
            normalized = creator.create_result([word.un_normalized, next_word.un_normalized, sentence.get_word(word_index+2).un_normalized])
            for i in range(len(normalized)):
                W=sentence.get_word(word_index+i)
                W.type="num"
                W.subtype="result"
                if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                    W.normalized=normalized[i]
                    W.status="normalized"
            

        # WHOLE NUMBER
        if word_type_check.is_whole_number(word.text, is_last_word, sentence, next_word=next_word, tokenize_sentence=sentence.tokenized):
            word.un_normalized=word.text.replace(".", "").replace("–", "-")
            word.type="num"
            word.subtype="number"
            if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                if utils.integer_pronunciation(config, sentence, word_index, word.un_normalized) == "digits":
                    word.normalized=creator.create_number(word.un_normalized, declension=None, pronunciation="digits")
                    word.status="normalized"
                    return word
                try:
                    declension=get_number_declension(sentence, word_index)
                    word.normalized=creator.create_number(word.un_normalized, declension)
                    word.status="normalized"
                except NotImplementedError:
                    word.normalized=creator.create_number(word.un_normalized)
                    word.status="tried"
            
            return word

        # HOUR
        if word_type_check.is_hour(sentence, word_index):
            word.type="num"
            word.subtype="hour"
            if boolify(config[word.type]["normalize"]):
                declension=get_hour_case(sentence, word_index)
                word.normalized = creator.create_hour(word.un_normalized, declension)
                word.status="normalized"
            return word

        # DATE WITHOUT YEAR
        if word_type_check.is_date_without_year(word.un_normalized):
            word.type="num"
            word.subtype="date"
            if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                declension = date_declension(sentence, word_index)
                word.normalized=creator.create_date_without_year(config, word.un_normalized, declension)
                word.status="normalized"
            return word
        # DATE WITH YEAR
        if word_type_check.is_date_with_year(word.un_normalized):
            word.type="num"
            word.subtype="date"
            if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                declension = date_declension(sentence, word_index)
                word.normalized= creator.create_date_with_year(config, word.un_normalized, declension)
                word.status="normalized"
            return word
        
        # DECIMAL NUMBER
        if word_type_check.is_decimal_number(word.un_normalized):
            word.type="num"
            word.subtype="decimal_number"
            if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                word.normalized=creator.create_decimal_number(word.un_normalized)
                word.status="normalized"
            return word
        if word_type_check.is_decimal_number_additions(sentence, word_index):
            word.type="num"
            word.subtype="decimal_number"
            if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                word.normalized=creator.create_decimal_number(word.un_normalized[:-1])+word.un_normalized[-1]
                word.status="normalized"
            return word

        # SECTION
        if word_type_check.is_section(word.un_normalized):
            word.type="num"
            word.subtype="section"
            if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                word.normalized=creator.create_section(word.un_normalized)
                word.status="normalized"
            return word

        # ORDINAL NUMBER
        if word_type_check.is_ordinal_number(sentence, word_index):
            word.type="num"
            word.subtype="ordinal_number"
            if word.un_normalized.startswith("0"):
                word.un_normalized=str(int(word.un_normalized[:-1]))+"."
            if boolify(config["num"]["normalize"]) and boolify(config["num"]["subtypes"][word.subtype]["normalize"]):
                try:
                    #zakaj točno 2: ker je vmes in ali vejica
                    if sentence.get_word(word_index+2) and word_type_check.is_ordinal_number(sentence, word_index+2) and sentence.get_word(word_index+1).text.lower() in ["in", "do", "ter", ","]:
                        i=word_index+2
                        classify_word(config, sentence, i)
                        declension=sentence.get_word(i).declension if sentence.get_word(i).declension else get_abbreviation_declension_adj(config, sentence, word_index)    
                    else:
                        i=word_index
                        declension = get_abbreviation_declension_adj(config, sentence, i)
                    word.normalized=creator.create_ordinal_number(word.un_normalized, declension)
                    word.status="normalized"
                    word.declension=declension
                    if i!=word_index:
                        sentence.get_word(i).type="num"
                        sentence.get_word(i).subtype="ordinal_number"
                        sentence.get_word(i).normalized=creator.create_ordinal_number(sentence.get_word(i).un_normalized, declension)
                        sentence.get_word(i).status="normalized"

                except NotImplementedError:
                    word.normalized=get_basic_nr(word.un_normalized)
                    word.status="tried"
                    word.declension=None
            return word
        elif word_type_check.is_times(word.un_normalized):
            word.type="num"
            word.subtype="times"
            word.normalized=creator.create_times(word.un_normalized)
            word.status="normalized"
            word.declension=None

        # unknown/unsupported number format
        if boolify(config["not_supported"]["normalize"]):
        #if config["not_supported"]["normalize"] == "true":
            other = creator.create_complex_word(config, word.un_normalized, is_last_word, default_normalization=True)
            return other
        else:
            return word

    # unknown/unsupported
    if boolify(config["not_supported"]["normalize"]) and not word_type_check.is_regular_word(word.un_normalized):
        word.type="complex"
        word.subtype="unidentified"
        word.normalized=creator.create_complex_word(config, word.un_normalized, is_last_word, default_normalization=True)
        word.status="alert"
        return word

    # if none of the above, we return the word as it is
    word.type = "regular"
    return word

def make_final_sentence(config, sentence):
    normalized = sentence.text
    toks=sentence.tokens
    sentence_length=sentence.length()
    S=spans(normalized, toks)
    for word_index in range(sentence_length):
        word=sentence.get_word(word_index)
        space_before=False
        space_after=False
        
        if not word.normalized == "" and word.text!=word.normalized and ((word.type in config.keys() and config[word.type]['normalize'] != "false") or word.type in ["alnum", "complex_unit"]):
            if word_index<sentence_length-1 and sentence.get_word(word_index+1).normalized not in ["?", "!", ".", ":", ";", ",", ")", "'", '"']:
                space_after=True
            if word_index<0 and sentence.get_word(word_index-1).normalized not in ["(", '"', "'"]:
                space_before=True
            if word_index == 0 and  (utils.starts_with_capital(word.text) or word.text[0].isdigit()): 
                normalized=normalized[:S[word_index][1][0]]+title(word.toString())+utils.space(space_after)+normalized[S[word_index][1][1]:]
                toks[word_index]=title(word.toString())
                S=spans(normalized, toks)
            elif sentence.is_last_word(word_index) and \
                    (word.type == "ordinal_number" or
                        (word.type == "date" and not match("\d+", word.un_normalized)) or
                        word.type == "abbr" or
                        word.type == "cabbr"):
                        #če se konča s piko, naj se doda pika
                toks[word_index]=utils.pika(word.toString())
                normalized=normalized[:S[word_index][1][0]]+utils.space(space_before)+utils.pika(word.toString())+normalized[S[word_index][1][1]:]
                S=spans(normalized, toks)
            else:
                normalized=normalized[:S[word_index][1][0]]+utils.space(space_before)+word.toString()+utils.space(space_after)+normalized[S[word_index][1][1]:]
                toks[word_index]=word.toString()
                S=spans(normalized, toks)
    return " ".join(normalized.split())