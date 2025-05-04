# apps/examination/admin.py
from django.contrib import admin
from .models import Test, TestAttempt, StudentResponse

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'created_by', 'duration', 'max_attempts', 'created_at')
    search_fields = ('title', 'created_by__email')
    list_filter = ( 'created_by', 'created_at')
    raw_id_fields = ('created_by', 'subject')
    

@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'start_time', 'end_time', 'score', 'created_at')
    search_fields = ('student__email', 'test__title')
    list_filter = ('start_time', 'test', 'student', 'created_at')
    raw_id_fields = ('student', 'test')
    ordering = ('-start_time',)

@admin.register(StudentResponse)
class StudentResponseAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_answer', 'is_correct', 'time_taken', 'created_at')
    search_fields = ('question__question_text', 'attempt__student__email')
    list_filter = ('is_correct', 'attempt__test', 'created_at')
    raw_id_fields = ('attempt', 'question')
    ordering = ('-created_at',)