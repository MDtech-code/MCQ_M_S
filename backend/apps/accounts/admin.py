from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, StudentProfile, TeacherProfile


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
    list_display = ('username', 'email', 'role', 'is_verified', 'is_staff')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    # Updated select_related field names
    list_select_related = ('studentprofile', 'teacherprofile')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('email',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Role Info'), {'fields': ('role', 'is_verified')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
    )
    
    def get_inline_instances(self, request, obj=None):
        """
        Dynamically add inlines based on user role, excluding inlines for ADMIN role.
        """
        if obj and obj.role == User.Role.ADMIN:
            return []  # No inlines for ADMIN role

        inline_instances = []
        if obj:
            if obj.role == User.Role.STUDENT:
                inline_instances.append(StudentProfileInline(self.model, self.admin_site))
            elif obj.role == User.Role.TEACHER:
                inline_instances.append(TeacherProfileInline(self.model, self.admin_site))

        return inline_instances

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'grade_level', 'parent_email', 'enrolled_date')
    search_fields = ('user__username', 'user__email', 'grade_level')
    ordering = ('-enrolled_date',)
    
    def has_add_permission(self, request):
        return False

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'office_number', 'hire_date')
    search_fields = ('user__username', 'user__email', 'department')
    ordering = ('-hire_date',)
    
    def has_add_permission(self, request):
        return False
