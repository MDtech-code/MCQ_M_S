from django.utils import timezone
from django.contrib import admin
from .models import Subject, Topic, Question, QuestionApproval

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'description', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    ordering = ('name',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'subject', 'difficulty_level', 'created_at')
    search_fields = ('name', 'subject__name')
    list_filter = ('subject', 'difficulty_level', 'created_at')
    ordering = ('subject__name', 'name')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id','question_text_short', 'question_type', 'difficulty', 'is_active', 'created_by', 'created_at')
    search_fields = ('question_text', 'created_by__email')
    list_filter = ('question_type', 'difficulty', 'is_active', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'version')
    filter_horizontal = ('topics',)

    def question_text_short(self, obj):
        return obj.question_text[:50]
    question_text_short.short_description = 'Question Text'

    def save_model(self, request, obj, form, change):
        # Prevent direct is_active changes; use QuestionApproval
        if change and 'is_active' in form.changed_data:
            self.message_user(request, "Cannot change is_active directly. Use QuestionApproval.", level='error')
            return
        super().save_model(request, obj, form, change)

@admin.register(QuestionApproval)
class QuestionApprovalAdmin(admin.ModelAdmin):
    list_display = ('id','question', 'status', 'flagged_by_system', 'flag_reason', 'reviewed_by', 'reviewed_at')
    search_fields = ('question__question_text', 'flag_reason')
    list_filter = ('status', 'flagged_by_system', 'reviewed_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'flagged_by_system', 'flag_reason')

    def save_model(self, request, obj, form, change):
        if not change or obj.status != form.initial.get('status'):
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            if obj.status == 'APPROVED':
                obj.question.is_active = True
                obj.question.save()
            elif obj.status == 'REJECTED':
                obj.question.is_active = False
                obj.question.save()
        super().save_model(request, obj, form, change)