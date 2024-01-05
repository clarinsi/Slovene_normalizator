from normalizator.utils_helpers import *
from normalizator.word import Word
from normalizator.sentence import Sentence

def get_value_if(key, dictx, defaultValue):
    if key in dictx:
        return dictx[key]
    else:
        return defaultValue

def extract_word_declension(word: Word):
    feats=dict([x.split("=") for x in word.tag["feats"].split("|")])
    pck=(get_value_if("Gender", feats, "Masc"), get_value_if("Case", feats, "Nom"), get_value_if("Number", feats, "Sing"))
    if pck==('Masc', 'Acc', 'Sing'):
        return (get_value_if("Gender", feats, "Masc"), get_value_if("Case", feats, "Nom"), get_value_if("Number", feats, "Sing"), get_value_if("Animacy", feats, "Inan"))
    else:
        return pck


def get_abbreviation_declension_adj(config, sentence: Sentence, word_index, lema=None, tempdict=None):
    i=word_index
    if not sentence.tags:
        sentence.tag()
    minidicts=[word.tag for word in sentence.words]
    word=sentence.get_word(i)
    tok=word.un_normalized
    if is_abbr(tok) and not lema and not tempdict:
        lema, tempdict = make_lemma_and_tempdict(config, word.un_normalized)
    elif isordinal(tok) or (tok.isnumeric() and not is_fraction(tok)):
        tempdict={}
        lema=get_nr_lemma(tok, False)
        if lema in sloleks_forms_dict and " " not in lema:
            tempdict[lema]=sloleks_forms_dict[lema].copy()
        else:
            tempdict=instant_tempdict(tok)
    P=prev_whole(i, minidicts)
    N=next_whole(i, minidicts)
    if i<len(minidicts)-1 and N != None and minidicts[N]["upos"] in ["ADJ"]:
        Infos=[sync_names[x] for x in get_info(minidicts[N])]
        if Infos[:3]==["moški", "tožilnik", "ednina"]:
            if minidicts[N]["text"].endswith("ega"):
                Infos[3]="da"
            elif minidicts[N]["text"].endswith("i"):
                Infos[3]="ne"
    elif i<len(minidicts)-1 and N != None and minidicts[N]["upos"] in ["NOUN"]:
        Infos=[sync_names[x] for x in get_info(minidicts[N])]
        
    elif i>0 and P != None and minidicts[P]["upos"] in ["ADJ"]:
        Infos=[sync_names[x] for x in get_info(minidicts[P])]
        if Infos[:3]==["moški", "tožilnik", "ednina"]:
            if minidicts[P]["text"].endswith("ega"):
                Infos[3]="da"
            elif minidicts[P]["text"].endswith("i"):
                Infos[3]="ne"
        
    elif i>1 and P != None and isordinal(minidicts[P]["text"]) and minidicts[P-1]["upos"] in ["ADJ"]:
        Infos=[sync_names[x] for x in get_info(minidicts[P-1])]
        if Infos[:3]==["moški", "tožilnik", "ednina"]:
            if minidicts[P-1]["text"].endswith("ega"):
                Infos[3]="da"
            elif minidicts[P-1]["text"].endswith("i"):
                Infos[3]="ne"
    elif P != None and minidicts[P]["upos"] in ["ADP"]:
        Infos=[sync_names[x] for x in get_info(minidicts[P])]
    elif any(x["upos"] == "VERB" for x in slicer(minidicts, i, 4)):
        Infos=[sync_names[x] for x in get_info(get_closest([x for x in slicer(minidicts, i, 4) if x["upos"] == "VERB"], i))]
        try:
            preclosest=get_closest([x for x in slicer(minidicts, i, 4, "L") if x["upos"] == "VERB"], i)
        except IndexError:
            preclosest=get_closest([x for x in slicer(minidicts, i, 4, "R") if x["upos"] == "VERB"], i)

        try:
            val=dict([x for x in infoglagol if x[0]==preclosest["lemma"]][0][1])
        except IndexError:
            raise NotImplementedError("Tega še ne znam: glagol biti edition ALI unknown glagol. Token: "+ minidicts[i]["text"])
        
        #zdej preverjam, kaj mora najbolj bit in kaj je že
        Pat=get_value_if("PAT", val, 0)
        Rec=get_value_if("REC", val, 0)
        Act=get_value_if("ACT", val, 0)
        list_of_roles=sorted([("PAT", Pat), ("REC", Rec), ("ACT", Act)], key=itemgetter(1), reverse=True)
        case_dict={"PAT": "Acc", "REC": "Dat", "ACT": "Nom"}
        if is_negated_verb(sentence, get_closest([preclosest], i, True)):
           case_dict={"PAT": "Gen", "REC": "Dat", "ACT": "Nom"} 
        In=preclosest["id"]-1
        for role in list_of_roles:
            if any([x for x in slicer(minidicts, In) if "feats" in x.keys() and "Case="+case_dict[role[0]] in x["feats"]]):
                continue
            else:
                if role[0]=="ACT":
                    Infos=[Infos[0], sync_names[case_dict[role[0]]], Infos[2]]
                else:    
                    Infos=[get_gen(lema, tempdict), sync_names[case_dict[role[0]]], "ednina"]
                    
                break        
    else:
        raise NotImplementedError("Tega še ne znam: uncharted waters edition. Token: "+ tok)
    return Infos


