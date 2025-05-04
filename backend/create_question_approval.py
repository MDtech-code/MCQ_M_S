import os
import django
from django.utils import timezone

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.content.models import Question, QuestionApproval
from apps.accounts.models import User

def create_question_approvals():
    try:
        # Fetch the admin user with username "mudasir"
        admin = User.objects.get(username="mudasir")
        # Get all questions that don't have an approval entry yet
        questions = Question.objects.filter(approval__isnull=True)
        created_count = 0

        for question in questions:
            # Create a QuestionApproval entry for each question
            QuestionApproval.objects.create(
                question=question,
                status='PENDING',
                flagged_by_system=False,
                flag_reason='',
                reviewed_by=admin,
                reviewed_at=timezone.now(),  # Set to current time
                review_notes='Created via script for admin approval by mudasir'
            )
            created_count += 1

        print(f"Created {created_count} QuestionApproval entries for existing questions.")
    except User.DoesNotExist:
        print("Admin user 'mudasir' not found. Please ensure the user exists.")

if __name__ == "__main__":
    create_question_approvals()