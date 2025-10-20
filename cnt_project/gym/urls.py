from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .admin import admin_site
from . import views
from django.shortcuts import render

app_name = 'gym'

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset/success/', views.password_reset_success, name='password_reset_success'),
    path('profile/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('calendar-test/', views.calendar_test, name='calendar_test'),
    path('body-information/', views.body_information_form, name='body_information_form'),
    path('accept-agreement/', views.accept_agreement, name='accept_agreement'),
    path('verify-profile-for-payment/', views.verify_profile_for_payment, name='verify_profile_for_payment'),
    path('verify-profile-for-payment/<path:next_url>/', views.verify_profile_for_payment, name='verify_profile_for_payment_with_next'),
    path('workout-plans/', views.workout_plans, name='workout_plans'),
    path('workout-plans/add/', views.add_workout_plan, name='add_workout_plan'),
    path('workout-plans/add/<int:user_id>/', views.add_workout_plan, name='add_workout_plan_for_user'),
    path('workout-plans/<int:plan_id>/download/', views.download_workout_plan, name='download_workout_plan'),
    path('workout-plans/<int:plan_id>/delete/', views.delete_workout_plan, name='delete_workout_plan'),
    path('diet-plans/', views.diet_plans, name='diet_plans'),
    path('diet-plans/add/', views.add_diet_plan, name='add_diet_plan'),
    path('diet-plans/add/<int:user_id>/', views.add_diet_plan, name='add_diet_plan_for_user'),
    path('diet-plans/<int:plan_id>/download/', views.download_diet_plan, name='download_diet_plan'),
    path('diet-plans/<int:plan_id>/delete/', views.delete_diet_plan, name='delete_diet_plan'),
    path('payments/', views.payments, name='payments'),
    path('payments/add/', views.add_payment, name='add_payment'),
    path('payments/plan-request/', views.plan_request_payment, name='plan_request_payment'),
    path('payments/debug-plan-payment/', views.debug_plan_payment, name='debug_plan_payment'),
    path('payments/gateway-callback/', views.payment_gateway_callback, name='payment_gateway_callback'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('payment/gateway-status/', views.payment_gateway_status, name='payment_gateway_status'),
    path('tickets/', views.tickets, name='tickets'),
    path('tickets/add/', views.add_ticket, name='add_ticket'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/update-status/', views.update_ticket_status, name='update_ticket_status'),
    path('documents/', views.documents, name='documents'),
    path('documents/add/', views.add_document, name='add_document'),
    path('documents/<int:doc_id>/view/', views.view_document, name='view_document'),
    path('staff/users/', views.admin_user_management, name='admin_user_management'),
    
    # VIP Customers Management
    path('staff/vip-customers/', views.vip_customers, name='vip_customers'),
    path('staff/vip-customers/toggle/<int:user_id>/', views.toggle_vip_status, name='toggle_vip_status'),
    
    # Email Notifications
    path('staff/test-email-notifications/', views.test_email_notifications, name='test_email_notifications'),
    
    # Plan request management
    path('plan-requests/', views.manage_plan_requests, name='manage_plan_requests'),
    path('plan-requests/<int:request_id>/update/', views.update_plan_request, name='update_plan_request'),
    path('plan-requests/<int:request_id>/detail/', views.plan_request_management_detail, name='plan_request_management_detail'),
    path('plan-management/', views.comprehensive_plan_management, name='comprehensive_plan_management'),
    path('payments/<int:payment_id>/update-status/', views.update_payment_status, name='update_payment_status'),
    path('request-plan/', views.request_plan, name='request_plan'),
    path('plan-request-flow/', views.plan_request_flow, name='plan_request_flow'),
    path('plan-request-flow/<str:step>/', views.plan_request_flow, name='plan_request_flow'),
    
    # Body Analysis Reports
    path('body-analysis/', views.body_analysis_reports, name='body_analysis_reports'),
    path('body-analysis/<int:report_id>/', views.body_analysis_detail, name='body_analysis_detail'),
    path('inbody/<int:report_id>/', views.inbody_detail, name='inbody_detail'),
    
    # Monthly Goals
    path('monthly-goals/', views.monthly_goals, name='monthly_goals'),
    path('monthly-goals/<int:goal_id>/', views.monthly_goal_detail, name='monthly_goal_detail'),
    path('monthly-goals/add/', views.add_monthly_goal, name='add_monthly_goal'),
    path('monthly-goals/<int:goal_id>/edit/', views.edit_monthly_goal, name='edit_monthly_goal'),
    path('monthly-goals/<int:goal_id>/delete/', views.delete_monthly_goal, name='delete_monthly_goal'),
    path('api/user-measurements/<int:user_id>/', views.get_user_measurements, name='get_user_measurements'),
    
    # Progress Analysis
    path('progress/', views.progress_analysis, name='progress_analysis'),
    path('progress/delete/<int:entry_id>/', views.delete_progress_entry, name='delete_progress_entry'),
    path('progress/quick-add/', views.quick_add_measurement, name='quick_add_measurement'),
    
    # Placeholder routes for removed features
    path('attendance/', lambda request: render(request, 'gym/attendance.html'), name='attendance'),
    path('certificates/', lambda request: render(request, 'gym/certificates.html'), name='certificates'),
    path('booklets/', lambda request: render(request, 'gym/booklets.html'), name='booklets'),
    
    # Tuition System URLs
    path('tuition/', views.tuition_dashboard, name='tuition_dashboard'),
    path('tuition/upload/', views.upload_tuition_receipt, name='upload_tuition_receipt'),
    path('tuition/receipt/<int:receipt_id>/', views.tuition_receipt_detail, name='tuition_receipt_detail'),
    
    # Admin Tuition URLs
    path('staff/tuition/receipt/<int:receipt_id>/review/', views.review_tuition_receipt, name='review_tuition_receipt'),
    path('staff/tuition/receipt/<int:receipt_id>/quick-update/', views.quick_update_tuition_receipt, name='quick_update_tuition_receipt'),
    
    # Special Tuition Fee URLs (Integrated into main tuition dashboard)
    
    # API endpoints for special tuition fees
    path('api/users/', views.api_users, name='api_users'),
    path('api/special-fees/', views.api_special_fees, name='api_special_fees'),
    path('api/special-fees/create/', views.api_create_special_fee, name='api_create_special_fee'),
    path('api/special-fees/<int:fee_id>/delete/', views.api_delete_special_fee, name='api_delete_special_fee'),
    
    # Blog URLs
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    
    # Admin Blog URLs
    path('staff/blog/', views.blog_admin_list, name='blog_admin_list'),
    path('staff/blog/create/', views.blog_post_create, name='blog_post_create'),
    path('staff/blog/<int:pk>/edit/', views.blog_post_edit, name='blog_post_edit'),
    path('staff/blog/<int:pk>/delete/', views.blog_post_delete, name='blog_post_delete'),
    path('staff/blog/categories/', views.blog_category_list, name='blog_category_list'),
    path('staff/blog/categories/create/', views.blog_category_create, name='blog_category_create'),
    path('staff/blog/categories/<int:pk>/edit/', views.blog_category_edit, name='blog_category_edit'),
    path('staff/blog/comments/', views.blog_comment_list, name='blog_comment_list'),
    path('staff/blog/comments/<int:pk>/approve/', views.blog_comment_approve, name='blog_comment_approve'),
    path('staff/blog/comments/<int:pk>/reject/', views.blog_comment_reject, name='blog_comment_reject'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 