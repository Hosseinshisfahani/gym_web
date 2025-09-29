from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import AdminSite
from django.contrib.admin import ModelAdmin
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.utils import timezone

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
    BodyAnalysisReport, InBodyReport, MonthlyGoal, ProgressAnalysis, BodyInformationUser, PaymentCard, EmailNotificationSettings, TuitionCategory, TuitionReceipt, SpecialTuitionFee,
    BlogCategory, BlogPost, BlogComment
)

# Import shop models
from gym_shop.models import Category, Product, ProductImage, Cart, CartItem, Order, OrderItem

class UserProfileAdmin(admin.ModelAdmin):
    verbose_name = 'پروفایل کاربر'
    verbose_name_plural = 'پروفایل‌های کاربران'
    list_display = ('name', 'phone_number', 'birth_date', 'is_vip', 'user')
    search_fields = ('user__username', 'phone_number', 'melli_code', 'name')
    ordering = ('name',)
    list_filter = ('is_vip', 'agreement_accepted', 'birth_date')
    list_editable = ('is_vip',)

    def __str__(self):
        return f"{self.name} ({self.melli_code})"

class WorkoutPlanAdmin(admin.ModelAdmin):
    verbose_name = 'برنامه تمرینی'
    verbose_name_plural = 'برنامه‌های تمرینی'
    list_display = ('plan_type', 'user', 'created_at', 'is_active')
    list_filter = ('is_active', 'plan_type')
    search_fields = ('user__username', 'user__userprofile__name')
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

