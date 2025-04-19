# apps/content/management/commands/populate_questions.py
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.content.models import Subject, Topic, Question, QuestionApproval
from apps.accounts.models import User
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Populates 10 questions per topic with approvals for all subjects and topics'

    def handle(self, *args, **kwargs):
        try:
            # Get teacher for approvals
            teacher = User.objects.get(email='virjarock@gmail.com', role=User.Role.TEACHER)
        except User.DoesNotExist:
            logger.error("Teacher with email 'virjarock@example.com' not found. Please create a teacher user.")
            self.stdout.write(self.style.ERROR("Teacher 'virjarock@example.com' not found."))
            return

        # Get all subjects and topics
        subjects = Subject.objects.all()
        if not subjects:
            logger.error("No subjects found in the database.")
            self.stdout.write(self.style.ERROR("No subjects found. Please populate subjects first."))
            return

        total_questions_created = 0
        total_approvals_created = 0

        # Use transaction to ensure data integrity
        with transaction.atomic():
            for subject in subjects:
                topics = Topic.objects.filter(subject=subject)
                if not topics:
                    logger.warning(f"No topics found for subject {subject.name}.")
                    self.stdout.write(self.style.WARNING(f"No topics for {subject.name}. Skipping."))
                    continue

                for topic in topics:
                    # Create 10 questions per topic
                    for i in range(1, 11):
                        question_text = f"Question {i} for {topic.name} in {subject.name}"
                        options = {
                            "A": f"Option A for {question_text}",
                            "B": f"Option B for {question_text}",
                            "C": f"Option C for {question_text}",
                            "D": f"Option D for {question_text}"
                        }
                        correct_answer = random.choice(['A', 'B', 'C', 'D'])
                        metadata = {"explanation": f"This is a sample explanation for {question_text}"}
                        difficulty = random.choice(['E', 'M', 'H'])

                        # Create question
                        question = Question.objects.create(
                            question_text=question_text,
                            options=options,
                            correct_answer=correct_answer,
                            metadata=metadata,
                            difficulty=difficulty,
                            is_active=True  # Approved immediately
                        )
                        question.topics.add(topic)  # Link to topic
                        total_questions_created += 1

                        # Create approval
                        QuestionApproval.objects.create(
                            question=question,
                            status='APPROVED'
                        )
                        total_approvals_created += 1

                        logger.info(f"Created question {question.id} for {topic.name} in {subject.name}")
                        self.stdout.write(self.style.SUCCESS(f"Created question {question.id} for {topic.name}"))

            # Summary
            logger.info(f"Created {total_questions_created} questions and {total_approvals_created} approvals.")
            self.stdout.write(self.style.SUCCESS(
                f"Successfully created {total_questions_created} questions and {total_approvals_created} approvals."
            ))