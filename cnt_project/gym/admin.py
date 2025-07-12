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
    Payment, Ticket, TicketResponse, Document, PlanRequest,
    BodyAnalysisReport, MonthlyGoal, ProgressAnalysis, BodyInformationUser, PaymentCard, EmailNotificationSettings
)

# Import shop models
from gym_shop.models import Category, Product, ProductImage, Cart, CartItem, Order, OrderItem

class UserProfileAdmin(admin.ModelAdmin):
    verbose_name = 'پروفایل کاربر'
    verbose_name_plural = 'پروفایل‌های کاربران'
    list_display = ('name', 'phone_number', 'is_vip', 'user')
    search_fields = ('user__username', 'phone_number', 'melli_code', 'name')
    ordering = ('name',)
    list_filter = ('is_vip', 'agreement_accepted')
    list_editable = ('is_vip',)

    def __str__(self):
        return f"{self.name} ({self.melli_code})"

class WorkoutPlanAdmin(admin.ModelAdmin):
    verbose_name = 'برنامه تمرینی'
    verbose_name_plural = 'برنامه‌های تمرینی'
    list_display = ('title', 'user', 'created_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'user__username', 'user__userprofile__name')
    ordering = ('-created_at',)

class DietPlanAdmin(admin.ModelAdmin):
    verbose_name = 'برنامه غذایی'
    verbose_name_plural = 'برنامه‌های غذایی'
    list_display = ('title', 'user', 'created_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'user__username', 'user__userprofile__name')
    ordering = ('-created_at',)

class PaymentAdmin(admin.ModelAdmin):
    verbose_name = 'پرداخت'
    verbose_name_plural = 'پرداخت‌ها'
    list_display = ('user', 'amount', 'payment_type', 'payment_date', 'status')
    list_filter = ('status', 'payment_type')
    search_fields = ('user__username', 'user__userprofile__name', 'description')
    ordering = ('-payment_date',)

class TicketAdmin(admin.ModelAdmin):
    verbose_name = 'تیکت'
    verbose_name_plural = 'تیکت‌ها'
    list_display = ('subject', 'user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('subject', 'user__username', 'user__userprofile__name')
    ordering = ('-created_at',)

class TicketResponseAdmin(admin.ModelAdmin):
    verbose_name = 'پاسخ تیکت'
    verbose_name_plural = 'پاسخ‌های تیکت'
    list_display = ('ticket', 'user', 'created_at', 'is_staff')
    list_filter = ('is_staff',)
    search_fields = ('ticket__subject', 'user__username', 'message')
    ordering = ('-created_at',)

class DocumentAdmin(admin.ModelAdmin):
    verbose_name = 'مدرک'
    verbose_name_plural = 'مدارک'
    list_display = ('title', 'user', 'document_type', 'upload_date')
    list_filter = ('document_type',)
    search_fields = ('title', 'user__username', 'user__userprofile__name')
    ordering = ('-upload_date',)

class PlanRequestAdmin(admin.ModelAdmin):
    verbose_name = 'درخواست برنامه'
    verbose_name_plural = 'درخواست‌های برنامه'
    list_display = ('user', 'plan_type', 'status', 'created_at')
    list_filter = ('status', 'plan_type')
    search_fields = ('user__username', 'user__userprofile__name', 'description')
    ordering = ('-created_at',)

# Admin classes for new models
class BodyAnalysisReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'report_date', 'status', 'response_date')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__userprofile__name', 'description', 'admin_response')
    ordering = ('-report_date',)

class MonthlyGoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'start_date', 'end_date', 'status', 'progress')
    list_filter = ('status',)
    search_fields = ('title', 'user__username', 'user__userprofile__name', 'description')
    ordering = ('-start_date',)

class ProgressAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'measurement_type', 'value', 'unit', 'measurement_date')
    list_filter = ('measurement_type',)
    search_fields = ('user__username', 'user__userprofile__name', 'notes')
    ordering = ('-measurement_date',)

class BodyInformationUserAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'birth_date', 'gender', 'height_cm', 'weight_kg', 'disease_history')
    search_fields = ('user_profile__name', 'user_profile__user__username')

class EmailNotificationSettingsAdmin(admin.ModelAdmin):
    verbose_name = 'تنظیمات اطلاع‌رسانی ایمیل'
    verbose_name_plural = 'تنظیمات اطلاع‌رسانی ایمیل'
    list_display = ('admin_user', 'notification_email', 'is_active', 'notification_frequency', 'notify_shop_orders', 'notify_workout_plan_requests', 'notify_diet_plan_requests')
    list_filter = ('is_active', 'notification_frequency', 'notify_shop_orders', 'notify_workout_plan_requests', 'notify_diet_plan_requests')
    search_fields = ('admin_user__username', 'notification_email')
    ordering = ('-created_at',)
    list_editable = ('is_active', 'notification_frequency')
    
    fieldsets = (
        ('تنظیمات کلی', {
            'fields': ('admin_user', 'notification_email', 'is_active', 'notification_frequency')
        }),
        ('اطلاع‌رسانی فروشگاه', {
            'fields': ('notify_shop_orders', 'notify_shop_order_status_change')
        }),
        ('اطلاع‌رسانی برنامه‌ها', {
            'fields': ('notify_workout_plan_requests', 'notify_diet_plan_requests')
        }),
        ('سایر اطلاع‌رسانی‌ها', {
            'fields': ('notify_new_user_registration', 'notify_payment_uploads')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('admin_user')
    
    def save_model(self, request, obj, form, change):
        # Auto-create notification settings for the current admin if they don't exist
        if not change and not obj.notification_email and request.user.email:
            obj.notification_email = request.user.email
        super().save_model(request, obj, form, change)

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
admin_site.register(BodyAnalysisReport, BodyAnalysisReportAdmin)
admin_site.register(MonthlyGoal, MonthlyGoalAdmin)
admin_site.register(ProgressAnalysis, ProgressAnalysisAdmin)
admin_site.register(BodyInformationUser, BodyInformationUserAdmin)
admin_site.register(EmailNotificationSettings, EmailNotificationSettingsAdmin)

# Import and register shop admin classes
from gym_shop.admin import CategoryAdmin, ProductAdmin, CartAdmin, OrderAdmin, ProductImageAdmin
admin_site.register(Category, CategoryAdmin)
admin_site.register(Product, ProductAdmin)
admin_site.register(Cart, CartAdmin)
admin_site.register(Order, OrderAdmin)
admin_site.register(ProductImage, ProductImageAdmin)

class PaymentCardAdmin(admin.ModelAdmin):
    verbose_name = 'کارت پرداخت'
    verbose_name_plural = 'کارت‌های پرداخت'
    list_display = ['card_holder_name', 'get_formatted_card_number', 'price_workout', 'price_diet', 'price_both', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['card_holder_name', 'card_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = [
        ('اطلاعات کارت', {
            'fields': ['card_number', 'card_holder_name', 'is_active'],
            'description': 'شماره کارت باید 16 رقم باشد'
        }),
        ('قیمت‌گذاری (تومان)', {
            'fields': ['price_workout', 'price_diet', 'price_both'],
            'description': 'قیمت‌ها به تومان وارد شوند'
        }),
        ('تاریخ‌ها', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

admin_site.register(PaymentCard, PaymentCardAdmin)
