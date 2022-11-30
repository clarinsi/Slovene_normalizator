#generator Å¡tevil

uses_spaces = True

specific_numbers = {0: "nič", 1: "ena", 2: "dva", 3: "tri", 4: "štiri", 5: "pet", 6: "šest", 7: "sedem", 8: "osem", 9: "devet",
                    10: "deset", 11: "enajst", 20: "dvajset", 100: "sto", 200: "dvesto"}

def number2word_SLO(number):
    if number < 10 and number >= 0:
        return enice[number]

    # Äe je Å¡tevilka med 10 in 20, se bere specifiÄno
    if number < 20 and number > 10:
        return enice[number - 10] + 'najst'

    if number == 10 or number == 20: 
        return desetice[number]
    
    if number < 100:
        if number % 10 == 0:
            return enice[number/10] + 'deset'
        else:
            return 

def space():
    if uses_spaces:
        return(" ")
    else:
        return("")

def list_string(l):
    seznam = ""
    for item in l:
        seznam += item + ", "
    return seznam[:-2]

def izgovorjava_dvomestnega_stevila(i):
    if i in specific_numbers:
        return specific_numbers[i]
    if (i > 10 and i < 20):
        enica = (i % 10)
        zapis = specific_numbers[enica] + "najst"
        return zapis
    if (i > 20 and i < 30):
        enica = (i % 10)
        desetica = i - enica
        zapis = specific_numbers[enica] + "in" + specific_numbers[desetica / 10] + "jset"
        return zapis
    if (i >= 30 and i < 100):
        enica = (i % 10)
        desetica = i - enica
        if i % 10 == 0:
            zapis = specific_numbers[i/10] + "deset"
            return zapis
        else:
            zapis = specific_numbers[enica] + "in" + specific_numbers[desetica/10] + "deset"
            return zapis

def n2w(i):

    if i <= 100:
        return (i, izgovorjava_dvomestnega_stevila(i))
    if (i > 100 and i < 1000):
        enica = i % 100 % 10
        desetica = i % 100 - enica
        stotica = int(i / 100)
        if stotica == 1:
            zapis = "sto" + space() + izgovorjava_dvomestnega_stevila(i%100)
        else:
            zapis = specific_numbers[stotica] + "sto" + space() + izgovorjava_dvomestnega_stevila(i % 100)
            # Äe je enica niÄ, jo reÅ¾em, npr. 250, 400..., ker se ne izgovori
            #print(enica, desetica)
            if enica == 0 and desetica == 0:
                zapis = zapis[:-3]

        if zapis[0:3]=="dva": zapis = "dve"+zapis[3:]
        return (i, zapis.strip())
    
    if (i >= 1000):
        miljonica = int(i / 1000000)
        tisocica = int((i-miljonica*1000000) / 1000)
        stotica = int((i-miljonica*1000000-tisocica*1000) / 100)
        desetica = int((i-miljonica*1000000-tisocica*1000-stotica*100) / 10)
        enica = int(i-miljonica*1000000-tisocica*1000-stotica*100-desetica*10)
        
        tisocica_zapis = ''
        miljonica_zapis = ''
        if tisocica == 1:
            tisocica_zapis = "tisoč" + space()
        elif tisocica > 1: 
            tisocica_zapis = n2w(tisocica)[1] + space() + 'tisoč' + space()
        if miljonica == 1:
            miljonica_zapis = 'milijon' + space()
        elif  miljonica == 2:
            miljonica_zapis = 'dva milijona' + space()
        elif  miljonica == 3 or miljonica == 4:
            miljonica_zapis = n2w(miljonica)[1] + space() + 'milijone' + space()
        elif miljonica > 4:
            miljonica_zapis = n2w(miljonica)[1] + space() + 'milijonov' + space()
        
        if str(i)[-3:]=="000":
            return(i, (miljonica_zapis + tisocica_zapis + n2w(int(str(i)[-3:]))[1])[:-3].strip())
        else:
            return(i, (miljonica_zapis + tisocica_zapis + n2w(int(str(i)[-3:]))[1]).strip())

#vrstilni
specific_numbers_vrstilni = {0: "ničti", 1: "prvi", 2: "drugi", 3: "tretji", 4: "četrti", 5: "peti", 6: "šesti", 7: "sedmi", 8: "osmi", 9: "deveti",
                    10: "deseti", 11: "enajsti", 20: "dvajseti", 100: "stoti", 200: "dvestoti"}

def izgovorjava_dvomestnega_stevila_vrstilni(i):
    if i in specific_numbers:
        return specific_numbers_vrstilni[i]
    if (i > 10 and i < 20):
        enica = (i % 10)
        zapis = specific_numbers[enica] + "najsti"
        return zapis
    if (i > 20 and i < 30):
        enica = (i % 10)
        desetica = i - enica
        zapis = specific_numbers[enica] + space() + "in" + space() + specific_numbers[desetica / 10] + "jseti"
        return zapis
    if (i >= 30 and i < 100):
        enica = (i % 10)
        desetica = i - enica
        if i % 10 == 0:
            zapis = specific_numbers[i/10] + space() + "deseti"
            return zapis
        else:
            zapis = specific_numbers[enica] + space() + "in" + space() + specific_numbers[desetica/10] + space() + "deseti"
            return zapis