class InBodyReportAdmin(admin.ModelAdmin):
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
admin_site.register(InBodyReport, InBodyReportAdmin)
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
    list_display = ['card_holder_name', 'bank_name', 'get_formatted_card_number', 'price_workout', 'price_diet', 'price_both', 'is_active', 'created_at']
    list_filter = ['is_active', 'bank_name', 'created_at']
    search_fields = ['card_holder_name', 'card_number', 'bank_name', 'account_number', 'iban']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = [
        ('اطلاعات کارت', {
            'fields': ['card_number', 'card_holder_name', 'bank_name', 'is_active'],
            'description': 'شماره کارت باید 16 رقم باشد'
        }),
        ('اطلاعات بانکی', {
            'fields': ['account_number', 'iban'],
            'description': 'شماره حساب و شبا برای پرداخت دستی'
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

# Google OAuth Admin Configuration
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken
from allauth.account.models import EmailAddress

# Register Site model for allauth
admin_site.register(Site)

# Register SocialApp for Google OAuth configuration
class SocialAppAdmin(admin.ModelAdmin):
    list_display = ('provider', 'name', 'client_id')
    list_filter = ('provider',)
    search_fields = ('name', 'client_id')

admin_site.register(SocialApp, SocialAppAdmin)

# Register SocialAccount for managing user social accounts
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'uid', 'date_joined')
    list_filter = ('provider', 'date_joined')
    search_fields = ('user__email', 'user__username', 'uid')
    readonly_fields = ('date_joined', 'last_login')

admin_site.register(SocialAccount, SocialAccountAdmin)

# Register SocialToken for managing OAuth tokens
class SocialTokenAdmin(admin.ModelAdmin):
    list_display = ('account', 'token', 'expires_at')
    list_filter = ('expires_at',)
    search_fields = ('account__user__email', 'account__user__username')
    readonly_fields = ('token', 'token_secret', 'expires_at')

admin_site.register(SocialToken, SocialTokenAdmin)

# Register EmailAddress for email verification
class EmailAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'primary', 'verified')
    list_filter = ('primary', 'verified')
    search_fields = ('user__email', 'user__username', 'email')

admin_site.register(EmailAddress, EmailAddressAdmin)

# Tuition System Admin Classes
class TuitionCategoryAdmin(admin.ModelAdmin):
    verbose_name = 'دسته‌بندی شهریه'
    verbose_name_plural = 'دسته‌بندی‌های شهریه'
    list_display = ('name', 'amount', 'duration_months', 'is_active', 'created_at')
    list_filter = ('is_active', 'duration_months')
    search_fields = ('name', 'description')
    ordering = ('amount',)
    list_editable = ('is_active', 'amount', 'duration_months')
    
    fieldsets = [
        ('اطلاعات پایه', {
            'fields': ['name', 'description', 'is_active']
        }),
        ('مشخصات مالی', {
            'fields': ['amount', 'duration_months']
        }),
        ('تاریخ‌ها', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]
    readonly_fields = ('created_at',)

class TuitionReceiptAdmin(admin.ModelAdmin):
    verbose_name = 'رسید شهریه'
    verbose_name_plural = 'رسیدهای شهریه'
    list_display = ('get_athlete_name', 'category', 'amount_paid', 'payment_date', 'status', 'expiry_date', 'created_at')
    list_filter = ('status', 'category', 'payment_date', 'created_at')
    search_fields = ('athlete__username', 'athlete__userprofile__name', 'notes', 'admin_notes')
    ordering = ('-created_at',)
    list_editable = ('status',)
    readonly_fields = ('athlete', 'category', 'receipt_image', 'amount_paid', 'payment_date', 'notes', 'created_at', 'updated_at')
    
    fieldsets = [
        ('اطلاعات ورزشکار', {
            'fields': ['athlete', 'category']
        }),
        ('جزئیات پرداخت', {
            'fields': ['receipt_image', 'amount_paid', 'payment_date', 'expiry_date']
        }),
        ('وضعیت و بررسی', {
            'fields': ['status', 'notes', 'admin_notes', 'reviewed_by', 'reviewed_at']
        }),
        ('تاریخ‌ها', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_athlete_name(self, obj):
        """Display athlete name instead of username/melli_code"""
        try:
            if obj.athlete.userprofile.name:
                return f"{obj.athlete.userprofile.name} ({obj.athlete.username})"
            return obj.athlete.username
        except:
            return obj.athlete.username
    get_athlete_name.short_description = 'ورزشکار'
    get_athlete_name.admin_order_field = 'athlete__userprofile__name'

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('athlete', 'category', 'reviewed_by')

class SpecialTuitionFeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'amount', 'due_date', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at', 'due_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'title']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'created_by')

# Register tuition models
admin_site.register(TuitionCategory, TuitionCategoryAdmin)
admin_site.register(TuitionReceipt, TuitionReceiptAdmin)
admin_site.register(SpecialTuitionFee, SpecialTuitionFeeAdmin)

# Blog Admin Classes
class BlogCategoryAdmin(admin.ModelAdmin):
    verbose_name = 'دسته‌بندی بلاگ'
    verbose_name_plural = 'دسته‌بندی‌های بلاگ'
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_editable = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = [
        ('اطلاعات پایه', {
            'fields': ['name', 'slug', 'description', 'is_active']
        }),
        ('تاریخ‌ها', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]
    readonly_fields = ('created_at',)

class BlogPostAdmin(admin.ModelAdmin):
    verbose_name = 'مقاله بلاگ'
    verbose_name_plural = 'مقالات بلاگ'
    list_display = ('title', 'author', 'category', 'status', 'is_featured', 'view_count', 'published_at')
    list_filter = ('status', 'is_featured', 'category', 'created_at', 'published_at')
    search_fields = ('title', 'content', 'excerpt', 'author__username', 'author__userprofile__name')
    ordering = ('-published_at', '-created_at')
    list_editable = ('status', 'is_featured')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ()
    
    fieldsets = [
        ('اطلاعات اصلی', {
            'fields': ['title', 'slug', 'content', 'excerpt']
        }),
        ('تنظیمات', {
            'fields': ['author', 'category', 'status', 'is_featured', 'allow_comments']
        }),
        ('رسانه', {
            'fields': ['featured_image']
        }),
        ('آمار', {
            'fields': ['view_count'],
            'classes': ['collapse']
        }),
        ('تاریخ‌ها', {
            'fields': ['created_at', 'updated_at', 'published_at'],
            'classes': ['collapse']
        }),
    ]
    readonly_fields = ('created_at', 'updated_at', 'published_at', 'view_count')
    
    def save_model(self, request, obj, form, change):
        if not change:  # New post
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category')

class BlogCommentAdmin(admin.ModelAdmin):
    verbose_name = 'کامنت بلاگ'
    verbose_name_plural = 'کامنت‌های بلاگ'
    list_display = ('author_name', 'post', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('author_name', 'author_email', 'content', 'post__title')
    ordering = ('-created_at',)
    list_editable = ('status',)
    
    fieldsets = [
        ('اطلاعات کامنت', {
            'fields': ['post', 'author_name', 'author_email', 'content']
        }),
        ('وضعیت', {
            'fields': ['status']
        }),
        ('تاریخ‌ها', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post')

# Register blog models
admin_site.register(BlogCategory, BlogCategoryAdmin)
admin_site.register(BlogPost, BlogPostAdmin)
admin_site.register(BlogComment, BlogCommentAdmin)
