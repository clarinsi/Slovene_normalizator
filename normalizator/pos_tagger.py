import classla
import requests

class PosTagger:
    _instance = None
    classla_pos_tagger = None
    remote = False

    def __new__(cls, remote = False):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.remote = remote
            cls._instance.initialize()
        return cls._instance       


    def initialize(self):
        if not self.remote and self.classla_pos_tagger is None:
            classla.download("sl")
            self.classla_pos_tagger = classla.Pipeline(lang="sl", tokenize_pretokenized=True)

    def pos_tag(self, toks):
        if self.remote:
            response = requests.post('http://localhost:8091/pos_tag', json={'sentence': toks})
            return response.json()
        else:
            return self.classla_pos_tagger([toks]).to_dict()[0][0]
