import sys
import argparse
from normalizator.pos_tagger import PosTagger 

externalTagger = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('text', help='Text to be normalized')
    parser.add_argument('--externalTagger', action='store_true', help='Set externalTagger to True')
    args = parser.parse_args()

    externalTagger = args.externalTagger  # This sets the global variable
    print(f" externall tagger: {externalTagger}")

    pos_tagger = PosTagger(remote=externalTagger)

    from normalizator.main_normalization import normalize_text

    result = normalize_text(args.text)
    print("Normalized Text:", result)
