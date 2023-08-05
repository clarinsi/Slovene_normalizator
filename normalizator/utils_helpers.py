from operator import itemgetter
from re import match
import pickle
import sys
import os
from normalizator.sentence import Sentence
from normalizator.word import Word
from normalizator.super_tools.word_tokenizer import word_tokenizer
from normalizator.super_tools.slicer import slicer
import normalizator.support.num_generator1mio as ng

prefixes = {'': '', 'p': 'piko', 'n': 'nano', 'μ': 'mikro', 'µ': 'mikro', 'm': 'mili', 'c': 'centi', 'd': 'deci', 'dc': 'deci', 'da': 'deka', 'dk': 'deka', 'h': 'hekto', 'k': 'kilo', 'M': 'mega', 'G': 'giga', 'T': 'tera'}

current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)
with open(os.path.join(current_directory, 'support/Sloleks_lemmas_with_forms_v2.pickle'), "rb") as handle:
    sloleks_forms_dict=pickle.load(handle)

if "promile" in sloleks_forms_dict:
    sloleks_forms_dict["promil"]=sloleks_forms_dict["promile"]

if "newton" not in sloleks_forms_dict and "njuton" in sloleks_forms_dict:
    temp={}
    for key in sloleks_forms_dict["njuton"]:
        temp[key]=(sloleks_forms_dict["njuton"][key][0].replace("njuton", "newton"), sloleks_forms_dict["njuton"][key][1])
    sloleks_forms_dict["newton"]=temp

with open(os.path.join(current_directory, 'support/valenca-interres-new.pickle'), 'rb') as handle:
    infoglagol=pickle.load(handle)

units=['E', 'ha', 'mol', 'kcal', 'tbl.', 'ted.', 'vp.', 'Wh', 'KM', '´', '´´', '˝', '‰', 'B', 'min', 'm', "m2", "m3", 'g', 'l', 'L', 't', 'b', 'N', 'Pa', 'V', 'W', 'A', 's', 
'h', 'K', 'Hz', 'J', 'F', 'Ω', '°', '°C', '°F', 'EUR', 'SIT', '€', '%', '$', "kat"]

predpone = {'piko': 'p', 'nano': 'n', 'mikro': 'μ', 'mili': 'm', 'centi': 'c', 'deci': 'd', 'deka': 'da', 'hekto': 'h', 'kilo': 'k', 'mega': 'M', 'giga': 'G', 'tera': 'T'}

predpone_rev=dict([(predpone[key], key) for key in predpone])

merske = {"meter": "m", "gram": "g","liter": "l", "tona": "t", "bar": "b", "newton": "N", "paskal": "Pa", "volt": "V", "watt": "W", "amper": "A",
          "sekunda": "s", "minuta": "min", "ura": "h", "kelvin": "K", "herc": "Hz", "joule": "J", "farad": "F", "stopinja": "°",
          "promil": "‰", "odstotek": "%", "evro": "€", "dolar": "$"}

merske_rev=dict([(merske[key], key) for key in merske])

enote=[x+y for x in predpone.values() for y in merske.values() if y.isalpha()]+list(merske.values())+["m2", "m3"]

#convert Classla tags to Sloleks tags
sync_names={"Masc": "moški", "Fem": "ženski", "Neut": "srednji", "Sing": "ednina", "Dual": "dvojina", "Plur": "množina",
"Nom": "imenovalnik", "Gen": "rodilnik", "Dat": "dajalnik", "Acc": "tožilnik", "Loc": "mestnik", "Ins": "orodnik",
"NOUN": "samostalnik", "ADJ": "pridevnik", "ADV": "prislov",
"Inan": "ne", "Anim": "da"}

sync_names_rev = {v: k for k, v in sync_names.items()}

