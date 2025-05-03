from django.contrib import admin
from .models import StudentProgress, TestAnalytics, TestAttemptHistory

@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'total_attempts', 'average_score', 'last_updated')
    list_filter = ('subject', 'last_updated')
    search_fields = ('student__email', 'subject__name')
    readonly_fields = ('last_updated',)

@admin.register(TestAnalytics)
class TestAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('test', 'average_score')
    list_filter = ('test__created_by',)
    search_fields = ('test__title',)

@admin.register(TestAttemptHistory)
class TestAttemptHistoryAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'score', 'completed_at', 'duration')
    list_filter = ('completed_at', 'test__subjects')
    search_fields = ('student__email', 'test__title')
    readonly_fields = ('completed_at',)