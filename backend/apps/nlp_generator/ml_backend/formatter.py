# # nlp_generator/ml_generator/formatter.py
# from .distractor_gen import get_distractors
# import random

# def format_to_question_objects(questions, paragraph, topic_ids, difficulty):
#     formatted_questions = []

#     for q in questions:
#         # Naively pick first word after 'answer:' as correct answer (customize later)
#         correct_answer = "Answer"  # <-- Replace with real extraction if available
#         distractors = get_distractors(correct_answer)

#         all_options = [correct_answer] + distractors
#         random.shuffle(all_options)

#         options_dict = {chr(65+i): opt for i, opt in enumerate(all_options)}
#         correct_key = next(k for k, v in options_dict.items() if v == correct_answer)

#         question_obj = {
#             "question_text": q,
#             "question_type": "MCQ",
#             "difficulty": difficulty,
#             "topics": topic_ids,
#             "options": options_dict,
#             "correct_answer": correct_key,
#             "metadata": {
#                 "explanation": "Auto-generated via ML",
#                 "source": paragraph[:100] + "..."
#             }
#         }
#         formatted_questions.append(question_obj)

#     return formatted_questions
