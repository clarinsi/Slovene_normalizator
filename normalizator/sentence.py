from normalizator.word import Word
import classla
classla.download("sl")
from super_tools.word_tokenizer import word_tokenizer, spans
classla_pos_tagger = classla.Pipeline(lang="sl", tokenize_pretokenized=True)

def pos_tag(toks):
    return classla_pos_tagger([toks]).to_dict()[0][0]

def add_tags(sentence):
    sentence_length=sentence.length()
    for i in range(sentence_length):
        word=sentence.get_word(i)
        word.tag=sentence.tags[i]


class Sentence:

    def __init__(self, text=None, tokenized=True):
        self.text=text
        self.tokens = word_tokenizer(self.text, include_last_dot=False)
        self.tokenized = tokenized
        self.tags = None
        self.words = [Word(x) for x in self.tokens]
        self.status=1
        
    def length(self):
        return len(self.tokens)

    def tag(self):
        if not self.tags:
            self.tags=pos_tag(self.tokens)
            add_tags(self)

    def get_word(self, index):
        if index >= len(self.tokens) or index < 0:
            return None  # to avoid out of range errors
        return self.words[index]

    def set_word(self, word: Word, index):
        self.words[index] = word

    def is_last_word(self, index):
        return index == self.length() - 1

    def is_first_word(self, index):
        return index == 0

    def to_string(self):
        sentence_normalized = ""
        for word in self.words:
            sentence_normalized += word.prefix_punct + word.un_normalized + word.suffix_punct + " "

        return sentence_normalized.strip()

    def track_changes(self):
        return [(x.text, x.normalized) for x in self.words if x.text!=x.normalized]