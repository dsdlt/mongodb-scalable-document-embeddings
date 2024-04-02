import spacy
from collections import Counter

# This downloads a small english model. You can also use 'en_core_web_lg' for larger models, but they are much slower to load and process text with.  
#python -m spacy download en_core_web_sm  

def init_library(model):
    nlp = spacy.load(model)
    return nlp

def extract_tags(lyrics, nlp):
    doc = nlp(lyrics)

    tags = []
    tags_list = []
    for token in doc:
        if(token.head.pos_ == 'NOUN' ):
            tags.append(token.head.text)
    data = Counter(tags)
    tags = data.most_common(10)
    for tag in tags:
        tags_list.append(tag[0])
    return tags_list