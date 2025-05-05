def extract_cloze_and_answer(question_text):
    if "_____" not in question_text:
        raise ValueError("Not a valid cloze question format")
    
    parts = question_text.split("_____")
    if len(parts) < 2:
        raise ValueError("Invalid question format")
    
    answer_part = parts[1].strip()
    if not answer_part:
        raise ValueError("No answer found after blank")
    
    # Extract first word and clean punctuation
    answer = answer_part.split()[0].strip('.,?!')
    base_question = parts[0].strip() + "_____"
    
    return base_question, answer