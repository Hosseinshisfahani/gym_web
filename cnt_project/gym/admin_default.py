from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from .models import (
    UserProfile, WorkoutPlan, DietPlan, 
    Payment, Ticket, TicketResponse, Document, PlanRequest
)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number')
    search_fields = ('user__username', 'phone_number', 'melli_code', 'name')
    ordering = ('name',)

class WorkoutPlanAdmin(admin.ModelAdmin):
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
    list_display = ('user', 'amount', 'date', 'status')
    search_fields = ('user__username',)
    list_filter = ('date', 'status')

class TicketAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'created_at', 'resolved')
    search_fields = ('user__username', 'subject')
    list_filter = ('created_at', 'resolved')

class TicketResponseAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'created_at')
    search_fields = ('ticket__subject', 'user__username')
    list_filter = ('created_at',)

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'upload_date', 'is_paid')
    search_fields = ('user__username', 'title')
    list_filter = ('upload_date', 'is_paid')

class PlanRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_type', 'status', 'created_at')
    list_filter = ('plan_type', 'status', 'created_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)

# Register all models with the default Django admin site
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(WorkoutPlan, WorkoutPlanAdmin)
admin.site.register(DietPlan, DietPlanAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketResponse, TicketResponseAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(PlanRequest, PlanRequestAdmin) 