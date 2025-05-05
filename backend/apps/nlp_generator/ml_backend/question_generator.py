from .model_loader import tokenizer, model
import torch

def generate_mcqs_from_paragraph(paragraph, num_questions=3):
    input_text = (
        f"generate {num_questions} fill-in-the-blank questions with answers from this text: {paragraph} "
        "Format each as: 'Question text _____. Answer' </s>"
    )
    
    input_ids = tokenizer.encode(
        input_text, 
        return_tensors="pt", 
        max_length=512, 
        truncation=True
    )

    outputs = model.generate(
        input_ids,
        max_length=128,
        num_return_sequences=num_questions,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        temperature=0.7,
        early_stopping=True
    )

    questions = []
    for output in outputs:
        decoded = tokenizer.decode(output, skip_special_tokens=True)
        if '_____' in decoded and 'Answer' in decoded:
            questions.append(decoded.replace('Answer', '').strip())
    
    return questions[:num_questions]