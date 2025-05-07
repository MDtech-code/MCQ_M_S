from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, StudentProfile, TeacherProfile, ApprovalRequest
from .tasks import send_teacher_approval_email_task

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    raw_id_fields = ['user']
    extra = 0
    can_delete = False
    verbose_name_plural = _('Student Profile')
    fk_name = 'user'

class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    raw_id_fields = ['user']
    extra = 0
    can_delete = False
    verbose_name_plural = _('Teacher Profile')
    fk_name = 'user'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id','username', 'email', 'role', 'is_verified', 'is_approved', 'is_staff')
    list_filter = ('role', 'is_verified', 'is_approved', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('email', 'first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_approved', 'groups', 'user_permissions')
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Role Info'), {'fields': ('role', 'is_verified')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2', 'is_approved'),
        }),
    )
    actions = ['approve_teachers', 'reject_teachers']

    def get_inline_instances(self, request, obj=None):
        if obj and obj.role == User.Role.ADMIN:
            return []
        inline_instances = []
        if obj:
            if obj.role == User.Role.STUDENT:
                inline_instances.append(StudentProfileInline(self.model, self.admin_site))
            elif obj.role == User.Role.TEACHER:
                inline_instances.append(TeacherProfileInline(self.model, self.admin_site))
        return inline_instances

    

@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status','qualifications', 'created_at', 'document_link')

    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email','qualifications')
    actions = ['approve_requests', 'reject_requests']

    
    def get_readonly_fields(self, request, obj=None):
        """Make status read-only **only** in the form, but allow changes via actions."""
        if obj:  # If an object exists, prevent manual status changes in the form
            return ('status',)
        return ()





    def document_link(self, obj):
        if obj.document:
            return f'<a href="{obj.document.url}" target="_blank">Download</a>'
        return "No document"
    document_link.allow_tags = True
    document_link.short_description = "Document"

    def approve_requests(self, request, queryset):
        count = 0
        for req in queryset.filter(status=ApprovalRequest.Status.PENDING):
            req.user.is_approved = True
            req.user.is_active = True
            req.user.save()
            req.status = ApprovalRequest.Status.APPROVED
            req.save()
            send_teacher_approval_email_task.delay(req.user.id, approved=True)
            count += 1
        self.message_user(request, f"{count} request(s) approved successfully.")
    approve_requests.short_description = "Approve selected requests"

    def reject_requests(self, request, queryset):
        count = 0
        for req in queryset.filter(status=ApprovalRequest.Status.PENDING):
            req.status = ApprovalRequest.Status.REJECTED
            req.rejection_reason = "Rejected by admin"
            req.save()
            send_teacher_approval_email_task.delay(req.user.id, approved=False)
            count += 1
        self.message_user(request, f"{count} request(s) rejected successfully.")
    reject_requests.short_description = "Reject selected requests"
