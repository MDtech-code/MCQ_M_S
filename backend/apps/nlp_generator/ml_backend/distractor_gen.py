import random
import nltk
from nltk.corpus import wordnet

nltk.download('wordnet')

def get_distractors(correct_answer, num_distractors=3):
    distractors = set()
    normalized_answer = correct_answer.strip('.,?!').lower()
    
    # Try synonyms first
    synsets = wordnet.synsets(normalized_answer)
    for synset in synsets:
        for lemma in synset.lemmas():
            candidate = lemma.name().replace('_', ' ').title()
            if candidate.lower() != normalized_answer and candidate not in distractors:
                distractors.add(candidate)
                if len(distractors) >= num_distractors:
                    return list(distractors)
    
    # Try hyponyms if synonyms not enough
    for synset in synsets:
        for hypo in synset.hyponyms():
            candidate = hypo.name().split('.')[0].replace('_', ' ').title()
            if candidate not in distractors:
                distractors.add(candidate)
                if len(distractors) >= num_distractors:
                    return list(distractors)
    
    # Fallback strategy
    fallbacks = ['London', 'Berlin', 'Tokyo', 'Rome', 'Madrid', 'Washington']
    while len(distractors) < num_distractors:
        fake = random.choice(fallbacks)
        if fake != correct_answer:
            distractors.add(fake)
    
    return list(distractors)[:num_distractors]