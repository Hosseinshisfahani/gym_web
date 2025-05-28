from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import AdminSite
from django.contrib.admin import ModelAdmin
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

# The User and Group models are already registered with the default admin site by Django
# so we don't need to register them explicitly

class CustomAdminSite(AdminSite):
    site_header = _('پنل مدیریت')
    site_title = _('پنل مدیریت')
    index_title = _('پنل مدیریت')

    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_dict = self._build_app_dict(request)
        
        # Define the desired order of apps
        app_order = ['gym']
        
        # Define the desired order of models within each app
        model_order = {
            'scores': [
                'school',      # مدارس
                'grade',       # پایه‌های تحصیلی
                'subject',     # درس‌ها
                'class',       # کلاس‌ها
                'studentscore', # نمرات دانش‌آموزان
                'score',       # نمرات
            ],
            'exams': [
                'exam',         # آزمون‌ها
                'question',     # سوالات
                'examregistration', # ثبت‌نام‌های آزمون
                'useranswer',   # پاسخ‌های کاربران
            ]
        }
        
        # Sort apps according to app_order
        app_list = []
        for app_label in app_order:
            if app_label in app_dict:
                app = app_dict[app_label]
                # Sort models within the app
                if app_label in model_order:
                    app['models'].sort(
                        key=lambda x: model_order[app_label].index(x['object_name'].lower())
                        if x['object_name'].lower() in model_order[app_label]
                        else len(model_order[app_label])
                    )
                app_list.append(app)
        
        return app_list

# Create an instance of our custom admin site
admin_site = CustomAdminSite(name='admin')

from .models import (
    UserProfile, WorkoutPlan, DietPlan, Certificate,
    Attendance, Payment, Ticket, TicketResponse, Document,
    CertificateComment
)

class UserProfileAdmin(admin.ModelAdmin):
    verbose_name = 'پروفایل کاربر'
    verbose_name_plural = 'پروفایل‌های کاربران'
    list_display = ('melli_code', 'full_name', 'phone_number')
    search_fields = ('user__username', 'phone_number', 'melli_code', 'full_name')
    ordering = ('full_name',)

    def __str__(self):
        return f"{self.full_name} ({self.melli_code})"

class WorkoutPlanAdmin(admin.ModelAdmin):
    verbose_name = 'برنامه تمرینی'
    verbose_name_plural = 'برنامه‌های تمرینی'
    list_display = ('user', 'title', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'user')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at',)
    list_editable = ('is_active',)
    def has_add_permission(self, request):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

class DietPlanAdmin(admin.ModelAdmin):
    verbose_name = 'برنامه غذایی'
    verbose_name_plural = 'برنامه‌های غذایی'
    list_display = ('user', 'title', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'user')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at',)
    list_editable = ('is_active',)
    def has_add_permission(self, request):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