#finds the word to get info from: for nouns
def get_abbreviation_declension_noun(config, sentence: Sentence, word_index, lema=None, tempdict=None):
    i=word_index
    if not sentence.tags:
        sentence.tag()
    minidicts=[word.tag for word in sentence.words]
    word=sentence.get_word(i)
    if not lema and not tempdict: lema, tempdict = make_lemma_and_tempdict(config, word.un_normalized)
    P=prev_whole(i, minidicts)
    N=next_whole(i, minidicts)

    if i>0 and (is_decimal(minidicts[i-1]["text"]) or is_fraction(minidicts[i-1]["text"])):
        print(" --- fraction")
        Infos=[get_gen(lema, tempdict), "rodilnik", get_nr(lema, tempdict)]
    elif ("-" in minidicts[i-1]["text"].replace("–", "-") and is_decimal(minidicts[i-1]["text"].replace("–", "-").split("-")[-1])) or ("x" in minidicts[i-1]["text"].replace("×", "x") and is_decimal(minidicts[i-1]["text"].replace("×", "x").split("x")[-1]) or is_fraction(minidicts[i-1]["text"].replace("–", "-").split("-")[-1])):
        print(" --- multiplication")
        Infos=[get_gen(lema, tempdict), "rodilnik", get_nr(lema, tempdict)]
    elif ("x" in minidicts[i-1]["text"].replace("×", "x") and minidicts[i-1]["text"].replace("×", "x").split("x")[-1].isnumeric()):
        if int(minidicts[i-1]["text"].replace("×", "x").split("x")[-1][-2:])<5:
            Infos=[get_gen(lema, tempdict), "tožilnik", get_nr_from_int(minidicts[i-1]["text"].replace("×", "x").split("x")[-1])]
        else:
            Infos=[get_gen(lema, tempdict), "rodilnik", get_nr_from_int(minidicts[i-1]["text"].replace("×", "x").split("x")[-1])]
    elif i>0 and minidicts[i-1]["text"].isnumeric() and not 0<int(minidicts[i-1]["text"])<5 and not is_fraction(minidicts[i-1]["text"]):
        Infos=[get_gen(lema, tempdict), "rodilnik", get_nr_from_int(minidicts[i-1]["text"])]
    elif i>0 and P != None and minidicts[P]["upos"] in ["ADJ"]:
        Infos=[sync_names[x] for x in get_info(minidicts[P])]
        if Infos[:3]==["moški", "tožilnik", "ednina"]:
            if minidicts[N]["text"].endswith("ega"):
                Infos[3]="da"
            elif minidicts[N]["text"].endswith("i"):
                Infos[3]="ne"
    elif i>1 and P != None and isordinal(minidicts[P]["text"]) and minidicts[P-1]["upos"] in ["ADJ"]:
        Infos=[sync_names[x] for x in get_info(minidicts[P-1])]
        if Infos[:3]==["moški", "tožilnik", "ednina"]:
            if minidicts[P-1]["text"].endswith("ega"):
                Infos[3]="da"
            elif minidicts[P-1]["text"].endswith("i"):
                Infos[3]="ne"
    elif i>0 and P != None and minidicts[P]["upos"] in ["ADP"]:
        if i<len(minidicts) and N != None and minidicts[N]["ner"]!="O":
            Infos=[sync_names[x] for x in get_info(minidicts[N])][:1]+[sync_names[x] for x in get_info(minidicts[P])][1:]
        else:
            if get_gen(lema, tempdict)!="moški" and [sync_names[x] for x in get_info(minidicts[P])][-1] in ["da", "ne"]:
                Infos=[get_gen(lema, tempdict)]+[sync_names[x] for x in get_info(minidicts[P])][1:-1]
            else:
                Infos=[get_gen(lema, tempdict)]+[sync_names[x] for x in get_info(minidicts[P])][1:]
    elif i>0 and P != None and minidicts[P]["upos"] in ["NOUN"]:
        if i<len(minidicts)-1 and N != None and minidicts[N]["upos"]=="PROPN":
            Infos=[sync_names[x] for x in get_info(minidicts[N])]
            
        else:
            Infos=[get_gen(lema, tempdict), "rodilnik", "ednina"]
            
    elif i<len(minidicts)-1 and N != None and minidicts[N]["upos"] in ["PROPN"]:
        Infos=[sync_names[x] for x in get_info(minidicts[N])]
        
    elif P != None and minidicts[P]["upos"] in ["ADP"]:
        Infos=[sync_names[x] for x in get_info(minidicts[P])]
    elif any(x["upos"] == "VERB" for x in slicer(minidicts, i, 4)) or sentence.last_verb:
        closest = get_closest([x for x in slicer(minidicts, i, 4) if x["upos"] == "VERB"], i)
        if closest:
            sentence.last_verb = closest
        Infos=[sync_names[x] for x in get_info(sentence.last_verb)]
        
        try:
            preclosest=get_closest([x for x in slicer(minidicts, i, 4, "L") if x["upos"] == "VERB"], i)
            
            if preclosest:
                sentence.pre_last_verb = preclosest
            else: raise IndexError()
        except IndexError:
            try:
                preclosest=get_closest([x for x in slicer(minidicts, i, 4, "R") if x["upos"] == "VERB"], i)
                if preclosest: 
                    sentence.pre_last_verb = preclosest
                else: raise IndexError()
            except:
                preclosest = sentence.pre_last_verb
        try:
            val=dict([x for x in infoglagol if x[0]==preclosest["lemma"]][0][1]) 
        except IndexError:
            raise NotImplementedError("Tega še ne znam: glagol biti edition ALI unknown glagol. Token: " + minidicts[i]["text"])
        
        Pat=get_value_if("PAT", val, "0")
        Rec=get_value_if("REC", val, "0")
        Act=get_value_if("ACT", val, "0")
        list_of_roles=sorted([("PAT", Pat), ("REC", Rec), ("ACT", Act)], key=itemgetter(1), reverse=True)
        case_dict={"PAT": "Acc", "REC": "Dat", "ACT": "Nom"}
        
        if is_negated_verb(sentence, preclosest["id"]):
           case_dict={"PAT": "Gen", "REC": "Dat", "ACT": "Nom"} 
        I=preclosest["id"]-1
        
        for role in list_of_roles:
            if any([x for x in slicer(minidicts, I) if x["upos"] in ["NOUN"] and "Case="+case_dict[role[0]] in x["feats"]]):
                continue
            else:
                if role[0]=="ACT":
                    Infos=[Infos[0], sync_names[case_dict[role[0]]], Infos[2]]
                else:    
                    if i>0 and minidicts[i-1]["text"].isnumeric() and not is_fraction(minidicts[i-1]["text"]):
                        Infos=[get_gen(lema, tempdict), sync_names[case_dict[role[0]]], get_nr_from_int(minidicts[i-1]["text"])]
                    else:
                        Infos=[get_gen(lema, tempdict), sync_names[case_dict[role[0]]], get_nr(lema, tempdict)]
                    
                break        
                
    else:
        raise NotImplementedError("Tega še ne znam: uncharted waters edition. Token: "+ minidicts[i]["text"])
                    
    return Infos