def is_fraction(tok):
    if tok in ["¼", "½", "¾", "⅐", "⅑", "⅒", "⅔", "⅓", "⅕", "⅖", "⅗", "⅘", "⅙", "⅚", "⅛", "⅜", "⅝", "⅞", "⅟", "↉"]:
        return True
    else:
        return False

def is_sublist(small, big):
    for i in range(len(big) - len(small) + 1):
        if small == big[i:i + len(small)]: return True
    return False


def where_sublist(small, big):
    results = []
    for i in range(len(big) - len(small) + 1):
        if small == big[i:i + len(small)]:
            results.append([i for i in range(i, i + len(small))])
    return results

def dot_in_the_middle(tok, dot=".", include_more=False):
    if tok.count(dot)==1 and tok.index(dot)!=0 and tok.index(dot)!=len(tok)-1:
        return True
    elif include_more and tok.count(dot)>0 and tok.index(dot)!=0 and tok.index(dot)!=len(tok)-1:
        return True
    return False

def is_decimal(tok):
    if dot_in_the_middle(tok, ",") and tok.replace(",", "").isnumeric(): return True
    if (tok.startswith("+") or tok.startswith("-")) and is_decimal(tok[1:]): return True
    return False

def is_numeric(tok, include_fraction=False):
    if tok=="": return False
    elif all(char.isnumeric() and not is_fraction(char) for char in tok): return True
    elif "." in tok and all(char.isnumeric() and not is_fraction(char) for char in tok.replace(".", "")) and len(tok.split(".")[0])>0 and all(len(p)==3 for p in tok.split(".")[1:]): return True
    elif (tok.startswith("+") or tok.startswith("-") or tok.startswith("–")) and is_numeric(tok[1:]): return True
    elif include_fraction and is_fraction(tok): return True
    return False


def is_interval(tok):
    tok=tok.replace("-", "–")
    if dot_in_the_middle(tok, "–") and (all((x.isnumeric() or is_decimal(x)) for x in tok.split("–")) or all(isordinal(x) for x in tok.split("–"))):
        return True
    return False

#gets value if it exist, otherwise assigns default value
def get_value_if(key, dictx, defaultValue):
    if key in dictx:
        return dictx[key]
    else:
        return defaultValue

def next_whole(i, toks):
    if type(toks[0])==dict:
        toks=[x["text"] for x in toks]
    i+=1
    while i<len(toks)-1 and (is_abbr(toks[i]) or toks[i] in ['"']):
        i+=1
    if i<len(toks) and not is_abbr(toks[i]):
        return i
    return None

def prev_whole(i, toks):
    if type(toks[0])==dict:
        toks=[x["text"] for x in toks]
    i-=1
    while i>1 and (is_abbr(toks[i]) or toks[i] in ['"']):
        i-=1
    if i>=0 and not is_abbr(toks[i]):
        return i
    return None

#gets needed values from other specified word
def get_info(minidict):
    feats=dict([x.split("=") for x in minidict["feats"].split("|")])
    pck=(get_value_if("Gender", feats, "Masc"), get_value_if("Case", feats, "Nom"), get_value_if("Number", feats, "Sing"))
    if pck==('Masc', 'Acc', 'Sing'):
        return (get_value_if("Gender", feats, "Masc"), get_value_if("Case", feats, "Nom"), get_value_if("Number", feats, "Sing"), get_value_if("Animacy", feats, "Inan"))
    else:
        return pck

