from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny,IsAuthenticated
from apps.common.authentication import CookieTokenAuthentication
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from django.contrib import messages
from apps.content.serializers import QuestionSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from apps.common.throttles import CustomUserRateThrottle
from apps.common.permissions import IsTeacher
from .serializers import ParagraphInputSerializer
from apps.nlp_generator.utils.mcq_generator import generate_mcqs
from django.shortcuts import redirect
from django.contrib import messages
from apps.content.models import Topic,Subject

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# nlp_generator/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status, permissions
from django.contrib import messages
from django.shortcuts import redirect,get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
import random

import logging

logger = logging.getLogger(__name__)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class MCQGenerationView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request):
        subjects = Subject.objects.all()
        topics = Topic.objects.all()
        if request.accepted_renderer.format == 'html':
            return Response(
                {
                    'subjects': subjects,
                    'topics': topics,
                    'form_data': {}
                },
                template_name="nlp_generator/mcq_generate.html"
            )
        return Response({"message": "MCQ generation endpoint (GET)"}, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_active or not request.user.is_verified:
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Your account is not active or verified.")
                return redirect('teacher_dashboard')
            return Response(
                {"error": "Account not active or verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ParagraphInputSerializer(data=request.data)
        if not serializer.is_valid():

            if request.accepted_renderer.format == 'html':
                print(serializer.errors)
                messages.error(request, "Invalid paragraph input.")
                subjects = Subject.objects.all()
                topics = Topic.objects.all()
                return Response(
                    {
                        'form_data': request.data,
                        'subjects': subjects,
                        'topics': topics,
                        'errors': serializer.errors
                    },
                    template_name="nlp_generator/mcq_generate.html",
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        paragraph = request.data.get("paragraph")
        topic_ids = request.data.getlist("topics")
        difficulty = request.data.get("difficulty")
        subject_id = request.data.get("subject")

        # Validate inputs
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            topics = Topic.objects.filter(id__in=topic_ids)
            if not topics.exists():
                raise ValueError("No valid topics selected")
            if difficulty not in ['E', 'M', 'H']:
                raise ValueError("Invalid difficulty level")
        except (ValueError, Subject.DoesNotExist) as e:
            if request.accepted_renderer.format == 'html':
                messages.error(request, str(e))
                subjects = Subject.objects.all()
                topics = Topic.objects.all()
                return Response(
                    {
                        'form_data': request.data,
                        'subjects': subjects,
                        'topics': topics,
                        'errors': {"detail": str(e)}
                    },
                    template_name="nlp_generator/mcq_generate.html",
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        generated_questions = generate_mcqs(paragraph)
        logger.debug(f"Generated {len(generated_questions)} questions: {generated_questions}")

        saved_questions = []
        errors = []

        for q_data in generated_questions:
            serializer = QuestionSerializer(data={
                **q_data,
                "subject": subject.id,
                "topics": [t.id for t in topics],
                "difficulty": difficulty,
                "question_type": "MCQ",
            }, context={"request": request})

            if serializer.is_valid():
                question = serializer.save()
                saved_questions.append(question)
            else:
                errors.append({
                    "question_text": q_data["question_text"],
                    "errors": serializer.errors
                })
                logger.warning(f"Validation error for question: {q_data['question_text']} - {serializer.errors}")

        if request.accepted_renderer.format == 'html':
            if saved_questions:
                messages.success(request, f"{len(saved_questions)} questions were generated and saved successfully.")
                return redirect('question_list')
            if errors:
                messages.warning(request, f"{len(errors)} questions failed validation: {', '.join([e['question_text'][:50] for e in errors])}")
            if not generated_questions:
                messages.warning(request, "No valid MCQs could be generated from the provided paragraph.")
            return redirect("generate_mcq")

        return Response(
            {
                "saved_count": len(saved_questions),
                "saved_questions": QuestionSerializer(saved_questions, many=True).data,
                "errors": errors,
            },
            status=status.HTTP_201_CREATED if saved_questions else status.HTTP_400_BAD_REQUEST
        )


# nlp_generator/views_ml.py



# nlp_generator/views.py




# from apps.nlp_generator.ml_backend.question_utils import extract_cloze_and_answer
# from apps.nlp_generator.ml_backend.question_generator import generate_mcqs_from_paragraph
# from apps.nlp_generator.ml_backend.distractor_gen import get_distractors

# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class MCQMLGenerationView(APIView):
#     permission_classes = [IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         subjects = Subject.objects.all()
#         topics = Topic.objects.all()
#         return Response({
#             'subjects': subjects,
#             'topics': topics,
#             'form_data': {}
#         }, template_name="nlp_generator/mcq_generate.html")

#     def post(self, request):
#         serializer = ParagraphInputSerializer(data=request.data)
#         if not serializer.is_valid():
#             messages.error(request, "Invalid paragraph input.")
#             return Response({
#                 "form_data": request.data,
#                 "subjects": Subject.objects.all(),
#                 "topics": Topic.objects.all(),
#                 "errors": serializer.errors
#             }, template_name="nlp_generator/mcq_generate.html", status=400)

#         paragraph = serializer.validated_data["paragraph"]
#         topic_ids = request.data.getlist("topics")
#         difficulty = request.data.get("difficulty")
#         subject_id = request.data.get("subject")

#         try:
#             subject = get_object_or_404(Subject, id=subject_id)
#             topics = Topic.objects.filter(id__in=topic_ids)
#             if not topics.exists():
#                 raise ValueError("No valid topics selected.")
#             if difficulty not in ['E', 'M', 'H']:
#                 raise ValueError("Invalid difficulty level.")
#         except Exception as e:
#             messages.error(request, str(e))
#             return Response({
#                 "form_data": request.data,
#                 "subjects": Subject.objects.all(),
#                 "topics": Topic.objects.all(),
#                 "errors": {"detail": str(e)}
#             }, template_name="nlp_generator/mcq_generate.html", status=400)

#         questions = generate_mcqs_from_paragraph(paragraph)

#         saved_questions = []
#         errors = []

#         for question_text in questions:
#             try:
#                 if "_____" not in question_text:
#                     logger.warning(f"Skipping non-cloze format: {question_text}")
#                     continue

#                 full_question = question_text
#                 correct_answer = full_question.split("_____")[-1].strip().strip('.').split()[0]
#                 base_question, correct_answer = extract_cloze_and_answer(question_text)

#                 distractors = get_distractors(correct_answer)
#                 options = [correct_answer] + distractors
#                 random.shuffle(options)

#                 option_dict = {chr(65 + i): opt for i, opt in enumerate(options)}
#                 correct_option_key = next(k for k, v in option_dict.items() if v == correct_answer)

#                 q_data = {
#                     "question_text": base_question,
#                     "question_type": "MCQ",
#                     "difficulty": difficulty,
#                     "topics": topic_ids,
#                     "options": option_dict,
#                     "correct_answer": correct_option_key,
#                     "metadata": {"explanation": "ML-generated MCQ."}
#                 }

#                 q_serializer = QuestionSerializer(data=q_data, context={"request": request})
#                 if q_serializer.is_valid():
#                     saved_questions.append(q_serializer.save())
#                 else:
#                     logger.warning(f"Invalid question: {q_serializer.errors}")
#                     errors.append({"question": base_question, "errors": q_serializer.errors})

#             except Exception as e:
#                 logger.error(f"Error processing question '{question_text}': {e}")
#                 errors.append({"question": question_text, "errors": str(e)})

#         if request.accepted_renderer.format == "html":
#             if saved_questions:
#                 messages.success(request, f"{len(saved_questions)} questions saved.")
#                 return redirect("question_list")
#             messages.error(request, "All questions failed.")
#             return redirect("generate_mcq_ml")

#         return Response({
#             "saved_count": len(saved_questions),
#             "saved_questions": QuestionSerializer(saved_questions, many=True).data,
#             "errors": errors
#         }, status=201 if saved_questions else 400)




from apps.nlp_generator.ml_backend.question_utils import extract_cloze_and_answer
from apps.nlp_generator.ml_backend.question_generator import generate_mcqs_from_paragraph
from apps.nlp_generator.ml_backend.distractor_gen import get_distractors
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.views import APIView

@method_decorator(ensure_csrf_cookie, name='dispatch')
class MCQMLGenerationView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request):
        subjects = Subject.objects.all()
        topics = Topic.objects.all()
        return Response({
            'subjects': subjects,
            'topics': topics,
            'form_data': {}
        }, template_name="nlp_generator/mcq_generate.html")

    def post(self, request):
        
        serializer = ParagraphInputSerializer(data=request.data)
        if not serializer.is_valid():
            messages.error(request, "Invalid paragraph input.")
            return Response({
                "form_data": request.data,
                "subjects": Subject.objects.all(),
                "topics": Topic.objects.all(),
                "errors": serializer.errors
            }, template_name="nlp_generator/mcq_generate.html", status=400)

        paragraph = serializer.validated_data["paragraph"]
        topic_ids = request.data.getlist("topics")
        difficulty = request.data.get("difficulty")
        subject_id = request.data.get("subject")
        
        try:
            # Validate subject-topics relationship
            subject = get_object_or_404(Subject, id=subject_id)
            topics = Topic.objects.filter(
                id__in=topic_ids,
                subject=subject  # Ensure topics belong to subject
            )
            if topics.count() != len(topic_ids):
                invalid_ids = set(topic_ids) - set(t.id for t in topics)
                raise ValueError(f"Invalid topic IDs: {invalid_ids}")
            
            # Generate questions
            questions = generate_mcqs_from_paragraph(paragraph)
            saved_questions = []
            errors = []

            for raw_question in questions:
                try:
                    base_question, correct_answer = extract_cloze_and_answer(raw_question)
                    distractors = get_distractors(correct_answer)
                    
                    # Prepare options
                    options = [correct_answer] + distractors[:3]
                    random.shuffle(options)
                    option_dict = {chr(65 + i): opt for i, opt in enumerate(options)}
                    correct_key = next(k for k, v in option_dict.items() if v == correct_answer)

                    # Build question object
                    q_data = {
                        "question_text": f"{base_question}?",
                        "question_type": "MCQ",
                        "difficulty": difficulty,
                        "topics": [t.id for t in topics],
                        "options": option_dict,
                        "correct_answer": correct_key,
                        "metadata": {
                            "explanation": "ML-generated MCQ",
                            "source": f"{paragraph[:150]}..." if paragraph else ""
                        }
                    }

                    # Validate and save
                    q_serializer = QuestionSerializer(data=q_data, context={"request": request})
                    if q_serializer.is_valid():
                        saved_questions.append(q_serializer.save())
                    else:
                        errors.append({
                            "question": base_question,
                            "errors": q_serializer.errors
                        })
                        
                except ValueError as e:
                    errors.append({"question": raw_question, "errors": str(e)})
                except Exception as e:
                    logger.error(f"Error processing question: {str(e)}")
                    errors.append({"question": raw_question, "errors": "Internal error"})

            # ... [Keep remaining response handling code] ...
            if request.accepted_renderer.format == "html":
                if saved_questions:
                    messages.success(request, f"{len(saved_questions)} questions saved.")
                    return redirect("question_list")
                messages.error(request, "All questions failed.")
                return redirect("generate_mcq_ml")

        except Exception as e:
            logger.error(f"Generation error: {str(e)}")
            messages.error(request, str(e))
            return Response({
                "form_data": request.data,
                "subjects": Subject.objects.all(),
                "topics": Topic.objects.all(),
                "errors": {"detail": str(e)}
            }, template_name="nlp_generator/mcq_generate.html", status=400)