# apps/examination/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from .models import Test, TestAttempt
from .serializers import TestSerializer,TestAttemptSerializer, StudentResponseSerializer
from apps.common.throttles import CustomUserRateThrottle
from apps.accounts.models import User
from django.core.paginator import Paginator, EmptyPage
from django.utils import timezone
from .models import Test, TestAttempt, StudentResponse
from datetime import timedelta


import logging
logger = logging.getLogger(__name__)

class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.TEACHER

class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.STUDENT

class TestCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [TokenAuthentication]
    throttle_classes = [CustomUserRateThrottle]

    def post(self, request):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to create test")
            return Response({"error": "Account not active or verified"}, status=status.HTTP_403_FORBIDDEN)
        serializer = TestSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            test = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Test creation failed for {request.user.email}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class TestListView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [TokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         if not request.user.is_active:
#             logger.warning(f"Inactive user {request.user.email} attempted to list tests")
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
#         if request.user.role == User.Role.TEACHER:
#             queryset = Test.objects.filter(created_by=request.user)
#         elif request.user.role == User.Role.STUDENT:
#             queryset = Test.objects.all()
#         else:
#             logger.warning(f"Invalid role {request.user.role} for {request.user.email}")
#             return Response({"error": "Invalid role"}, status=status.HTTP_403_FORBIDDEN)

#         # Filters
#         subject_id = request.query_params.get('subject')
#         if subject_id:
#             try:
#                 queryset = queryset.filter(subjects__id=subject_id)
#             except ValueError:
#                 return Response({"error": "Invalid subject ID"}, status=status.HTTP_400_BAD_REQUEST)

#         status_filter = request.query_params.get('status')
#         if status_filter == 'active':
#             queryset = queryset.filter(schedule_start__lte=timezone.now(), schedule_end__gte=timezone.now())
#         elif status_filter == 'upcoming':
#             queryset = queryset.filter(schedule_start__gt=timezone.now())
#         elif status_filter == 'expired':
#             queryset = queryset.filter(schedule_end__lt=timezone.now())

#         paginator = Paginator(queryset, 20)
#         page = request.query_params.get('page', 1)
#         try:
#             tests = paginator.page(page)
#         except EmptyPage:
#             logger.warning(f"Invalid page {page} for test list by {request.user.email}")
#             return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)

#         serializer = TestSerializer(tests, many=True)
#         logger.info(f"Test list retrieved by {request.user.email} (role: {request.user.role})")
#         return Response({
#             "count": paginator.count,
#             "results": serializer.data
#         })

class TestUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [TokenAuthentication]
    throttle_classes = [CustomUserRateThrottle]

    def put(self, request, pk):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to update test {pk}")
            return Response({"error": "Account not active or verified"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            test = Test.objects.get(pk=pk, created_by=request.user)
        except Test.DoesNotExist:
            logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
            return Response({"error": "Test not found or not owned by you"}, status=status.HTTP_404_NOT_FOUND)

        if TestAttempt.objects.filter(test=test).exists():
            logger.warning(f"Test {pk} update failed: Already attempted")
            return Response({"error": "Cannot update test with attempts"}, status=status.HTTP_403_FORBIDDEN)

        serializer = TestSerializer(test, data=request.data, context={'request': request})
        if serializer.is_valid():
            updated_test = serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.warning(f"Test update failed for {request.user.email}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TestDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [TokenAuthentication]
    throttle_classes = [CustomUserRateThrottle]

    def delete(self, request, pk):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to delete test {pk}")
            return Response({"error": "Account not active or verified"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            test = Test.objects.get(pk=pk, created_by=request.user)
        except Test.DoesNotExist:
            logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
            return Response({"error": "Test not found or not owned by you"}, status=status.HTTP_404_NOT_FOUND)

        if TestAttempt.objects.filter(test=test).exists():
            logger.warning(f"Test {pk} deletion failed: Already attempted")
            return Response({"error": "Cannot delete test with attempts"}, status=status.HTTP_403_FORBIDDEN)

        test.delete()
        logger.info(f"Test {pk} deleted by {request.user.email}")
        return Response(status=status.HTTP_204_NO_CONTENT)



# apps/examination/views.py



class TestListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        logger.info(f"TestListView accessed by {request.user.email} (role: {request.user.role})")
        
        if request.user.role == User.Role.TEACHER:
            queryset = Test.objects.filter(created_by=request.user)
        elif request.user.role == User.Role.STUDENT:
            queryset = Test.objects.all()  # Students see all available tests
        else:
            logger.warning(f"Unauthorized role: {request.user.role}")
            return Response({"error": "Invalid user role"}, status=status.HTTP_403_FORBIDDEN)

        subject_id = request.query_params.get('subject')
        if subject_id:
            try:
                queryset = queryset.filter(subjects__id=subject_id)
            except ValueError:
                logger.error(f"Invalid subject ID: {subject_id}")
                return Response({"error": "Invalid subject ID"}, status=status.HTTP_400_BAD_REQUEST)

        logger.debug(f"Queryset for {request.user.email}: {queryset.values('id', 'title', 'duration')}")
        
        serializer = TestSerializer(queryset, many=True)
        return Response(serializer.data)

class TestAttemptView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        serializer = TestAttemptSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            attempt = serializer.save()
            logger.info(f"Attempt {attempt.id} started by {request.user.email} for test {attempt.test.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            attempt = TestAttempt.objects.get(pk=pk, student=request.user)
        except TestAttempt.DoesNotExist:
            return Response({"error": "Attempt not found or not yours"}, status=status.HTTP_404_NOT_FOUND)
        
        if attempt.end_time:
            return Response({"error": "Attempt already submitted"}, status=status.HTTP_400_BAD_REQUEST)
        
        time_limit = attempt.start_time + timedelta(minutes=attempt.test.duration)
        now = timezone.now()
        if now > time_limit:
            attempt.end_time = time_limit
            attempt.calculate_score()
            attempt.save()
            logger.info(f"Attempt {attempt.id} auto-expired for {request.user.email} with score {attempt.score}")
            return Response({"error": "Test duration expired", "id": attempt.id, "score": attempt.score}, status=status.HTTP_400_BAD_REQUEST)
        
        attempt.end_time = now
        attempt.calculate_score()
        attempt.save()
        logger.info(f"Attempt {attempt.id} submitted by {request.user.email} with score {attempt.score}")
        return Response({"id": attempt.id, "score": attempt.score}, status=status.HTTP_200_OK)

    def get(self, request):
        attempts = TestAttempt.objects.filter(student=request.user)
        serializer = TestAttemptSerializer(attempts, many=True)
        return Response(serializer.data)

class StudentResponseView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        serializer = StudentResponseSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            response = serializer.save()
            logger.info(f"Response {response.id} saved for question {response.question.id} by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class TestAttemptView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [TokenAuthentication]

#     def post(self, request):
#         serializer = TestAttemptSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             attempt = serializer.save()
#             logger.info(f"Attempt {attempt.id} started by {request.user.email} for test {attempt.test.id}")
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def patch(self, request, pk):
#         try:
#             attempt = TestAttempt.objects.get(pk=pk, student=request.user)
#         except TestAttempt.DoesNotExist:
#             return Response({"error": "Attempt not found or not yours"}, status=status.HTTP_404_NOT_FOUND)
        
#         if attempt.end_time:
#             return Response({"error": "Attempt already submitted"}, status=status.HTTP_400_BAD_REQUEST)
        
#         attempt.end_time = timezone.now()
#         score = attempt.calculate_score()
#         attempt.save()
#         logger.info(f"Attempt {attempt.id} submitted by {request.user.email} with score {score}")
#         return Response({"id": attempt.id, "score": score}, status=status.HTTP_200_OK)

#     def get(self, request):
#         attempts = TestAttempt.objects.filter(student=request.user)
#         serializer = TestAttemptSerializer(attempts, many=True)
#         return Response(serializer.data)

# class StudentResponseView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [TokenAuthentication]

#     def post(self, request):
#         serializer = StudentResponseSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             response = serializer.save()
#             logger.info(f"Response {response.id} saved for question {response.question.id} by {request.user.email}")
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



























# # apps/examination/views.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status, permissions
# from rest_framework.authentication import TokenAuthentication
# from .models import Test
# from .serializers import TestSerializer
# from apps.common.throttles import CustomUserRateThrottle
# from apps.accounts.models import User
# from .tasks import send_test_notification_task
# from django.utils import timezone
# from django.core.paginator import Paginator, EmptyPage
# import logging
# logger = logging.getLogger(__name__)

# class IsTeacher(permissions.BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == User.Role.TEACHER

# class TestCreateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [TokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def post(self, request):
#         if not request.user.is_active:
#             logger.warning(f"Inactive teacher {request.user.email} attempted to create test")
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
#         serializer = TestSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             # Validate question_filters (async via Celery)
#             question_filters = serializer.validated_data.get('question_filters', {})
#             if question_filters:
#                 from .tasks import validate_question_filters_task
#                 validate_question_filters_task.delay(
#                     serializer.validated_data['question_filters'],
#                     on_success=lambda: serializer.save(creator=request.user)
#                 )
#             else:
#                 test = serializer.save(creator=request.user)
#                 send_test_notification_task.delay(
#                     test.id, request.user.email, action="created"
#                 )
#                 logger.info(f"Test {test.id} created by {request.user.email}")
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         logger.warning(f"Test creation failed for {request.user.email}: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class TestUpdateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [TokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def patch(self, request, test_id):
#         if not request.user.is_active:
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
#         try:
#             test = Test.objects.get(id=test_id, creator=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {test_id} not found for {request.user.email}")
#             return Response({"error": "Test not found or not owned"}, status=status.HTTP_404_NOT_FOUND)
        
#         # Prevent editing if test started
#         if test.schedule_start <= timezone.now():
#             logger.warning(f"Attempt to edit started test {test_id} by {request.user.email}")
#             return Response({"error": "Cannot edit test that has started"}, status=status.HTTP_400_BAD_REQUEST)
        
#         serializer = TestSerializer(test, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             send_test_notification_task.delay(
#                 test.id, request.user.email, action="updated"
#             )
#             logger.info(f"Test {test.id} updated by {request.user.email}")
#             return Response(serializer.data)
#         logger.warning(f"Test update failed for {request.user.email}: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class TestDeleteView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [TokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def delete(self, request, test_id):
#         if not request.user.is_active:
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
#         try:
#             test = Test.objects.get(id=test_id, creator=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {test_id} not found for {request.user.email}")
#             return Response({"error": "Test not found or not owned"}, status=status.HTTP_404_NOT_FOUND)
        
#         # Prevent deletion if test has attempts
#         if test.testattempt_set.exists():
#             logger.warning(f"Attempt to delete test {test_id} with attempts by {request.user.email}")
#             return Response({"error": "Cannot delete test with attempts"}, status=status.HTTP_400_BAD_REQUEST)
        
#         test.delete()
#         send_test_notification_task.delay(
#             test_id, request.user.email, action="deleted"
#         )
#         logger.info(f"Test {test_id} deleted by {request.user.email}")
#         return Response({"message": "Test deleted"}, status=status.HTTP_200_OK)

# class TestListView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [TokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         if not request.user.is_active:
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
#         queryset = Test.objects.filter(creator=request.user).select_related('creator').prefetch_related('subjects')
#         # Filters
#         subject_id = request.query_params.get('subject')
#         active = request.query_params.get('active')
        
#         if subject_id:
#             queryset = queryset.filter(subjects__id=subject_id)
#         if active is not None:
#             now = timezone.now()
#             if bool(active):
#                 queryset = queryset.filter(schedule_start__lte=now, schedule_end__gte=now)
#             else:
#                 queryset = queryset.exclude(schedule_start__lte=now, schedule_end__gte=now)
        
#         # Pagination
#         paginator = Paginator(queryset, 20)
#         page = request.query_params.get('page', 1)
#         try:
#             tests = paginator.page(page)
#         except EmptyPage:
#             return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
        
#         serializer = TestSerializer(tests, many=True)
#         logger.info(f"Test list retrieved by {request.user.email}")
#         return Response({
#             "count": paginator.count,
#             "results": serializer.data
#         })