#finds correct form in Sloleks
def get_correct_form(lema, POS=None, spol=None, sklon=None, oseba=None, oblika=None, stevilo=None, živost=None, določnost=None, minidict=None):
    if POS in ["prislov"]:
            return lema
    if minidict: temp_dict=minidict.copy()
    else: temp_dict=sloleks_forms_dict.copy()
    if lema in temp_dict.keys():
        underkey=[]
        if not any(x[1]==spol for x in list(temp_dict[lema].keys()) if len(x)>1) and get_gen(lema, temp_dict) in ["moški", "ženski", "srednji"]:
            spol=get_gen(lema, temp_dict, POS)
        if POS!="števnik" and get_gen(lema, temp_dict, POS) not in ["moški", "ženski", "srednji"]:
            orig_spol=spol
            spol=None
        elif POS=="števnik":
            try:
                if get_gen(lema, temp_dict, POS) not in ["moški", "ženski", "srednji"]:
                    orig_spol=spol
                    spol=None
            except IndexError:
                try:
                    if get_gen(lema, temp_dict, "pridevnik") not in ["moški", "ženski", "srednji"]:
                        orig_spol=spol
                        spol=None
                except IndexError:
                    if get_gen(lema, temp_dict, "samostalnik") not in ["moški", "ženski", "srednji"]:
                        orig_spol=spol
                        spol=None
        for k in [POS, spol, sklon, stevilo, živost, določnost]:
            if k!=None:
                underkey.append(k)
        if živost==None and POS=="samostalnik" and spol=="moški" and stevilo=="ednina" and sklon=="tožilnik":
            try:
                tempunderkey=underkey+["ne"]
                return temp_dict[lema][tuple(tempunderkey)][0]
            except KeyError:
                tempunderkey=underkey+["da"]
                return temp_dict[lema][tuple(tempunderkey)][0]
        #določnost
        if POS in ["pridevnik"] and spol=="moški" and stevilo=="ednina" and sklon in ["imenovalnik", "tožilnik"]:
            if živost=="da":
                tempunderkey=underkey[:-1]
                return temp_dict[lema][tuple(tempunderkey)][0]
            elif živost=="ne":
                try:
                    tempunderkey=underkey[:-1]+["da"]
                    return temp_dict[lema][tuple(tempunderkey)][0]
                except KeyError:
                        try:
                            tempunderkey=underkey[:-1]+["ne"]
                            return temp_dict[lema][tuple(tempunderkey)][0]
                        except KeyError:
                            return get_correct_form(lema, "števnik", spol, sklon, oseba, oblika, stevilo, živost, določnost, minidict)
            elif not živost:
                try:
                    tempunderkey=underkey+["da"]
                    return temp_dict[lema][tuple(tempunderkey)][0]
                except KeyError:
                        try:
                            tempunderkey=underkey+["ne"]
                            return temp_dict[lema][tuple(tempunderkey)][0]
                        except KeyError:
                            return get_correct_form(lema, "števnik", spol, sklon, oseba, oblika, stevilo, živost, določnost, minidict)
            else:
                raise KeyError(underkey)
        if živost==None and POS in ["števnik"] and spol=="moški" and stevilo=="ednina" and sklon in ["tožilnik"]:
            try:
                return temp_dict[lema][tuple(underkey+["ne"])][0]
            except KeyError:
                try:
                    return temp_dict[lema][tuple(underkey+["da"])][0]
                except KeyError:
                    return temp_dict[lema][tuple(underkey)][0]

        if določnost==None and POS in ["števnik"] and spol=="moški" and stevilo=="ednina" and sklon in ["imenovalnik"]:
            try:
                return temp_dict[lema][tuple(underkey+["da"])][0]
            except KeyError:
                try:
                    return temp_dict[lema][tuple(underkey+["ne"])][0]
                except KeyError:
                    return temp_dict[lema][tuple(underkey)][0]
        underkey=tuple(underkey)
        try:
            return temp_dict[lema][underkey][0]
        except KeyError:
            if underkey[0]=="pridevnik":
                return get_correct_form(lema, "števnik", spol, sklon, oseba, oblika, stevilo, živost, določnost, minidict)
            elif underkey==('samostalnik', 'moški', 'tožilnik', 'ednina', 'ne'):
                try:
                    return temp_dict[lema][('samostalnik', 'moški', 'tožilnik', 'ednina', 'da')][0]
                except KeyError:
                    return temp_dict[lema][('samostalnik', 'moški', 'tožilnik', 'ednina')][0]

            else:
                raise KeyError(underkey)


