from flask import Flask, request, jsonify
import classla
from normalizator.super_tools.word_tokenizer import word_tokenizer, spans
from normalizator.word import Word
from normalizator import PosTagger

classla.download("sl")
classla.download("sl", type='web')


# Initialize Flask app
app = Flask(__name__)


# Instantiate the PosTagger
pos_tagger = PosTagger()

@app.route('/pos_tag', methods=['POST'])
def pos_tag():
    content = request.json
    sentence = content['sentence']
    result = pos_tagger.pos_tag(sentence)
    return jsonify(result)

@app.route('/analyze', methods=['POST'])
def analyze():
    content = request.json
    sentence = content['sentence']
    result = pos_tagger.analyze(sentence)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=8091)  # The service will run on localhost:5000