class CertificateAdmin(admin.ModelAdmin):
    verbose_name = 'گواهی'
    verbose_name_plural = 'گواهی‌ها'
    list_display = ('get_user_full_name', 'title', 'status', 'issue_date', 'created_at', 'get_image_preview')
    list_filter = ('status', 'created_at', 'issue_date')
    search_fields = ('title', 'description', 'user__username', 'user__userprofile__full_name', 'user__userprofile__melli_code')
    readonly_fields = ('created_at', 'updated_at', 'get_image_display')
    list_editable = ('status',)
    ordering = ('-created_at',)
    list_per_page = 20
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'get_user_details')
        }),
        ('اطلاعات گواهی', {
            'fields': ('title', 'description', 'issue_date', 'status', 'get_image_display')
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('پیام‌ها', {
            'fields': ('approval_message',),
        }),
    )

    def get_user_full_name(self, obj):
        return obj.user.userprofile.full_name if hasattr(obj.user, 'userprofile') else obj.user.username
    get_user_full_name.short_description = 'نام کاربر'
    get_user_full_name.admin_order_field = 'user__userprofile__full_name'

    def get_user_details(self, obj):
        if hasattr(obj.user, 'userprofile'):
            profile = obj.user.userprofile
            return f"""
            <div style="margin: 10px 0;">
                <strong>نام کامل:</strong> {profile.full_name}<br>
                <strong>کد ملی:</strong> {profile.melli_code}<br>
                <strong>شماره تماس:</strong> {profile.phone_number or 'ثبت نشده'}<br>
                <strong>نام پدر:</strong> {profile.father_name or 'ثبت نشده'}<br>
            </div>
            """
        return "پروفایل کاربر موجود نیست"
    get_user_details.short_description = 'اطلاعات کاربر'
    get_user_details.allow_tags = True

    def get_image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 50px; max-width: 100px;" />'
        return 'بدون تصویر'
    get_image_preview.short_description = 'تصویر'
    get_image_preview.allow_tags = True

    def get_image_display(self, obj):
        if obj.image:
            return f'<a href="{obj.image.url}" target="_blank"><img src="{obj.image.url}" style="max-height: 300px; max-width: 100%;" /></a>'
        return 'بدون تصویر'
    get_image_display.short_description = 'تصویر گواهی'
    get_image_display.allow_tags = True

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == 'approved':
                messages.success(request, f'گواهی "{obj.title}" با موفقیت تایید شد.')
            elif obj.status == 'rejected':
                messages.error(request, f'گواهی "{obj.title}" رد شد.')
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    class Media:
        css = {
            'all': ('admin/css/custom.css',)
        }

class CertificateCommentAdmin(admin.ModelAdmin):
    verbose_name = 'نظر گواهی'
    verbose_name_plural = 'نظرات گواهی'
    list_display = ('certificate', 'user', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('message', 'user__username', 'certificate__title')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'date', 'present', 'description')
    list_filter = ('present', 'date')
    search_fields = ('user_profile__full_name', 'user_profile__melli_code')
    date_hierarchy = 'date'
    ordering = ('-date',)

class PaymentAdmin(admin.ModelAdmin):
    verbose_name = 'پرداخت'
    verbose_name_plural = 'پرداخت‌ها'
    list_display = ('user', 'amount', 'date', 'status')
    search_fields = ('user__username',)
    list_filter = ('date', 'status')

class TicketAdmin(admin.ModelAdmin):
    verbose_name = 'تیکت'
    verbose_name_plural = 'تیکت‌ها'
    list_display = ('user', 'subject', 'created_at', 'resolved')
    search_fields = ('user__username', 'subject')
    list_filter = ('created_at', 'resolved')

class TicketResponseAdmin(admin.ModelAdmin):
    verbose_name = 'پاسخ تیکت'
    verbose_name_plural = 'پاسخ‌های تیکت'
    list_display = ('ticket', 'user', 'created_at')
    search_fields = ('ticket__subject', 'user__username')
    list_filter = ('created_at',)

class DocumentAdmin(admin.ModelAdmin):
    verbose_name = 'مدرک'
    verbose_name_plural = 'مدارک'
    list_display = ('user', 'title', 'upload_date', 'is_paid')
    search_fields = ('user__username', 'title')
    list_filter = ('upload_date', 'is_paid')

# Register all models with the custom Persian admin site
admin_site.register(UserProfile, UserProfileAdmin)
admin_site.register(WorkoutPlan, WorkoutPlanAdmin)
admin_site.register(DietPlan, DietPlanAdmin)
admin_site.register(Certificate, CertificateAdmin)
admin_site.register(CertificateComment, CertificateCommentAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(Ticket, TicketAdmin)
admin_site.register(TicketResponse, TicketResponseAdmin)
admin_site.register(Document, DocumentAdmin)

# Register the models with the default Django admin site too
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(WorkoutPlan, WorkoutPlanAdmin)
admin.site.register(DietPlan, DietPlanAdmin)
admin.site.register(Certificate, CertificateAdmin)
admin.site.register(CertificateComment, CertificateCommentAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketResponse, TicketResponseAdmin)
admin.site.register(Document, DocumentAdmin)