#gets closest word if more than one applies
def get_closest(list_of_dicts, i, return_index=False):
    I=i+1
    if return_index:
        return sorted([(abs(el["id"]-I), el) for el in list_of_dicts], key=itemgetter(0))[0][1]["id"]-1
    return sorted([(abs(el["id"]-I), el) for el in list_of_dicts], key=itemgetter(0))[0][1]

def is_abbr(tok, config=None):
    if config:
        if tok in config["abbr"]["set"]: return True
        return False
    if not config and tok.endswith(".") and tok[:-1].isalpha(): return True
    return False

def is_nr_seq(pck):
    toklist=pck[0]
    i=pck[1]
    t=toklist[i]
    if t.isnumeric() and not is_fraction(t):
        nrs = []
        while i < len(toklist) and toklist[i].isnumeric() and not is_fraction(toklist[i]):
            nrs.append(toklist[i])
            i += 1
        if len(nrs) > 2:
            return True
        i -=  1
        while i > 0 and toklist[i].isnumeric() and not is_fraction(toklist[i]):
            nrs = [toklist[i]] + nrs
            i -= 1
        if len(nrs) > 2:
            return True
        else:
            return False
    else:
        return False

def is_abbr_or_nr(tok):
    if is_abbr(tok):
        return True
    elif tok.isnumeric() and not is_fraction(tok):
        return True

def is_abbr_chain(i, toks, include_chain=False, include_numbers=False, config=None):
    if is_abbr(toks[i], config) and ((i>0 and is_abbr(toks[i-1], config)) or (i<len(toks)-1 and is_abbr(toks[i+1], config))):
        if include_chain:
            abrs = []
            while i < len(toks) and is_abbr(toks[i]):
                abrs.append(toks[i])
                i += 1
            i -=  (len(abrs)+1)
            while i >= 0 and is_abbr(toks[i]):
                abrs = [toks[i]] + abrs
                i -= 1
            return abrs
        return True
    if include_numbers and is_abbr_or_nr(toks[i]) and ((i>0 and is_abbr(toks[i-1])) or (i<len(toks)-1 and is_abbr(toks[i+1]))):
        if include_chain:
            abrs = []
            while i < len(toks) and is_abbr_or_nr(toks[i]):
                abrs.append(toks[i])
                i += 1
            i -=  (len(abrs)+1)
            while i >= 0 and is_abbr(toks[i]):
                abrs = [toks[i]] + abrs
                i -= 1
            return abrs
        return True
    return False

def get_nr_from_int(nr):
    nr=nr.replace(".", "")
    if all(char.isnumeric() for char in nr):
        if len(str(nr))>2:
            nr=str(nr)[-2:]
        if abs(int(nr))==1:
            return "ednina"
        elif abs(int(nr))==2:
            return "dvojina"
        else:
            return "množina"
    elif "-" in nr.replace("–", "-"):
        return get_nr_from_int(nr.replace("–", "-").split("-")[-1])

def get_gen(lema, tempdict, POS=None):
    if POS: spoli=[x[1] for x in list(tempdict[lema].keys()) if len(x)>1 and x[0]==POS]
    else: spoli=[x[1] for x in list(tempdict[lema].keys()) if len(x)>1]
    if len(set(spoli))==1:
        return spoli[0]
    else:
        return spoli[0]

def get_nr(lema, tempdict):
    štev=[x[3] for x in list(tempdict[lema].keys()) if len(x)>1]
    if len(set(štev))==1:
        return štev[0]
    else:
        return štev[0]

