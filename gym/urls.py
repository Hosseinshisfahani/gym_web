from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .admin import admin_site
from . import views

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
    path('accept-agreement/', views.accept_agreement, name='accept_agreement'),
    path('workout-plans/', views.workout_plans, name='workout_plans'),
    path('workout-plans/add/', views.add_workout_plan, name='add_workout_plan'),
    path('workout-plans/add/<int:user_id>/', views.add_workout_plan, name='add_workout_plan_for_user'),
    path('workout-plans/<int:plan_id>/download/', views.download_workout_plan, name='download_workout_plan'),
    path('diet-plans/', views.diet_plans, name='diet_plans'),
    path('diet-plans/add/', views.add_diet_plan, name='add_diet_plan'),
    path('diet-plans/add/<int:user_id>/', views.add_diet_plan, name='add_diet_plan_for_user'),
    path('diet-plans/<int:plan_id>/download/', views.download_diet_plan, name='download_diet_plan'),
    path('request-plan/', views.request_plan, name='request_plan'),
    path('certificates/', views.certificates, name='certificates'),
    path('certificates/add/', views.add_certificate, name='add_certificate'),
    path('certificates/<int:certificate_id>/comment/', views.add_certificate_comment, name='add_certificate_comment'),
    path('certificates/manage/', views.manage_certificates, name='manage_certificates'),
    path('certificates/<int:certificate_id>/update-status/', views.update_certificate_status, name='update_certificate_status'),
    path('attendance/', views.attendance, name='attendance'),
    path('payments/', views.payments, name='payments'),
    path('payments/add/', views.add_payment, name='add_payment'),
    path('tickets/', views.tickets, name='tickets'),
    path('tickets/add/', views.add_ticket, name='add_ticket'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/update-status/', views.update_ticket_status, name='update_ticket_status'),
    path('documents/', views.documents, name='documents'),
    path('documents/add/', views.add_document, name='add_document'),
    path('documents/<int:doc_id>/view/', views.view_document, name='view_document'),
    path('staff/users/', views.admin_user_management, name='admin_user_management'),
    path('staff/attendance/', views.attendance_management, name='attendance_management'),
    path('staff/plans/', views.admin_plans, name='admin_plans'),
    path('staff/plan-requests/', views.manage_plan_requests, name='manage_plan_requests'),
    path('staff/plan-requests/<int:request_id>/update/', views.update_plan_request, name='update_plan_request'),
    # Booklets URLs
    path('booklets/', views.booklets, name='booklets'),
    path('booklets/<int:booklet_id>/', views.booklet_detail, name='booklet_detail'),
    path('booklets/<int:booklet_id>/edit/', views.edit_booklet, name='edit_booklet'),
    path('booklets/<int:booklet_id>/payments/', views.booklet_payments, name='booklet_payments'),
    path('booklets/payments/<int:payment_id>/update/', views.update_payment_status, name='update_payment_status'),
    path('booklets/<int:product_id>/pay/', views.payment_upload, name='payment_upload'),
    path('booklets/<int:booklet_id>/view/', views.view_pdf, name='view_pdf'),
    path('booklets/<int:booklet_id>/stream/', views.stream_pdf, name='stream_pdf'),
    path('booklets/log-screenshot/', views.log_screenshot_attempt, name='log_screenshot_attempt'),
    path('booklets/feedback/', views.submit_feedback, name='submit_feedback'),
    # User search API
    path('api/search-users/', views.search_users, name='search_users'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 