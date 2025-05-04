import os
import django
from django.utils import timezone

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.content.models import QuestionApproval
from apps.accounts.models import User

def approve_all_questions():
    try:
        # Fetch the admin user "mudasir"
        admin = User.objects.get(username="mudasir")
        # Get all QuestionApproval entries with status PENDING
        approvals = QuestionApproval.objects.filter(status='PENDING')
        updated_count = 0

        for approval in approvals:
            # Update the approval status and related fields
            approval.status = 'APPROVED'
            approval.reviewed_by = admin
            approval.reviewed_at = timezone.now()
            approval.review_notes = 'Bulk approved via script by mudasir'
            approval.save()
            # The save will trigger the QuestionApprovalAdmin's save_model logic,
            # which sets question.is_active = True
            updated_count += 1

        print(f"Approved {updated_count} questions.")
    except User.DoesNotExist:
        print("Admin user 'mudasir' not found. Please ensure the user exists.")

if __name__ == "__main__":
    approve_all_questions()