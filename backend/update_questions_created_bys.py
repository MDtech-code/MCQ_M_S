import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.accounts.models import User  # Import the custom User model
from apps.content.models import Question
from django.core.exceptions import ObjectDoesNotExist

def update_questions_created_by():
    # Replace 'ali' with the actual username of the teacher if different
    try:
        teacher = User.objects.get(username="ali")
        questions = Question.objects.filter(created_by=None)
        for question in questions:
            question.created_by = teacher
            question.save()
        print(f"Updated {questions.count()} questions with created_by set to {teacher.username}")
    except ObjectDoesNotExist:
        print("Teacher username not found. Please ensure the user exists.")

if __name__ == "__main__":
    update_questions_created_by()