def n2wv(i):
    if i <= 100:
        return (i, izgovorjava_dvomestnega_stevila_vrstilni(i).replace(" ", ""))
    if (i > 100 and i < 1000):
        enica = i % 100 % 10
        desetica = i % 100 - enica
        stotica = int(i / 100)
        if stotica == 1:
            zapis = "sto" + space() + izgovorjava_dvomestnega_stevila_vrstilni(i%100)
        else:
            zapis = specific_numbers[stotica] + "sto" + space() + izgovorjava_dvomestnega_stevila_vrstilni(i % 100)
            # Äe je enica niÄ, jo reÅ¾em, npr. 250, 400..., ker se ne izgovori
            #print(enica, desetica)
            if enica == 0 and desetica == 0:
                zapis = zapis[:-5]+zapis[-2:]

        if zapis[0:3]=="dva": zapis = "dve"+zapis[3:]
        zapis=zapis.replace(" ", "")
        return (i, zapis)
    
    if (i >= 1000):
        miljonica = int(i / 1000000)
        tisocica = int((i-miljonica*1000000) / 1000)
        stotica = int((i-miljonica*1000000-tisocica*1000) / 100)
        desetica = int((i-miljonica*1000000-tisocica*1000-stotica*100) / 10)
        enica = int(i-miljonica*1000000-tisocica*1000-stotica*100-desetica*10)
        
        tisocica_zapis = ''
        miljonica_zapis = ''
        if tisocica == 1:
            tisocica_zapis = "tisoč" + space()
        elif tisocica > 1: 
            tisocica_zapis = n2w(tisocica)[1] + space() + 'tisoč' + space()
        if miljonica == 1:
            miljonica_zapis = 'milijon' + space()
        elif  miljonica == 2:
            miljonica_zapis = 'dva milijona' + space()
        elif  miljonica == 3 or miljonica == 4:
            miljonica_zapis = n2w(miljonica)[1] + space() + 'milijone' + space()
        elif miljonica > 4:
            miljonica_zapis = n2w(miljonica)[1] + space() + 'milijonov' + space()
        zapis=(miljonica_zapis + tisocica_zapis + n2wv(int(str(i)[-3:]))[1]).replace(" ", "")
        if str(i)[-3:]=="000":
            zapis=((miljonica_zapis + tisocica_zapis + n2wv(int(str(i)[-3:]))[1]).replace(" ", ""))[:-5]+"i"
        
        return(i, zapis.replace(" ", ""))


# MAIN

# =============================================================================
# print(n2w(3500))
# print(n2w(111111111111)) 
# print(n2w(8))   
# print(n2w(12))
# print(n2w(19))
# print(n2w(10))
# print(n2w(60))
# print(n2w(27))
# print(n2w(89))
# print(n2w(209))
# print(n2w(387))
# print(n2w(999))
# print(n2w(1333))
# print(n2w(2409))
# print(n2w(39806))
# print(n2w(23409888))
# print(n2w(308409388))
# print(n2w(101))
# print(n2w(1999))
# print(n2w(111111))
# print(n2w(1995344))
# =============================================================================
# tosave1=[]
# for i in range(10000):
#     tosave1.append((n2w(i)))
#     basic=n2w(i)[1]
#     nr=str(i)
#     if basic[-2:]=="em":
#         tosave1.append((nr, basic[:-2]+"m"+"imi"))
#         tosave1.append((nr, basic[:-2]+"m"+"ih"))
#         tosave1.append((nr, basic[:-2]+"m"+"im"))
#     elif str(i)[-2:]=="04" or i==4:
#         tosave1.append((nr, basic+"mi"))
#         tosave1.append((nr, basic+"h"))
#         tosave1.append((nr, basic+"m"))
#         tosave1.append((nr, basic[:-1]+"je"))
#     elif str(i)[-2:]=="03":
#         tosave1.append((nr, basic.split()[0]+" tremi"))
#         tosave1.append((nr, basic.split()[0]+" treh"))
#         tosave1.append((nr, basic.split()[0]+" trem"))
#         tosave1.append((nr, basic.split()[0]+" trije"))
#     elif i==3:
#         tosave1.append((nr, "tremi"))
#         tosave1.append((nr, "treh"))
#         tosave1.append((nr, "trem"))
#         tosave1.append((nr, "trije"))
#     elif str(i)[-2:]=="02":
#         tosave1.append((nr, basic.split()[0]+" dvema"))
#         tosave1.append((nr, basic.split()[0]+" dveh"))
#     elif i==2:
#         tosave1.append((nr, "dve"))
#         tosave1.append((nr, "dvema"))
#         tosave1.append((nr, "dveh"))
#     elif str(i)[-2:]=="01":
#         tosave1.append((nr, basic.split()[0]+" enemu"))
#         tosave1.append((nr, basic.split()[0]+" enim"))
#         tosave1.append((nr, basic.split()[0]+" enem"))
#     elif i==1:
#         tosave1.append((nr, "enemu"))
#         tosave1.append((nr, "enim"))
#         tosave1.append((nr, "enem"))
#         tosave1.append((nr, "enega"))
#     else:
#         tosave1.append((nr, basic+"imi"))
#         tosave1.append((nr, basic+"ih"))
#         tosave1.append((nr, basic+"im"))
        

# tosave2=[]
# for i in range(10000):
#     tosave2.append((str(i)+'.', (n2wv(i)[1])))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'ega'))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'imi'))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'emu'))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'em'))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'im'))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'ih'))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'a'))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'e'))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'i'))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'o'))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'u'))
#     tosave2.append((str(i)+'.', (n2wv(i)[1][:-1])+'ič'))

    

# with open(r'C:\Users\jelov\OneDrive\Dokumenti\LPT\št_9999_v2.txt', 'w', encoding='utf-8') as file:
#     for el in tosave1:
#         file.write(str(el[0]) + "|" + el[1] + '\n')

# with open(r'C:\Users\jelov\OneDrive\Dokumenti\LPT\št_9999_vrst.txt', 'w', encoding='utf-8') as file:
#     for el in tosave2:
#         file.write(str(el[0]) + "|" + el[1] + '\n')
