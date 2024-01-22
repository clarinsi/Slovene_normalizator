import nltk

def next(i, toks, howmuch=1):
    if i+howmuch<len(toks):
        return toks[i+howmuch]
    else:
        return ""

def spans(sent, toks=None):
    if not toks:
        toks=nltk.word_tokenize(sent)
    offset = 0
    indexes=[]
    for tok in toks:
        offset = sent.find(tok, offset)
        indexes.append((tok, [offset, offset+len(tok)]))
        offset += len(tok)
        #print (tok, offset)
    return indexes

def dot_in_the_middle(tok, dot="."):
    if tok.count(dot)==1 and tok.index(dot)!=0 and tok.index(dot)!=len(tok)-1:
        return True
    return False

def content_word(tok):
    if any(char.isalnum() for char in tok): return True
    return False


#mixed združi zadnjo piko s prejšnjim tokenom, če je alfa; sicer narazen 
def word_tokenizer(sent, include_last_dot=False, include_spans=False, support_spelling=False, mixed=False):
    toks=spans(sent)
    if mixed: include_last_dot=False
    trutoks=[]
    i=0
    sub=1
    if include_last_dot==True:
        sub=0
    while i<len(toks):
        t=toks[i][0]
        if t=="." and i>0 and i<len(toks)-sub and toks[i-1][1][1]==toks[i][1][0] and any([content_word(x) for x in [x[0] for x in toks[i+1:]]]):
            new=trutoks[-1]+t
            trutoks=trutoks[:-1]
            trutoks.append(new)
        elif t in ['``', "''"]:
            trutoks.append('"')
        #elif 0<i<len(toks)-1 and t=="@" and dot_in_the_middle(toks[i-1][0]) and dot_in_the_middle(toks[i+1][0]):
        elif 0<i<len(toks)-1 and t=="@" and toks[i-1][1][1]==toks[i][1][0] and toks[i][1][1]==toks[i+1][1][0]:
            new=trutoks[-1]+t+toks[i+1][0]
            trutoks=trutoks[:-1]
            trutoks.append(new)
            i+=1
        elif support_spelling and t=="@" and any("|" in x for x in [next(i, toks)[0], next(i, toks, -1)[0]]):
            if i>0 and ("|" in toks[i-1][0] or len(toks[i-1][0])==1) and toks[i-1][1][1]==toks[i][1][0]:
                subs=toks[i-1][0]+t
                trutoks=trutoks[:-1]
                i+=1
                while i<=len(toks) and (toks[i][0]=="@" or "|" in toks[i][0]) and toks[i-1][1][1]==toks[i][1][0]:
                    subs+=toks[i][0]
                    i+=1
                i-=1
                trutoks.append(subs)
            else:
                trutoks.append(t)
        else:
            trutoks.append(t)
        i+=1
    if mixed and len(trutoks)>1:
        if trutoks[-1].endswith(".") and trutoks[-2].isalpha():
            trutoks=trutoks[:-2]+["".join(trutoks[-2:])]
    if include_spans:
        return spans(sent, trutoks)
    return trutoks