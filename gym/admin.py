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
        
        # Sort the apps alphabetically
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())
        
        return app_list

# Create an instance of our custom admin site
admin_site = CustomAdminSite(name='admin')

from .models import (
    UserProfile, WorkoutPlan, DietPlan, 
    Payment, Ticket, TicketResponse, Document, PlanRequest
)

class UserProfileAdmin(admin.ModelAdmin):
    verbose_name = 'پروفایل کاربر'
    verbose_name_plural = 'پروفایل‌های کاربران'
    list_display = ('name', 'phone_number')
    search_fields = ('user__username', 'phone_number', 'melli_code', 'name')
    ordering = ('name',)

    def __str__(self):
        return f"{self.name} ({self.melli_code})"

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

class PlanRequestAdmin(admin.ModelAdmin):
    verbose_name = 'درخواست برنامه'
    verbose_name_plural = 'درخواست‌های برنامه'
    list_display = ('user', 'plan_type', 'status', 'created_at')
    list_filter = ('plan_type', 'status', 'created_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)

# Register all models with the custom Persian admin site
admin_site.register(UserProfile, UserProfileAdmin)
admin_site.register(WorkoutPlan, WorkoutPlanAdmin)
admin_site.register(DietPlan, DietPlanAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(Ticket, TicketAdmin)
admin_site.register(TicketResponse, TicketResponseAdmin)
admin_site.register(Document, DocumentAdmin)
admin_site.register(PlanRequest, PlanRequestAdmin)
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
