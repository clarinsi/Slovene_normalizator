# Sintaktični normalizator

Namen normalizatorja je, da vse elemente, ki niso zapisani v črkah in v polni obliki, zapiše z besedami (npr. številke, okrajšave, datume, simbole).

## Priprava za uporabo

Predpogoj za uporabo je nameščen **Python v3.9** in **pip**.

#### Windows:

1. `py -m venv env`
2. `.\env\Scripts\activate`
3. `pip install -r requirements.txt`

#### MAC/Linux:

1. `python3 -m venv env`
2. `source env/bin/activate`
3. `pip install -r requirements.txt`

## Uporaba

Glavna metoda se nahaja v direktoriju `normalizator`/`main_normalization.py`, kliče pa se z metodo `normalize_text(text: string)`.

Na primer:
```python
normalize_text("Sodobna definicija Celzijeve temperaturne lestvice, ki velja od leta 1954, je, da je temperatura trojne točke vode enaka 0,01 °C.") 
```
Normalizator vrne rezultat v obliki slovarja (dictionary), in sicer z naslednjimi ključi: `input_text` je vhodno besedilo v obliki niza, `normalized_text` je normalizirano besedilo v obliki niza, `status` je status normalizacije v obliki celega števila in `logs` je seznam terk vseh sprememb v obliki (izvirni element, normalizirani element).

```python
{'input_text': 'Sodobna definicija Celzijeve temperaturne lestvice, ki velja od leta 1954, je, da je temperatura trojne točke vode enaka 0,01 °C.',
'normalized_text': 'Sodobna definicija Celzijeve temperaturne lestvice, ki velja od leta tisoč devetsto štiriinpetdeset, je, da je temperatura trojne točke vode enaka nič celih nič ena stopinje Celzija.',
'status': 1,
'logs': [('1954', 'tisoč devetsto štiriinpetdeset'), ('0,01', 'nič celih nič ena'), ('°C', 'stopinje Celzija')]}
```

## Status normalizacije

Normalizator v izhodu vrne tudi status normalizacije. Statusi so cela števila od -2 do 2. Pomeni posameznega statusa so naslednji:

- `-2` Težava z normalizacijo vsaj ene povedi.
- `-1` Težava z normalizacijo vsaj enega tokena.
- `0` Normalizacija ni potrebna.
- `1` Normalizacija uspešna.
- `2` Besedilo vsebuje tip tokena, ki potrebuje normalizacijo, vendar še ni podprt.

## Nastavitve

Opcijsko lahko normalizatorju dodamo polje `custom_config`. Če tega parametra ne podamo, se uporabijo osnovne nastavitve (osnovna konfiguracijska datoteka).

Spremeniti je mogoče samo posamezne parametre. Parametri, ki niso definirani, bodo ostali takšni, kot so določeni v osnovni konfiguracijski datoteki (`normalizator\config\basic_config.json`).

```
custom_config={
   "abbr":{
      "normalize":"true",
      "include":{
         "lekt.":{
            "lektor+lektorica":"NOUN"
         }
      },
      "exclude":[
         "dr.",
         "mag."
      ],
      "set":[
         
      ]
   },
   "tokenize_sentences":"false"
}
```

Kategorijam, ki temeljijo na vnaprej definiranem naboru elementov lahko dodamo polje ```include```, kjer lahko element dodamo v množico ali prepišemo obstoječi element z drugačnim pomenom, kot ga želimo.

Če želimo iz nabora odstraniti elemente, dodamo polje ```exclude```, kjer določimo ključe, ki naj se iz nabora odstranijo.
Če želimo popolnoma spremeniti nabor, dodamo polje ```set```, ki bo prepisal obstoječi nabor.

## Podprte kategorije

### Številke

Kategorija številke (v konfiguracijski datoteki pod poljem ```num```; prednastavljeno ```True```) je sestavljena iz več podkategorij, in sicer:
cele številke (```number```), vrstilni števniki (```ordinal_number```), decimalne številke (```decimal_number```), ulomki (```fraction```), ure (```hour```), razdelki (npr. poglavje 3.1.1; ```section```) rezultati (npr. 1 : 2; ```result```), telefonske številke (```phone_number```), datumi (```date```), kjer lahko dodatno izberemo še način izgovorjave meseca (```pronunciation_month```) in leta (```pronunciation_year```), zapisi kompleksnega trajanja (npr. 2:26,17; ```complex_duration```), alfanumerični tokeni (```alnum```) in številke z znakom krat (```times```).

  ### Rimske številke

Rimske številke so v konfiguracijski datoteki shranjene pod parametrom ```roman_numeral```. Prednastavljena nastavitev je ```True```.

### Intervali

Intervali so v konfiguracijski datoteki shranjeni pod parametrom ```interval```. Prednastavljena nastavitev je ```True```.
  
### E-maili

E-maili so v konfiguracijski datoteki shranjeni pod parametrom ```email```. Prednastavljena nastavitev je ```True```.
  
### Simboli

Simboli so v konfiguracijski datoteki shranjeni pod parametrom ```symbol```. Prednastavljena nastavitev je ```True```.

Nabor podprtih simbolov je sledeč:

```json    
{
   "$":"dolar",
   ",":"vejica",
   "-":"-",
   "–":"–",
   "_":"podčrtaj",
   "%":"odstotek",
   "#":"lojtra",
   "@":"afna",
   "+":"plus",
   "×":"krat",
   "*":"krat",
   "/":"skozi",
   ":":"dvopičje",
   ">":"je več kot",
   "<":"je manj kot",
   "<=":"je manj ali enako",
   ">=":"je več ali enako",
   "=":"je enako",
   "√":"koren",
   "∑":"vsota",
   "¬":"negacija",
   "∞":"neskončno",
   "≠":"ni enako",
   "≡":"je ekvivalentno",
   "≪":"je veliko manjše",
   "≫":"je veliko večje",
   "&":"in",
   "∀":"za vsak",
   "∃":"obstaja",
   "∈":"je element",
   "Γ":"veliki gama",
   "δ":"veliki delta",
   "Δ":"delta",
   "π":"pi",
   "∏":"produkt",
   "σ":"sigma",
   "α":"alfa",
   "β":"beta",
   "γ":"gama",
   "ε":"epsilon",
   "λ":"lambda",
   "ξ":"ksi",
   "τ":"tau",
   "ψ":"psi",
   "ω":"omega",
   "≈":"je približno enako",
   "±":"plus minus",
   "⊆":"je podmnožica",
   "⊂":"je prava podmnožica",
   "⊄":"ni podmnožica"
}
```
### Enote

Enote so v konfiguracijski datoteki shranjene pod parametrom ```unit```. Prednastavljena nastavitev je ```True```.

Nabor podprtih enot je sledeč:

```json
{
   "dan":"dan",
   "mesec":"mesec",
   "m2":"kvadratniMeter",
   "m3":"kubicniMeter",
   "ha":"hektar",
   "mol":"mol",
   "kcal":"kalorija",
   "tbl.":"tableta",
   "KM":"konjskaMoc",
   "´":"sekunda",
   "´´":"minuta",
   "˝":"palec",
   "‰":"promil",
   "B":"bajt",
   "min":"minuta",
   "m":"meter",
   "g":"gram",
   "l":"liter",
   "L":"liter",
   "t":"tona",
   "b":"bar",
   "N":"newton",
   "Pa":"paskal",
   "V":"volt",
   "W":"vat",
   "A":"amper",
   "s":"sekunda",
   "h":"ura",
   "K":"kelvin",
   "Hz":"herc",
   "J":"džul",
   "F":"farad",
   "Ω":"ohm",
   "°":"stopinja",
   "°C":"stopinjaCelzija",
   "°F":"stopinjaFahrenheita",
   "EUR":"evro",
   "SIT":"tolar",
   "€":"evro",
   "%":"odstotek",
   "$":"dolar"
}
```

### Okrajšave

Okrajšave so v konfiguracijski datoteki shranjene pod parametrom ```abbr```. Prednastavljena nastavitev je ```True```.

Okrajšave se v konfiguracijsko datoteko doda kot ključ `{"okrajšava": {"lema1+lema2": "POS"}}`. Če ne želimo, da se okrajšava sklanja, lahko na mesto oznake za `POS`, dodamo oznako `"FIXED"`.

Nabor okrajšav je sledeč:

```json 
{
   "g.":{
      "gospod":"NOUN"
   },
   "dr.":{
      "doktor+doktorica":"NOUN"
   },
   "mag.":{
      "magister+magistrica":"NOUN"
   },
   "prof.":{
      "profesor+profesorica":"NOUN"
   },
   "asist.":{
      "asistent+asistentka":"NOUN"
   },
   "doc.":{
      "docent+docentka":"NOUN"
   },
   "ing.":{
      "inženir+inženirka":"NOUN"
   },
   "gdč.":{
      "gospodična":"NOUN"
   },
   "psih.":{
      "psiholog+psihologinja":"NOUN"
   },
   "prim.":{
      "primarij+primarijka":"NOUN"
   },
   "spec.":{
      "specialist+specialistka":"NOUN"
   },
   "kem.":{
      "kemik+kemičarka":"NOUN"
   },
   "št.":{
      "številka":"NOUN"
   },
   "tbl.":{
      "tableta":"NOUN"
   },
   "žl.":{
      "žlica":"NOUN"
   },
   "maks.":{
      "maksimalen":"ADJ"
   },
   "roj.":{
      "rojen":"ADJ"
   },
   "kl.":{
      "kliničen":"ADJ"
   },
   "izr.":{
      "izreden":"ADJ"
   },
   "dipl.":{
      "diplomiran":"ADJ"
   },
   "univ.":{
      "univerziteten":"ADJ"
   },
   "ev.":{
      "eventuelen":"ADJ"
   },
   "pribl.":{
      "približno":"ADV"
   },
   "oz.":{
      "oziroma":"ADV"
   },
   "cca.":{
      "cirka":"ADV"
   },
   "ge.":{
      "gospe":"FIXED"
   },
   "go.":{
      "gospo":"FIXED"
   },
   "el.":{
      "elektronski":"ADJ"
   },
   "čl.":{
      "člen":"NOUN"
   },
   "odst.":{
      "odstavek":"NOUN"
   },
   "sv.":{
      "svet":"ADJ"
   },
   "tj.":{
      "to je":"FIXED"
   },
   "itd.":{
      "in tako dalje":"FIXED"
   },
   "itn.":{
      "in tako naprej":"FIXED"
   },
   "ipd.":{
      "in podobno":"FIXED"
   },
   "npr.":{
      "na primer":"FIXED"
   },
   "ddr.":{
      "dvojen_doktor+doktorica":"ADJ_NOUN"
   },
   "t. i.":{
      "tako_imenovan":"ADV_ADJ"
   },
   "pr. n. št.":{
      "pred_našim_štetjem":"FIXED"
   }
}
```

### Povezave

Povezave so v konfiguracijski datoteki shranjene pod parametrom ```link```. Prednastavljena nastavitev je ```True```.

### Neznano

Neprepoznani tipi se lahko normalizirajo po principu osnovne normalizacije (znak po znak). Prednastavljena nastavitev je ```False```.


### Stavčna tokenizacija

Če želimo, da se besedilo razbija na povedi, nastavimo parameter ```tokenize_sentences``` na ```True```. Prednastavljena nastavitev je ```False```.