def get_main_abbr(config, abbr_chain):
    abbrs=config["abbr"]["set"]
    if type(abbr_chain)==list:
        if all(tok in abbrs for tok in abbr_chain):
            for i in range(len(abbr_chain)):
                tok=abbr_chain[i]
                if list(abbrs[tok].values())[0] in ["NOUN"]:
                    return(tok, i)
        elif any(tok in abbrs for tok in abbr_chain):
            for i in range(len(abbr_chain)):
                tok=abbr_chain[i]
                if tok in abbrs and list(abbrs[tok].values())[0] in ["NOUN"]:
                    return(tok, i)
    elif type(abbr_chain)==str:
        if "_" in abbr_chain:
            Split=abbr_chain.split("_")
            if "NOUN" in Split:
                return (Split.index("NOUN"), "samostalnik")
            elif "ADJ" in Split:
                Split.reverse()
                rev_index=Split.index("ADJ")
                Split.reverse()
                tru_index=len(Split)-rev_index-1
                return (tru_index, "pridevnik")

def isordinal(tok):
    if tok[:-1].isnumeric() and not is_fraction(tok[:-1]) and tok[-1] == ".":
        return True
    else:
        return False

def get_nr_lemma(nr, basic=True):
    predznaki={"+": "plus", "-": "minus", "–": "minus"}
    if is_fraction(nr):
        raise ValueError("No fractions please!")
    elif any(nr.startswith(p) for p in predznaki):
        return predznaki[nr[0]]+" "+get_nr_lemma(nr[1:])
    elif not (isordinal(nr) or nr.isnumeric()) or (dot_in_the_middle(nr) and nr.replace(".", "").isnumeric()):
        raise ValueError("Nr must be numeric or ordinal!")
    elif isordinal(nr) and not basic:
        if nr=="2.":
            return "drug"
        else:
            return ng.n2wv(int(nr.replace(".", "")))[1]
    elif isordinal(nr) and basic:
        return ng.n2wv(int(nr.replace(".", "")))[1]
    elif (nr.isnumeric() or (dot_in_the_middle(nr) and nr.replace(".", "").isnumeric())) and not basic:
        nr=nr.replace(".", "")
        if nr=="1":
            return "en"
        elif str(int(nr[-2:]))=="1":
            return " ".join(ng.n2w(int(nr))[1].split()[:-1]+["en"])
        elif nr=="3":
            return "trije"
        elif str(int(nr[-2:]))=="3":
            return " ".join(ng.n2w(int(nr))[1].split()[:-1]+["trije"])
        elif nr=="4":
            return "štirje"
        elif str(int(nr[-2:]))=="4":
            return " ".join(ng.n2w(int(nr))[1].split()[:-1]+["štirje"])
        return ng.n2w(int(nr))[1]
    elif (nr.isnumeric() or (dot_in_the_middle(nr) and nr.replace(".", "").isnumeric())) and basic:
        nr=nr.replace(".", "")
        return ng.n2w(int(nr))[1]


def get_basic_nr(nr):
    if not (isordinal(nr) or nr.isnumeric()):
        raise ValueError("Nr must be numeric or ordinal!")
    if isordinal(nr):
        return ng.n2wv(int(nr.replace(".", "")))[1]
    if nr.isnumeric():
        return ng.n2w(int(nr))[1]

def get_animacy(lema, feats, tempdict):
    if lema in tempdict and feats==["moški", "tožilnik", "ednina"]:
        if len([x for x in tempdict[lema].keys() if x[1]=="moški" and x[2]=="tožilnik" and x[3]=="ednina" and x[4]=="ne"])!=0: return "Inan"
        if len([x for x in tempdict[lema].keys() if x[1]=="moški" and x[2]=="tožilnik" and x[3]=="ednina" and x[4]=="da"])!=0: return "Anim"