def get_number_declension(sentence: Sentence, word_index):
    i=word_index
    if not sentence.tags:
        sentence.tag()
    minidicts=[word.tag for word in sentence.words]
    word=sentence.get_word(i)
    tok=word.un_normalized
    if is_numeric(tok) or isordinal(tok) or (tok.isnumeric() and not is_fraction(tok)):
        tempdict={}
        lema=get_nr_lemma(tok, False)
        if " " not in lema:
            tempdict[lema]=sloleks_forms_dict[lema].copy()
        else:
            tempdict=instant_tempdict(tok)
    P=prev_whole(i, minidicts)
    N=next_whole(i, minidicts)
    if i<len(minidicts)-1 and N != None and minidicts[N]["upos"] in ["ADJ"]:
        Infos=[sync_names[x] for x in get_info(minidicts[N])]
        if int(word.un_normalized)>4 and Infos[1]=="rodilnik":
            raise NotImplementedError("To ni v resnici error, samo vodi do prave poti.")
        elif Infos[:3]==["moški", "tožilnik", "ednina"]:
            if minidicts[N]["text"].endswith("ega"):
                Infos[3]="da"
            elif minidicts[N]["text"].endswith("i"):
                Infos[3]="ne"
    elif i<len(minidicts)-1 and N != None and minidicts[N]["upos"] in ["NOUN"]:
        Infos=[sync_names[x] for x in get_info(minidicts[N])]
        if int(word.un_normalized)>4 and Infos[1]=="rodilnik":
            raise NotImplementedError("To ni v resnici error, samo vodi do prave poti.")
    else:
        raise NotImplementedError("Tega še ne znam: uncharted waters edition. Token: "+ tok)
    return Infos



