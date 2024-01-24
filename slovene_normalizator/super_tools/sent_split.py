from slovene_normalizator.sentence import PosTagger
import slovene_normalizator.super_tools.word_tokenizer as wt
from slovene_normalizator.super_tools.standardize_quotes import standardize_quotes



def split_sent(sent):
    pt = PosTagger()
    
    sent=" ".join(standardize_quotes(sent).split())
    final_punct=".?!"
    FP=0
    for p in final_punct:
        FP+=sent[:-1].count(p)
    if FP>0:
        toks=wt.word_tokenizer(sent, mixed=True)
        S=wt.spans(sent, toks)
        subsents=[]
        if any(any(t.endswith(p) for p in final_punct) for t in toks[:-1]):
            dictx=[]
            i=0
            change=False
            while i<len(toks):
                if toks[i] in ["?", "!"]:
                    if i<len(toks)-1 and toks[i+1]=='"' and (i==len(toks)-2 or S[i][1][1]==S[i+1][1][0]):
                        i+=1
                    subsents.append(sent[:S[i][1][1]])
                    toks=toks[i+1:]
                    sent=sent[S[i][1][1]:].strip()
                    S=wt.spans(sent, toks)
                    i=-1
                    change=True

                elif i<len(toks)-1 and toks[i].endswith(".") and ((i<len(toks)-1 and toks[i+1].istitle() and not toks[i+1].endswith(".")) or (i<len(toks)-2 and toks[i+1]=='"' and toks[i+2].istitle() and not toks[i+2].endswith("."))) and not (toks[i].lower()=="st." and toks[i+1]=="C"):
                    if i<len(toks)-1 and toks[i+1]=='"':
                        if i==len(toks)-2 or S[i][1][1]==S[i+1][1][0]:
                            i+=1
                        subsents.append(sent[:S[i][1][1]])
                        toks=toks[i+1:]
                        sent=sent[S[i][1][1]:].strip()
                        S=wt.spans(sent, toks)
                        i=-1
                        change=True
                    else:
                        if not dictx: #and not change:
                            #NOTE: check
                            dictx=pt.pos_tag(toks)
                        if dictx[i+1]["ner"]=="O":
                            subsents.append(sent[:S[i][1][1]])
                            toks=toks[i+1:]
                            sent=sent[S[i][1][1]:].strip()
                            S=wt.spans(sent, toks)
                            i=-1
                            change=True
                elif toks[i]==".":
                    break
                i+=1
        if sent:
            subsents.append(sent)
    else:
        subsents=[sent]
    return subsents


def split_sent_temp(sent):
    new_strings=[]
    i=0
    while i<len(sent):
        char=sent[i]
        if char in ["?", "!"]:
            new_strings.append(sent[:i+1])
            #print(sent[:i+1])
            sent=sent[i+1:].lstrip()
            i=0
        elif len(sent)-2>i>1 and char in ["."] and (sent[i-1].isalpha() or sent[i-1].isnumeric()) and sent[i+1]==" " and sent[i+2].isalpha() and sent[i+2].isupper():
            new_strings.append(sent[:i+1])
            #print(sent[:i+1])
            sent=sent[i+1:].lstrip()
            i=0
        elif i==len(sent)-1:
            new_strings.append(sent)
        i+=1
    return new_strings