def instant_tempdict(tok):
    base_dict={}
    if type(tok)==str and isordinal(tok):
        lema=get_nr_lemma(tok)
        base=get_nr_lemma(str(int(tok.replace(".", "")[-2:]))+".")
        pref=get_nr_lemma(str(int(tok.replace(".", "")[:-2]))+"00").replace(" ", "")
        temp=sloleks_forms_dict[base].copy()
        base_dict[lema]=dict([(k, temp[k]) for k in temp if k[0] in ["števnik", "pridevnik"]])
        for k in base_dict[lema]:
            base_dict[lema][k]=(pref+base_dict[lema][k][0], base_dict[lema][k][1])
    elif type(tok)==str and tok.isnumeric() and int(tok)%1000000==0:
        lema=get_nr_lemma(tok)
        base="milijon"
        pref=lema.rsplit(" ", 1)[0]+" "
        base_dict={}
        temp=sloleks_forms_dict[base].copy()
        base_dict[lema]=dict([(k, temp[k]) for k in temp if k[0] in ["samostalnik", "števnik"]])
        for k in base_dict[lema]:
            base_dict[lema][k]=(pref+base_dict[lema][k][0], base_dict[lema][k][1])
        
    elif tok in ["1", "3"]:
        lema=get_nr_lemma(tok, False)
        base_dict={}
        base_dict[lema]=sloleks_forms_dict[lema].copy()

    elif type(tok)==str and tok.isnumeric():
        lema=get_nr_lemma(tok, False) 
        base=lema.rsplit()[-1]
        pref=lema.rsplit(" ", 1)[0]+" "
        base_dict={}
        temp=sloleks_forms_dict[base].copy()
        base_dict[lema]=dict([(k, temp[k]) for k in temp if k[0] in ["števnik", "pridevnik"]])
        for k in base_dict[lema]:
            base_dict[lema][k]=(pref+base_dict[lema][k][0], base_dict[lema][k][1])
    elif type(tok)==list:
        if len(tok)>1:
            lema="".join(tok)
            base=tok[1]
            pref=tok[0]
            base_dict={}
            base_dict[lema]=sloleks_forms_dict[base].copy()
            for k in base_dict[lema]:
                base_dict[lema][k]=(pref+base_dict[lema][k][0], base_dict[lema][k][1])
        elif len(tok)==1:
            lema=tok[0]
            base_dict[lema]=sloleks_forms_dict[lema].copy()
    return base_dict


def get_basic_unit(config, tok, sep=True):
    for unt in config["unit"]["set"]:
        if tok.endswith(unt):
            base=unt
            base_whole=config["unit"]["set"][unt]
            if base!=tok:
                if tok[:-len(base)] in prefixes:
                    pref=tok[:-len(base)]
                    pref_whole=prefixes[pref]
                    if sep:
                        return [pref_whole, base_whole]
                    else:
                        return pref_whole+base_whole
            else:
                if sep:
                    return [base_whole]
                else:
                    return base_whole

#to je skoraj enako kot če dam samo lemo, se pa razlikuje v tem, da lahko jaz kot uporabnik recimo vnesem profesorica+profesor kot iztočnico in je profesorica moja glavna oblika,
# torej bo pod lemo profesor ničta oblika profesorica
def last_resort(lema, tempdict):
    if lema in tempdict: return list(tempdict[lema].values())[0][0]
    return lema

