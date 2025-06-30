import random
import spacy

nlp = spacy.load("en_core_web_sm")


import re

def preprocess_paragraph(paragraph):
    paragraph = paragraph.replace("—", " ").replace("–", " ").replace("�", "")
    paragraph = re.sub(r'[^\w\s.,!?]', ' ', paragraph)  # Keep basic punctuation, remove odd characters
    return paragraph.strip()

def generate_mcqs(paragraph, max_questions=5):
    paragraph = preprocess_paragraph(paragraph)
    doc = nlp(paragraph)
    questions = []
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip().split()) >= 5]

    # Shuffle sentences to ensure variety
    random.shuffle(sentences)

    for sentence in sentences:
        sent_doc = nlp(sentence)
        candidate_tokens = [
            token for token in sent_doc
            if token.pos_ in ["NOUN", "PROPN"]
            and not token.is_stop
            and len(token.text) > 2
        ]

        if not candidate_tokens:
            continue

        answer_token = random.choice(candidate_tokens)
        answer = answer_token.text
        question_text = sentence.replace(answer, "_____", 1)  # Replace only first occurrence

        # Skip if replacement failed or question is too short
        if question_text == sentence or len(question_text.split()) < 5 or "_____" not in question_text:
            continue

        # Generate distractors
        distractor_pool = [
            token.text for token in doc
            if token.text.lower() != answer.lower()
            and token.pos_ == answer_token.pos_
            and len(token.text) > 2
            and token.text.strip() not in [".", ",", ";", "(", ")", "-", "_"]
        ]

        # Remove duplicates and shuffle
        distractor_pool = list(dict.fromkeys(distractor_pool))
        random.shuffle(distractor_pool)

        distractors = []
        for d in distractor_pool:
            if d.lower() != answer.lower() and d not in distractors:
                distractors.append(d)
            if len(distractors) == 3:
                break

        # Context-aware fallbacks based on POS
        fallback_options = {
            "NOUN": ["Concept", "Element", "Principle", "Theory"],
            "PROPN": ["Newton", "Einstein", "Galileo", "Curie"]
        }.get(answer_token.pos_, ["Term", "Idea", "Object", "Entity"])

        while len(distractors) < 3:
            fallback = random.choice(fallback_options)
            if fallback != answer and fallback not in distractors:
                distractors.append(fallback)

        # Ensure unique options
        all_options = distractors + [answer]
        if len(set(all_options)) != 4:  # Skip if options aren't unique
            continue

        random.shuffle(all_options)
        labeled_options = dict(zip(['A', 'B', 'C', 'D'], all_options))
        correct_option_label = next(label for label, text in labeled_options.items() if text == answer)

        questions.append({
            "question_text": question_text.strip(),
            "correct_answer": correct_option_label,
            "options": labeled_options
        })

        if len(questions) >= max_questions:
            break

    # If fewer than max_questions, try to generate more from remaining sentences
    if len(questions) < max_questions and len(sentences) > len(questions):
        for sentence in sentences[len(questions):]:
            sent_doc = nlp(sentence)
            candidate_tokens = [
                token for token in sent_doc
                if token.pos_ in ["NOUN", "PROPN"]
                and not token.is_stop
                and len(token.text) > 2
            ]

            if not candidate_tokens:
                continue

            answer_token = random.choice(candidate_tokens)
            answer = answer_token.text
            question_text = sentence.replace(answer, "_____", 1)

            if question_text == sentence or len(question_text.split()) < 5 or "_____" not in question_text:
                continue

            distractor_pool = [
                token.text for token in doc
                if token.text.lower() != answer.lower()
                and token.pos_ == answer_token.pos_
                and len(token.text) > 2
                and token.text.strip() not in [".", ",", ";", "(", ")", "-", "_"]
            ]

            distractor_pool = list(dict.fromkeys(distractor_pool))
            random.shuffle(distractor_pool)

            distractors = []
            for d in distractor_pool:
                if d.lower() != answer.lower() and d not in distractors:
                    distractors.append(d)
                if len(distractors) == 3:
                    break

            while len(distractors) < 3:
                fallback = random.choice(fallback_options.get(answer_token.pos_, ["Term", "Idea", "Object", "Entity"]))
                if fallback != answer and fallback not in distractors:
                    distractors.append(fallback)

            all_options = distractors + [answer]
            if len(set(all_options)) != 4:
                continue

            random.shuffle(all_options)
            labeled_options = dict(zip(['A', 'B', 'C', 'D'], all_options))
            correct_option_label = next(label for label, text in labeled_options.items() if text == answer)

            questions.append({
                "question_text": question_text.strip(),
                "correct_answer": correct_option_label,
                "options": labeled_options
            })

            if len(questions) >= max_questions:
                break

    return questions