def get_abbreviation_declension(config, sentence: Sentence, word_index):
    word=sentence.get_word(word_index)
    if list(config["abbr"]["set"][word.un_normalized].values())[0] in ["NOUN"]:
        return get_abbreviation_declension_noun(config, sentence, word_index)
    return get_abbreviation_declension_adj(config, sentence, word_index)

# determines the case of a date
def date_declension(sentence: Sentence, word_index):
    if not sentence.is_first_word(word_index):
        previous_word = sentence.get_word(word_index - 1)
        previous_word_un_normalized = previous_word.un_normalized
        if not sentence.tags:
            sentence.tag()
        if "feats" in previous_word.tag and "Case=Gen" in previous_word.tag["feats"]:
            return ["rodilnik", "moški", "ednina"]
        if ("feats" in previous_word.tag and ("Case=Nom" in previous_word.tag["feats"] or "Case=Dat" in previous_word.tag["feats"])) and ("upos" in previous_word.tag and previous_word.tag["upos"] == "PROPN" or word_index == 1):
            return ["imenovalnik", "moški", "ednina"]
        if match("([Dd]an[:])|([Dd]atum[,:]?)|([Zz]a)", previous_word_un_normalized):
            return ["imenovalnik", "moški", "ednina"]
        if match("[Mm]ed", previous_word_un_normalized) or (word_index >= 3 and match("in", previous_word_un_normalized) and
                                                            not sentence.is_first_word(word_index - 3) and
                                                            match("[Mm]ed", sentence.get_word(word_index - 3).toString())):
            return ["orodnik","moški", "ednina"]
        if match("[(].+[)]", sentence.get_word(word_index).un_normalized):
            return ["imenovalnik", "moški", "ednina"]

    return ["rodilnik", "moški", "ednina"]  # default rodilnik, most frequent case


# determines suffix punctuation of an hour
def get_hour_case(sentence, word_index):
    word = sentence.get_word(word_index)
    next = sentence.get_word(word_index + 1)
    prev = sentence.get_word(word_index - 1)
    prevprev = sentence.get_word(word_index - 2) if word_index > 1 else None
    if (prev and prev.text.lower() in ["med"]) or (prevprev and prevprev.text.lower() in ["med"]):
        return ["ženski", "tožilnik", "ednina"]
    if (next and next.text.lower() in ["uro"]):
        return ["ženski", "tožilnik", "ednina"]
    elif (prev and prev.text.lower() in ["od", "do", "ob", "okrog", "okoli"]) or (prevprev and prevprev.text.lower() in ["od", "do", "ob", "okrog", "okoli"]):
        return ["ženski", "mestnik", "množina"]
    elif (next and next.text.lower() in ["uri"]):
        return ["ženski", "mestnik", "množina"]
    else:
        return "cardinal"