def make_lemma_and_tempdict(config, tok: str, postf=""):
    abbrs=config["abbr"]["set"]
    enote=[x+y for x in prefixes for y in config["unit"]["set"]]
    if tok in abbrs:
        tempdict={}
        if "+" not in list(abbrs[tok].keys())[0]:
            lema=list(abbrs[tok].keys())[0]
            tempdict[lema]=sloleks_forms_dict[lema].copy()
        else:
            lemmas=list(abbrs[tok].keys())[0].split("+")
            lema=lemmas[0]
            tempdict[lema]=sloleks_forms_dict[lema].copy()
            for l in lemmas[1:]:
                tempdict[lema]={**tempdict[lema], **sloleks_forms_dict[l]}
    elif tok in enote:
        Unt=None
        pref=""
        if tok=='°C':
            postf="Celzija"
            tok="°"
        elif tok=='°F':
            postf="Fahrenheita"
            tok="°"
        elif tok in ["m2", "m3"]:
            pref=tok[-1]
            tok="m"
            cubes={"2": "kvadraten", "3": "kubičen"}
        
        elif tok=="KM":
            pref="konjski"
            Unt, lema="moč", "moč"
            tempdict={lema: sloleks_forms_dict[Unt].copy()}
        
        #NOTE: 
        elif tok=="Wh":
            pref="vaten"
            Unt, lema="ura", "ura"
            tempdict={lema: sloleks_forms_dict[Unt].copy()}
        
        elif tok.endswith("m2") or tok.endswith("m3") and tok[:-2] in prefixes:
            very_temp_lema, very_temp_dict=make_lemma_and_tempdict(config, tok[-2:])
            pref=prefixes[tok[:-2]]
            lema=very_temp_lema.split()[0]+" "+pref+very_temp_lema.split()[1]
            tempdict={lema: {}}
            for k in very_temp_dict[very_temp_lema]:
                tempdict[lema][k]=(very_temp_dict[very_temp_lema][k][0].split()[0]+" "+pref+very_temp_dict[very_temp_lema][k][0].split()[1], very_temp_dict[very_temp_lema][k][1])
            return (lema, tempdict)
            
        if not Unt:
            Unt=get_basic_unit(config, tok)
            lema=get_basic_unit(config, tok, False)
            tempdict=instant_tempdict(Unt)
        
        if postf:
            newlema=" ".join([lema, postf])
            temp=tempdict.copy()
            tempdict={newlema: {}}
            for k in temp[lema]:
                tempdict[newlema][k]=(temp[lema][k][0]+" "+postf, temp[lema][k][1])
            lema=newlema
        if pref:
            temp=tempdict.copy()
            pref_lema=cubes[pref] if pref.isnumeric() else pref
            pref_tempdict={}
            pref_tempdict[pref_lema]=sloleks_forms_dict[pref_lema].copy()
            pref_POS="pridevnik"
            C=0
            for k in [x for x in temp[lema] if x[0]=="samostalnik"]:
                pref_norm=get_correct_form(pref_lema, pref_POS, spol=k[1], sklon=k[2], stevilo=k[3], minidict=pref_tempdict)
                if C==0:
                    newlema=pref_norm+" "+temp[lema][k][0]
                    tempdict={newlema: {}}
                C+=1
                tempdict[newlema][k]=(pref_norm+" "+temp[lema][k][0], temp[lema][k][1])
            lema=newlema
    return (lema, tempdict)

def title(tok):
    return tok[0].upper()+tok[1:]

def is_negated_verb(sentence: Sentence, word_index):
    prev_word = sentence.get_word(word_index - 1)
    prev_prev_word = sentence.get_word(word_index - 2)

    return bool(prev_word and match("([Nn]e)|([Nn]i)|([Nn]is.{1,2})", prev_word.un_normalized) or
                prev_prev_word and match("([Nn]e)|([Nn]i)|([Nn]is.{1,2})", prev_prev_word.un_normalized))


def lower_list(listX):
    return [x.lower() for x in listX]

def update_minidict(sentence, i, text, declension=None, POS=None, animacy=None):
    if not sentence.tags:
        sentence.tag()
    minidict=sentence.get_word(i).tag
    minidict["text"]=text
    if animacy:
        minidict["feats"]="Animacy="+animacy+"|Case="+sync_names_rev[declension[1]]+"|Gender="+sync_names_rev[declension[0]]+"|Number="+sync_names_rev[declension[2]]
    if declension:
        minidict["feats"]="Case="+sync_names_rev[declension[1]]+"|Gender="+sync_names_rev[declension[0]]+"|Number="+sync_names_rev[declension[2]]
    if POS:
        minidict["upos"]=sync_names_rev[POS]
    
            
