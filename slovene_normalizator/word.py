class Word:
    def __init__(self, word=""):
        self.text = word
        self.un_normalized = word
        self.normalized = word
        self.last_word = -1  # true if last word in a sentence, false if not, -1 if not sure. Useful when rebuilding sentences after Classla pos tagger
        self.word_class = ""
        self.supertype=""
        self.type = ""
        self.subtype=""
        self.tag = ""
        self.value = None  # in case it is or contains a number, this is its value
        self.status = "Normal"
        self.processed = False
        self.declension = ""
        self.prefix_punct = ""
        self.suffix_punct = ""
        
    def toString(self, normalized="true"):
        # return self.prefix_punct + self.normalized + self.suffix_punct
        if normalized == "true":
            return self.normalized
        else:
            return self.un_normalized