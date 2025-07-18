from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, FileResponse, StreamingHttpResponse, HttpResponseForbidden, JsonResponse
from .forms import (
    UserRegistrationForm, UserProfileForm, WorkoutPlanForm, 
    DietPlanForm, PaymentForm, TicketForm,
    TicketResponseForm, DocumentForm, PlanRequestForm,
    BodyAnalysisReportForm, BodyAnalysisResponseForm,
    MonthlyGoalForm, MonthlyGoalUpdateForm, MonthlyGoalCoachForm,
    ProgressAnalysisForm, BodyInformationUserForm
)
from .models import (
    UserProfile, WorkoutPlan, DietPlan, 
    Payment, Ticket, TicketResponse, Document, PlanRequest,
    BodyAnalysisReport, MonthlyGoal, ProgressAnalysis, BodyInformationUser, PaymentCard
)
from django.db.models import Q, Avg, Sum, Count
import datetime
import os
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
import json
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
from django.db.utils import IntegrityError
from django.db import transaction
import string
import random
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta

# Home view
def home(request):
    return render(request, 'gym/home.html')

# Authentication views
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Check if the user has agreed to the terms
            if 'agreement' not in request.POST:
                messages.error(request, 'شما باید با شرایط و قوانین موافقت کنید.')
                return render(request, 'gym/register.html', {'form': form})
                
            user = form.save()
            
            # Mark the agreement as accepted in the user profile
            profile = user.userprofile
            profile.agreement_accepted = True
            profile.save()
            
            login(request, user)
            messages.success(request, 'ثبت نام با موفقیت انجام شد.')
            return redirect('gym:profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'gym/register.html', {'form': form})

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        password = request.POST.get('password')
        
        # Try to find the user by their name in UserProfile
        try:
            profile = UserProfile.objects.get(name=name)
            # Get the associated User and authenticate with their username (which is now the name)
            authenticated_user = authenticate(request, username=profile.user.username, password=password)
            
            if authenticated_user is not None:
                login(request, authenticated_user)
                return redirect('gym:profile')
            else:
                messages.error(request, 'نام یا رمز عبور نامعتبر است.')
        except UserProfile.DoesNotExist:
            messages.error(request, 'کاربری با این نام یافت نشد.')
        except UserProfile.MultipleObjectsReturned:
            # In case there are multiple users with the same name (should not happen with our validation)
            messages.error(request, 'چندین کاربر با این نام وجود دارد. لطفاً با پشتیبانی تماس بگیرید.')
    
    return render(request, 'gym/login.html')

def logout_view(request):
    logout(request)
    return redirect('gym:home')

@login_required
def accept_agreement(request):
    if request.method == 'POST':
        # Get the user's profile
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Mark the agreement as accepted
        user_profile.agreement_accepted = True
        user_profile.save()
        
        messages.success(request, 'توافقنامه با موفقیت پذیرفته شد.')
        
        # Redirect back to the referring page or profile page
        return redirect(request.META.get('HTTP_REFERER', 'gym:profile'))
    
    # If not a POST request, redirect to profile
    return redirect('gym:profile')

# Profile views
@login_required
def profile(request, user_id=None):
    # If user_id is provided, get that user's profile
    if user_id:
        # Only staff members can view other users' profiles
        if not request.user.is_staff:
            messages.error(request, 'شما دسترسی لازم برای مشاهده پروفایل دیگران را ندارید.')
            return redirect('gym:profile')
        
        try:
            user = User.objects.get(id=user_id)
            user_profile = user.userprofile
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            messages.error(request, 'کاربر مورد نظر یافت نشد.')
            return redirect('gym:profile')
    else:
        # Get or create current user's profile
        try:
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # If profile was just created, set some default values
            if created:
                user_profile.save()
        except IntegrityError as e:
            if 'melli_code' in str(e):
                return render(request, 'gym/duplicate_melli_code.html')
            else:
                # If it's a different IntegrityError, re-raise it
                raise
    
    # Get counts for dashboard statistics
    if user_id:
        user = User.objects.get(id=user_id)
    else:
        user = request.user
    
    # Dashboard statistics
    stats = {
        'body_analysis_count': BodyAnalysisReport.objects.filter(user=user).count(),
        'body_analysis_pending': BodyAnalysisReport.objects.filter(user=user, status='pending').count(),
        'payment_count': Payment.objects.filter(user=user).count(),
        'payment_pending': Payment.objects.filter(user=user, status='pending').count(),
        'goals_count': MonthlyGoal.objects.filter(user=user).count(),
        'goals_active': MonthlyGoal.objects.filter(user=user).exclude(status__in=['completed', 'failed']).count(),
        'progress_entries': ProgressAnalysis.objects.filter(user=user).count(),
    }
    
    # VIP statistics and email notification settings for admin users
    vip_stats = None
    notification_settings = None
    if request.user.is_staff:
        vip_stats = {
            'total_users': UserProfile.objects.count(),
            'vip_users': UserProfile.objects.filter(is_vip=True).count(),
            'non_vip_users': UserProfile.objects.filter(is_vip=False).count(),
            'vip_percentage': round((UserProfile.objects.filter(is_vip=True).count() / UserProfile.objects.count()) * 100, 1) if UserProfile.objects.count() > 0 else 0,
        }
        
        # Get or create email notification settings for this admin
        try:
            from gym.models import EmailNotificationSettings
            notification_settings, created = EmailNotificationSettings.objects.get_or_create(
                admin_user=request.user,
                defaults={
                    'notification_email': request.user.email or 'admin@example.com',
                    'notify_shop_orders': True,
                    'notify_workout_plan_requests': True,
                    'notify_diet_plan_requests': True,
                    'notify_payment_uploads': True,
                    'notification_frequency': 'immediate',
                    'is_active': True,
                }
            )
        except Exception as e:
            # Log the error but don't break the page
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating notification settings: {str(e)}")
            notification_settings = None
    
    # Get most recent progress data for quick view
    recent_progress = ProgressAnalysis.objects.filter(user=user).order_by('-measurement_date')[:5]
    
    context = {
        'user_profile': user_profile,
        'is_own_profile': not user_id or user_id == request.user.id,
        'stats': stats,
        'recent_progress': recent_progress,
        'vip_stats': vip_stats,
        'notification_settings': notification_settings,
    }
    return render(request, 'gym/profile.html', context)

@login_required
def edit_profile(request):
    # Get or create user profile
    try:
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    except IntegrityError as e:
        if 'melli_code' in str(e):
            return render(request, 'gym/duplicate_melli_code.html')
        else:
            raise
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            try:
                # Start a transaction to ensure all updates happen or none
                with transaction.atomic():
                    # Save the profile data
                    profile = form.save()
                    
                    # Update user email if changed
                    email = form.cleaned_data.get('email')
                    if email and email != request.user.email:
                        request.user.email = email
                        request.user.save()
                    
                    # Update password if provided
                    password = form.cleaned_data.get('password')
                    if password:
                        request.user.set_password(password)
                        request.user.save()
                        
                        # Re-authenticate the user to prevent logout
                        update_session_auth_hash(request, request.user)
                
                messages.success(request, 'پروفایل شما با موفقیت به‌روزرسانی شد.')
                
                # Check if there's a redirect URL stored in the session for payment
                if 'payment_redirect_url' in request.session:
                    redirect_url = request.session.pop('payment_redirect_url')
                    redirect_step = request.session.pop('payment_redirect_step', None)
                    if redirect_step:
                        return redirect(redirect_url, step=redirect_step)
                    return redirect(redirect_url)
                
                # Check if there's a product ID stored for payment
                if 'payment_product_id' in request.session:
                    product_id = request.session.pop('payment_product_id')
                    return redirect('gym:payment_upload', product_id=product_id)
                
                return redirect('gym:profile')
            except IntegrityError as e:
                if 'melli_code' in str(e):
                    return render(request, 'gym/duplicate_melli_code.html')
                else:
                    messages.error(request, 'خطا در ذخیره اطلاعات. لطفا اطلاعات وارد شده را بررسی کنید.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = UserProfileForm(instance=user_profile)
    
    context = {
        'form': form,
        'user_profile': user_profile,
    }
    return render(request, 'gym/edit_profile.html', context)

# Workout plan views
@login_required
def workout_plans(request):
    # Admin view
    if request.user.is_staff:
        workout_plans = WorkoutPlan.objects.all().order_by('-created_at')
        plan_requests = PlanRequest.objects.filter(plan_type='workout').order_by('-created_at')
        
        # Get filter parameters
        user_id = request.GET.get('user_id')
        status = request.GET.get('status')
        search_query = request.GET.get('search', '')
        
        # Apply filters
        if user_id:
            workout_plans = workout_plans.filter(user_id=user_id)
            plan_requests = plan_requests.filter(user_id=user_id)
        
        if status:
            if status in ['active', 'inactive']:
                is_active = status == 'active'
                workout_plans = workout_plans.filter(is_active=is_active)
            elif status in ['pending', 'approved', 'rejected']:
                plan_requests = plan_requests.filter(status=status)
        
        if search_query:
            workout_plans = workout_plans.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__userprofile__name__icontains=search_query)
            )
            plan_requests = plan_requests.filter(
                Q(user__username__icontains=search_query) |
                Q(user__userprofile__name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        context = {
            'workout_plans': workout_plans,
            'plan_requests': plan_requests,
            'is_admin': True,
            'status_filter': status,
            'search_query': search_query,
            'selected_user_id': user_id
        }
        return render(request, 'gym/admin/workout_plans.html', context)
    
    # Regular user view
    else:
        workout_plans = WorkoutPlan.objects.filter(user=request.user, is_active=True)
        plan_requests = PlanRequest.objects.filter(user=request.user, plan_type='workout')
        
        context = {
            'workout_plans': workout_plans,
            'plan_requests': plan_requests,
        }
        return render(request, 'gym/workout_plans.html', context)

@login_required
def add_workout_plan(request, user_id=None):
    # Check if admin is creating plan for another user
    target_user = None
    
    if user_id and request.user.is_staff:
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'کاربر مورد نظر یافت نشد.')
            return redirect('gym:workout_plans')
    elif request.GET.get('user_id') and request.user.is_staff:
        try:
            target_user = User.objects.get(id=request.GET.get('user_id'))
        except User.DoesNotExist:
            messages.error(request, 'کاربر مورد نظر یافت نشد.')
            return redirect('gym:workout_plans')
    
    # Get plan request if it exists
    plan_request = None
    if target_user:
        plan_request = PlanRequest.objects.filter(
            user=target_user, 
            plan_type='workout',
            status='approved'
        ).order_by('-created_at').first()
    
    if request.method == 'POST':
        form = WorkoutPlanForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                plan = form.save(commit=False)
                
                # If admin is creating for another user specified in the form
                if not target_user and request.user.is_staff and 'user_id' in request.POST and request.POST['user_id']:
                    try:
                        selected_user_id = request.POST['user_id']
                        target_user = User.objects.get(id=selected_user_id)
                        plan.user = target_user
                        success_message = f'برنامه تمرینی برای {target_user.username} با موفقیت ایجاد شد!'
                    except User.DoesNotExist:
                        messages.error(request, 'کاربر مورد نظر یافت نشد.')
                        return redirect('gym:workout_plans')
                # If admin is creating for a user passed in URL
                elif target_user and request.user.is_staff:
                    plan.user = target_user
                    success_message = f'برنامه تمرینی برای {target_user.username} با موفقیت ایجاد شد!'
                # Normal user creating their own plan
                else:
                    plan.user = request.user
                    success_message = 'برنامه تمرینی با موفقیت ایجاد شد!'
                
                plan.save()
                
                # Mark the related request as completed if it exists
                if plan_request:
                    plan_request.status = 'completed'
                    plan_request.save()
                    
                messages.success(request, success_message)
                return redirect('gym:workout_plans')
                
            except Exception as e:
                messages.error(request, f'خطا در ذخیره برنامه: {str(e)}')
        else:
            # Handle form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    if field == 'image':
                        messages.error(request, 'لطفاً تصویر برنامه را انتخاب کنید. این فیلد ضروری است.')
                    else:
                        field_name = form.fields[field].label or field
                        messages.error(request, f'{field_name}: {error}')
    else:
        form = WorkoutPlanForm()
    
    # Get users for dropdown if admin and no target user
    users = []
    if request.user.is_staff and not target_user:
        users = User.objects.exclude(is_staff=True).order_by('username')
    
    context = {
        'form': form,
        'target_user': target_user,
        'plan_request': plan_request,
        'users': users
    }
    return render(request, 'gym/add_workout_plan.html', context)

@login_required
def download_workout_plan(request, plan_id):
    # Get the workout plan
    plan = get_object_or_404(WorkoutPlan, id=plan_id)
    
    # Check if user has access to this plan
    if plan.user != request.user and not plan.user.is_staff:
        messages.error(request, "شما دسترسی لازم برای دانلود این برنامه تمرینی را ندارید.")
        return redirect('gym:workout_plans')
    
    # Create a BytesIO buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object, using the BytesIO buffer as its "file"
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Always use Helvetica font - it's available on all systems
    p.setFont('Helvetica', 14)
    
    # Draw the title (no RTL support, but will still be readable)
    title = f"Workout Plan: {plan.title}"
    p.drawCentredString(300, 750, title)
    
    # Add creation date
    date_text = f"Created on: {plan.created_at.strftime('%Y/%m/%d')}"
    p.setFont('Helvetica', 10)
    p.drawString(50, 720, date_text)
    
    # Add description
    if plan.description:
        p.setFont('Helvetica', 12)
        description = plan.description
        
        # Split description into lines that fit on the page
        lines = []
        for line in description.split('\n'):
            if len(line) > 80:  # Rough estimate of characters that fit on a line
                chunks = [line[i:i+80] for i in range(0, len(line), 80)]
                lines.extend(chunks)
            else:
                lines.append(line)
        
        y_position = 680
        for line in lines:
            if y_position < 50:  # Start a new page if we're at the bottom
                p.showPage()
                p.setFont('Helvetica', 12)
                y_position = 750
            p.drawString(50, y_position, line)
            y_position -= 15
    
    # Add image if available
    if plan.image:
        try:
            img_path = plan.image.path
            img = Image.open(img_path)
            img_width, img_height = img.size
            
            # Scale down image if it's too large
            max_width = 500
            max_height = 400
            if img_width > max_width or img_height > max_height:
                ratio = min(max_width/img_width, max_height/img_height)
                img_width = int(img_width * ratio)
                img_height = int(img_height * ratio)
            
            # Start a new page for the image
            p.showPage()
            p.drawInlineImage(img_path, 50, 500, width=img_width, height=img_height)
        except Exception as e:
            print(f"Error adding image to PDF: {str(e)}")
    
    # Add footer with user info
    p.showPage()  # Start a new page for the footer
    p.setFont('Helvetica', 10)
    try:
        full_name = plan.user.userprofile.name if hasattr(plan.user, 'userprofile') else plan.user.username
    except UserProfile.DoesNotExist:
        full_name = plan.user.username
    footer = f"Created by: {full_name}"
    p.drawString(50, 30, footer)
    
    # Close the PDF object cleanly, and we're done
    p.save()
    
    # Get the value of the BytesIO buffer and write it to the response
    buffer.seek(0)
    
    # Create the response with PDF mime type
    filename = f"workout_plan_{plan.title}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# Diet plan views
@login_required
def diet_plans(request):
    # Admin view
    if request.user.is_staff:
        diet_plans = DietPlan.objects.all().order_by('-created_at')
        plan_requests = PlanRequest.objects.filter(plan_type='diet').order_by('-created_at')
        
        # Get filter parameters
        user_id = request.GET.get('user_id')
        status = request.GET.get('status')
        search_query = request.GET.get('search', '')
        
        # Apply filters
        if user_id:
            diet_plans = diet_plans.filter(user_id=user_id)
            plan_requests = plan_requests.filter(user_id=user_id)
        
        if status:
            if status in ['active', 'inactive']:
                is_active = status == 'active'
                diet_plans = diet_plans.filter(is_active=is_active)
            elif status in ['pending', 'approved', 'rejected']:
                plan_requests = plan_requests.filter(status=status)
        
        if search_query:
            diet_plans = diet_plans.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__userprofile__name__icontains=search_query)
            )
            plan_requests = plan_requests.filter(
                Q(user__username__icontains=search_query) |
                Q(user__userprofile__name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        context = {
            'diet_plans': diet_plans,
            'plan_requests': plan_requests,
            'is_admin': True,
            'status_filter': status,
            'search_query': search_query,
            'selected_user_id': user_id
        }
        return render(request, 'gym/admin/diet_plans.html', context)
    
    # Regular user view
    else:
        diet_plans = DietPlan.objects.filter(user=request.user, is_active=True)
        plan_requests = PlanRequest.objects.filter(user=request.user, plan_type='diet')
        
        context = {
            'diet_plans': diet_plans,
            'plan_requests': plan_requests,
        }
        return render(request, 'gym/diet_plans.html', context)

@login_required
def add_diet_plan(request, user_id=None):
    # Check if admin is creating plan for another user
    target_user = None
    
    if user_id and request.user.is_staff:
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'کاربر مورد نظر یافت نشد.')
            return redirect('gym:diet_plans')
    elif request.GET.get('user_id') and request.user.is_staff:
        try:
            target_user = User.objects.get(id=request.GET.get('user_id'))
        except User.DoesNotExist:
            messages.error(request, 'کاربر مورد نظر یافت نشد.')
            return redirect('gym:diet_plans')
    
    # Get plan request if it exists
    plan_request = None
    if target_user:
        plan_request = PlanRequest.objects.filter(
            user=target_user, 
            plan_type='diet',
            status='approved'
        ).order_by('-created_at').first()
    
    if request.method == 'POST':
        form = DietPlanForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                plan = form.save(commit=False)
                
                # If admin is creating for another user specified in the form
                if not target_user and request.user.is_staff and 'user_id' in request.POST and request.POST['user_id']:
                    try:
                        selected_user_id = request.POST['user_id']
                        target_user = User.objects.get(id=selected_user_id)
                        plan.user = target_user
                        success_message = f'برنامه غذایی برای {target_user.username} با موفقیت ایجاد شد!'
                    except User.DoesNotExist:
                        messages.error(request, 'کاربر مورد نظر یافت نشد.')
                        return redirect('gym:diet_plans')
                # If admin is creating for a user passed in URL
                elif target_user and request.user.is_staff:
                    plan.user = target_user
                    success_message = f'برنامه غذایی برای {target_user.username} با موفقیت ایجاد شد!'
                # Normal user creating their own plan
                else:
                    plan.user = request.user
                    success_message = 'برنامه غذایی با موفقیت ایجاد شد!'
                
                plan.save()
                
                # Mark the related request as completed if it exists
                if plan_request:
                    plan_request.status = 'completed'
                    plan_request.save()
                    
                messages.success(request, success_message)
                return redirect('gym:diet_plans')
                
            except Exception as e:
                messages.error(request, f'خطا در ذخیره برنامه: {str(e)}')
        else:
            # Handle form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    if field == 'image':
                        messages.error(request, 'لطفاً تصویر برنامه را انتخاب کنید. این فیلد ضروری است.')
                    else:
                        field_name = form.fields[field].label or field
                        messages.error(request, f'{field_name}: {error}')
    else:
        form = DietPlanForm()
    
    # Get users for dropdown if admin and no target user
    users = []
    if request.user.is_staff and not target_user:
        users = User.objects.exclude(is_staff=True).order_by('username')
    
    context = {
        'form': form,
        'target_user': target_user,
        'plan_request': plan_request,
        'users': users
    }
    return render(request, 'gym/add_diet_plan.html', context)

@login_required
def download_diet_plan(request, plan_id):
    # Get the diet plan
    plan = get_object_or_404(DietPlan, id=plan_id)
    
    # Check if user has access to this plan
    if plan.user != request.user and not plan.user.is_staff:
        messages.error(request, "شما دسترسی لازم برای دانلود این برنامه غذایی را ندارید.")
        return redirect('gym:diet_plans')
    
    # Create a BytesIO buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object, using the BytesIO buffer as its "file"
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Always use Helvetica font - it's available on all systems
    p.setFont('Helvetica', 14)
    
    # Draw the title (no RTL support, but will still be readable)
    title = f"Diet Plan: {plan.title}"
    p.drawCentredString(300, 750, title)
    
    # Add creation date
    date_text = f"Created on: {plan.created_at.strftime('%Y/%m/%d')}"
    p.setFont('Helvetica', 10)
    p.drawString(50, 720, date_text)
    
    # Add description
    if plan.description:
        p.setFont('Helvetica', 12)
        description = plan.description
        
        # Split description into lines that fit on the page
        lines = []
        for line in description.split('\n'):
            if len(line) > 80:  # Rough estimate of characters that fit on a line
                chunks = [line[i:i+80] for i in range(0, len(line), 80)]
                lines.extend(chunks)
            else:
                lines.append(line)
        
        y_position = 680
        for line in lines:
            if y_position < 50:  # Start a new page if we're at the bottom
                p.showPage()
                p.setFont('Helvetica', 12)
                y_position = 750
            p.drawString(50, y_position, line)
            y_position -= 15
    
    # Add image if available
    if plan.image:
        try:
            img_path = plan.image.path
            img = Image.open(img_path)
            img_width, img_height = img.size
            
            # Scale down image if it's too large
            max_width = 500
            max_height = 400
            if img_width > max_width or img_height > max_height:
                ratio = min(max_width/img_width, max_height/img_height)
                img_width = int(img_width * ratio)
                img_height = int(img_height * ratio)
            
            # Start a new page for the image
            p.showPage()
            p.drawInlineImage(img_path, 50, 500, width=img_width, height=img_height)
        except Exception as e:
            print(f"Error adding image to PDF: {str(e)}")
    
    # Add footer with user info
    p.showPage()  # Start a new page for the footer
    p.setFont('Helvetica', 10)
    try:
        full_name = plan.user.userprofile.name if hasattr(plan.user, 'userprofile') else plan.user.username
    except UserProfile.DoesNotExist:
        full_name = plan.user.username
    footer = f"Created by: {full_name}"
    p.drawString(50, 30, footer)
    
    # Close the PDF object cleanly, and we're done
    p.save()
    
    # Get the value of the BytesIO buffer and write it to the response
    buffer.seek(0)
    
    # Create the response with PDF mime type
    filename = f"diet_plan_{plan.title}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# Ticket views
@login_required
def tickets(request):
    # For admin/staff users, show all tickets
    if request.user.is_staff:
        # Get filter parameters
        status = request.GET.get('status')
        search_query = request.GET.get('search', '')
        
        # Base queryset
        tickets = Ticket.objects.select_related('user').all().order_by('-created_at')
        
        # Apply filters
        if status:
            tickets = tickets.filter(status=status)
        
        if search_query:
            tickets = tickets.filter(
                Q(subject__icontains=search_query) |
                Q(message__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__userprofile__name__icontains=search_query)
            )
        
        context = {
            'tickets': tickets,
            'is_admin': True,
            'status_filter': status,
            'search_query': search_query,
        }
        return render(request, 'gym/admin/tickets.html', context)
    
    # For regular users, show only their tickets
    user_tickets = Ticket.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'gym/tickets.html', {'tickets': user_tickets})

@login_required
def add_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(request, 'Ticket submitted successfully!')
            return redirect('gym:tickets')
    else:
        form = TicketForm()
    
    return render(request, 'gym/add_ticket.html', {'form': form})

@login_required
def ticket_detail(request, ticket_id):
    # For admin/staff users, allow access to all tickets
    if request.user.is_staff:
        ticket = get_object_or_404(Ticket, id=ticket_id)
    else:
        ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    
    responses = TicketResponse.objects.filter(ticket=ticket).order_by('created_at')
    
    if request.method == 'POST':
        form = TicketResponseForm(request.POST)
        if form.is_valid():
            response = TicketResponse(
                ticket=ticket,
                user=request.user,
                message=form.cleaned_data['message']
            )
            response.save()
            
            # Update ticket status when admin responds
            if request.user.is_staff:
                ticket.status = 'in_progress'
                ticket.save()
            
            messages.success(request, 'پاسخ با موفقیت ثبت شد.')
            return redirect('gym:ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketResponseForm()
    
    context = {
        'ticket': ticket,
        'responses': responses,
        'form': form,
        'is_admin': request.user.is_staff
    }
    return render(request, 'gym/ticket_detail.html', context)

@login_required
@staff_member_required
def update_ticket_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['pending', 'in_progress', 'resolved', 'closed']:
            ticket.status = status
            ticket.save()
            messages.success(request, 'وضعیت تیکت با موفقیت به‌روزرسانی شد.')
        else:
            messages.error(request, 'وضعیت نامعتبر است.')
    
    return redirect('gym:ticket_detail', ticket_id=ticket.id)

# Document views
@login_required
def documents(request):
    user_documents = Document.objects.filter(user=request.user).order_by('-upload_date')
    return render(request, 'gym/documents.html', {'documents': user_documents})

@login_required
def add_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.save()
            messages.success(request, 'Document uploaded successfully!')
            return redirect('gym:documents')
    else:
        form = DocumentForm()
    
    return render(request, 'gym/add_document.html', {'form': form})

@login_required
def view_document(request, doc_id):
    document = get_object_or_404(Document, id=doc_id)
    
    # Check if the user has access to view this document
    if document.user != request.user and not request.user.is_staff:
        if not document.is_paid:
            messages.error(request, "You don't have permission to view this document.")
            return redirect('gym:documents')
    
    try:
        return FileResponse(document.file, as_attachment=True)
    except Exception as e:
        messages.error(request, f"Error accessing document: {str(e)}")
        return redirect('gym:documents')

# Admin views
@login_required
def admin_user_management(request):
    if not request.user.is_staff:
        messages.error(request, 'شما دسترسی لازم برای مدیریت کاربران را ندارید.')
        return redirect('gym:profile')
    
    users = User.objects.all()
    return render(request, 'gym/admin/user_management.html', {'users': users})

@login_required
@staff_member_required
def vip_customers(request):
    """View for managing VIP customers"""
    # Get filter parameters
    search_query = request.GET.get('search', '')
    vip_filter = request.GET.get('vip_filter', 'all')  # all, vip_only, non_vip
    
    # Base queryset
    if vip_filter == 'vip_only':
        user_profiles = UserProfile.objects.filter(is_vip=True)
    elif vip_filter == 'non_vip':
        user_profiles = UserProfile.objects.filter(is_vip=False)
    else:
        user_profiles = UserProfile.objects.all()
    
    # Apply search filter
    if search_query:
        user_profiles = user_profiles.filter(
            Q(name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(melli_code__icontains=search_query)
        )
    
    # Order by VIP status (VIP first) then by name
    user_profiles = user_profiles.order_by('-is_vip', 'name')
    
    # Get VIP statistics
    vip_stats = {
        'total_users': UserProfile.objects.count(),
        'vip_users': UserProfile.objects.filter(is_vip=True).count(),
        'non_vip_users': UserProfile.objects.filter(is_vip=False).count(),
        'vip_percentage': round((UserProfile.objects.filter(is_vip=True).count() / UserProfile.objects.count()) * 100, 1) if UserProfile.objects.count() > 0 else 0,
    }
    
    context = {
        'user_profiles': user_profiles,
        'search_query': search_query,
        'vip_filter': vip_filter,
        'vip_stats': vip_stats,
    }
    
    return render(request, 'gym/admin/vip_customers.html', context)

@login_required
@staff_member_required
def toggle_vip_status(request, user_id):
    """View for toggling VIP status of a user"""
    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    
    if request.method == 'POST':
        user_profile.is_vip = not user_profile.is_vip
        user_profile.save()
        
        status_text = "VIP" if user_profile.is_vip else "عادی"
        messages.success(request, f'وضعیت {user_profile.name or user_profile.user.username} به {status_text} تغییر یافت.')
    
    # Redirect back to the referring page
    referrer = request.META.get('HTTP_REFERER')
    if referrer:
        return redirect(referrer)
    return redirect('gym:vip_customers')

@login_required
@staff_member_required
def manage_plan_requests(request):
    """View for managing all plan requests"""
    # Get filter parameters
    plan_type = request.GET.get('plan_type', '')
    status = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    plan_requests = PlanRequest.objects.all().order_by('-created_at')
    
    # Apply filters
    if plan_type:
        plan_requests = plan_requests.filter(plan_type=plan_type)
    
    if status:
        plan_requests = plan_requests.filter(status=status)
            
    if search_query:
        plan_requests = plan_requests.filter(
            Q(description__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__userprofile__name__icontains=search_query)
        )

    context = {
        'plan_requests': plan_requests,
        'plan_type': plan_type,
        'status': status,
        'search_query': search_query,
    }
    
    return render(request, 'gym/admin/manage_plan_requests.html', context)

@login_required
def request_plan(request):
    # First check if user has filled body information
    try:
        user_profile = request.user.userprofile
        body_info = user_profile.body_information
    except (UserProfile.DoesNotExist, BodyInformationUser.DoesNotExist):
        messages.warning(request, "لطفاً ابتدا اطلاعات بدنی خود را تکمیل کنید تا بتوانیم برنامه مناسبی برای شما تهیه کنیم.")
        return redirect("gym:body_information_form")

    """View for submitting a new plan request (workout or diet)"""
    if request.method == 'POST':
        plan_type = request.POST.get('plan_type')
        description = request.POST.get('description')
        
        if plan_type in ['workout', 'diet'] and description:
            # Store plan request data in session for later processing after payment
            request.session['pending_plan_request'] = {
                'plan_type': plan_type,
                'description': description
            }
            
            messages.info(request, 'لطفاً برای تکمیل درخواست، مبلغ مربوطه را پرداخت کرده و رسید آن را آپلود کنید.')
            
            # Redirect to payment page for plan request
            return redirect('gym:plan_request_payment')
        else:
            messages.error(request, 'اطلاعات ارسالی نامعتبر است.')
            
    # For GET requests or invalid form data, redirect to home
    return redirect('gym:home')

@login_required
def update_plan_request(request, request_id):
    """View for updating a plan request status"""
    plan_request = get_object_or_404(PlanRequest, id=request_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        admin_response = request.POST.get('admin_response', '')
        
        if status in ['approved', 'rejected']:
            plan_request.status = status
            plan_request.admin_response = admin_response
            plan_request.save()
            
            status_display = "تایید شده" if status == "approved" else "رد شده"
            messages.success(request, f'وضعیت درخواست به {status_display} تغییر یافت.')
    else:
        # Handle GET requests (quick actions from the admin tables)
        status = request.GET.get('status')
        
        if status in ['approved', 'rejected']:
            plan_request.status = status
            plan_request.save()
            
            status_display = "تایید شده" if status == "approved" else "رد شده"
            messages.success(request, f'وضعیت درخواست به {status_display} تغییر یافت.')
    
    # Redirect back to the referring page or to the plan requests page
    referrer = request.META.get('HTTP_REFERER')
    if referrer:
        return redirect(referrer)
    return redirect('gym:manage_plan_requests')

@login_required
def payments(request):
    # Get regular payments
    if request.user.is_staff:
        # For admin users, get all payments
        payments = Payment.objects.all().order_by('-payment_date')
        
        # Chart data for admin dashboard
        import json
        
        # Get filter parameters
        chart_period = request.GET.get('chart_period', 'monthly')  # monthly, weekly, yearly
        chart_type_filter = request.GET.get('chart_type_filter', 'all')  # all, membership, workout_plan, diet_plan, other
        chart_status_filter = request.GET.get('chart_status_filter', 'approved')  # all, pending, approved, rejected
        
        # Base queryset for charts
        chart_payments = Payment.objects.all()
        
        # Apply status filter
        if chart_status_filter != 'all':
            chart_payments = chart_payments.filter(status=chart_status_filter)
        
        # Apply type filter
        if chart_type_filter != 'all':
            chart_payments = chart_payments.filter(payment_type=chart_type_filter)
        
        # Prepare chart data based on period
        chart_data = {}
        
        if chart_period == 'monthly':
            # Last 12 months
            months_data = []
            labels = []
            now = datetime.datetime.now()
            for i in range(11, -1, -1):
                month_start = now.replace(day=1) - timedelta(days=30*i)
                month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                
                month_payments = chart_payments.filter(
                    payment_date__gte=month_start.date(),
                    payment_date__lte=month_end.date()
                )
                
                total_amount = month_payments.aggregate(total=Sum('amount'))['total'] or 0
                labels.append(month_start.strftime('%Y/%m'))
                months_data.append(int(total_amount))
            
            chart_data = {
                'labels': labels,
                'data': months_data,
                'label': 'درآمد ماهانه (تومان)'
            }
        
        elif chart_period == 'weekly':
            # Last 8 weeks
            weeks_data = []
            labels = []
            now = datetime.datetime.now()
            for i in range(7, -1, -1):
                week_start = now - timedelta(days=now.weekday() + 7*i)
                week_end = week_start + timedelta(days=6)
                
                week_payments = chart_payments.filter(
                    payment_date__gte=week_start.date(),
                    payment_date__lte=week_end.date()
                )
                
                total_amount = week_payments.aggregate(total=Sum('amount'))['total'] or 0
                labels.append(f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}")
                weeks_data.append(int(total_amount))
            
            chart_data = {
                'labels': labels,
                'data': weeks_data,
                'label': 'درآمد هفتگی (تومان)'
            }
        
        elif chart_period == 'yearly':
            # Last 3 years
            years_data = []
            labels = []
            current_year = datetime.datetime.now().year
            for year in range(current_year-2, current_year+1):
                year_payments = chart_payments.filter(payment_date__year=year)
                total_amount = year_payments.aggregate(total=Sum('amount'))['total'] or 0
                labels.append(str(year))
                years_data.append(int(total_amount))
            
            chart_data = {
                'labels': labels,
                'data': years_data,
                'label': 'درآمد سالانه (تومان)'
            }
        
        # Payment type breakdown chart (pie chart)
        type_breakdown = chart_payments.values('payment_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        type_chart_data = {
            'labels': [dict(Payment.PAYMENT_TYPE_CHOICES)[item['payment_type']] for item in type_breakdown],
            'data': [int(item['total']) for item in type_breakdown],
            'counts': [item['count'] for item in type_breakdown]
        }
        
        # Status breakdown chart (pie chart)
        status_breakdown = Payment.objects.values('status').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        status_chart_data = {
            'labels': [dict(Payment.PAYMENT_STATUS_CHOICES)[item['status']] for item in status_breakdown],
            'data': [int(item['total']) for item in status_breakdown],
            'counts': [item['count'] for item in status_breakdown]
        }
        
        # Total statistics
        total_income = chart_payments.aggregate(total=Sum('amount'))['total'] or 0
        total_count = chart_payments.count()
        avg_payment = (total_income / total_count) if total_count > 0 else 0
        
        context = {
            'payments': payments,
            'is_admin': True,
            'chart_data': json.dumps(chart_data),
            'type_chart_data': json.dumps(type_chart_data),
            'status_chart_data': json.dumps(status_chart_data),
            'chart_period': chart_period,
            'chart_type_filter': chart_type_filter,
            'chart_status_filter': chart_status_filter,
            'total_income': total_income,
            'total_count': total_count,
            'avg_payment': avg_payment,
        }
        return render(request, 'gym/payments.html', context)
    
    else:
        # For regular users, get only their payments
        payments = Payment.objects.filter(user=request.user).order_by('-payment_date')
        
        context = {
            'payments': payments,
        }
        return render(request, 'gym/payments.html', context)

@login_required
def add_payment(request):
    # Check if user's profile is complete
    try:
        user_profile = request.user.userprofile
        is_complete, missing_field = is_profile_complete_for_payment(user_profile)
        
        if not is_complete:
            messages.warning(request, f'برای انجام پرداخت، لطفاً اطلاعات پروفایل خود را کامل کنید. فیلد "{missing_field}" خالی است.')
            # Store the payment redirect in session
            request.session['payment_redirect_url'] = 'gym:add_payment'
            return redirect('gym:edit_profile')
    except UserProfile.DoesNotExist:
        messages.error(request, 'پروفایل شما یافت نشد.')
        return redirect('gym:profile')
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.save()
            messages.success(request, 'اطلاعات پرداخت با موفقیت ثبت شد!')
            return redirect('gym:payments')
        else:
            # Invalid form, errors will be shown to the user
            pass
    else:
        form = PaymentForm()
    
    return render(request, 'gym/add_payment.html', {'form': form})

@login_required
def plan_request_payment(request):
    """Payment view specifically for plan requests"""
    # Check if there's a pending plan request in session
    if 'pending_plan_request' not in request.session:
        messages.error(request, 'درخواست برنامه‌ای در انتظار پرداخت یافت نشد.')
        return redirect('gym:profile')
    
    plan_data = request.session['pending_plan_request']
    
    # Get active payment card for manual payments
    payment_card = PaymentCard.objects.filter(is_active=True).first()
    
    # Get price based on plan type
    plan_price = payment_card.get_price_for_plan_type(plan_data['plan_type']) if payment_card else 500000
    
    # Check if user's profile is complete
    try:
        user_profile = request.user.userprofile
        is_complete, missing_field = is_profile_complete_for_payment(user_profile)
        
        if not is_complete:
            messages.warning(request, f'برای انجام پرداخت، لطفاً اطلاعات پروفایل خود را کامل کنید. فیلد "{missing_field}" خالی است.')
            # Store the payment redirect in session
            request.session['payment_redirect_url'] = 'gym:plan_request_payment'
            return redirect('gym:edit_profile')
    except UserProfile.DoesNotExist:
        messages.error(request, 'پروفایل شما یافت نشد.')
        return redirect('gym:profile')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'gateway')
        
        if payment_method == 'gateway':
            # Handle gateway payment
            from gym.utils.payment_gateway import PaymentGateway
            gateway = PaymentGateway()
            
            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                amount=plan_price,
                payment_type='workout_plan' if plan_data['plan_type'] == 'workout' else 'diet_plan',
                payment_method='gateway',
                status='pending',
                gateway_type=gateway.gateway_type
            )
            
            # Store payment ID in session for callback verification
            request.session['pending_payment_id'] = payment.id
            
            # Generate callback URL
            callback_url = request.build_absolute_uri(reverse('gym:payment_gateway_callback'))
            
            # Create payment request with gateway
            plan_type_display = 'برنامه تمرینی' if plan_data['plan_type'] == 'workout' else 'برنامه غذایی'
            description = f'پرداخت {plan_type_display} - {user_profile.name}'
            
            success, result = gateway.create_payment_request(
                amount=plan_price,
                description=description,
                callback_url=callback_url,
                mobile=user_profile.phone_number,
                email=request.user.email
            )
            
            if success:
                payment.gateway_authority = result['authority']
                payment.save()
                # Redirect to payment gateway
                return redirect(result['gateway_url'])
            else:
                payment.status = 'failed'
                payment.gateway_response = str(result)
                payment.save()
                messages.error(request, f'خطا در اتصال به درگاه پرداخت: {result.get("error", "خطای ناشناخته")}')
        
        else:
            # Handle manual payment (existing logic)
            if not payment_card:
                messages.error(request, 'در حال حاضر امکان پرداخت دستی وجود ندارد.')
                return redirect('gym:profile')
                
            form = PaymentForm(request.POST, request.FILES)
            if form.is_valid():
                # Create the payment
                payment = form.save(commit=False)
                payment.user = request.user
                payment.payment_method = 'manual'
                payment.payment_type = 'workout_plan' if plan_data['plan_type'] == 'workout' else 'diet_plan'
                payment.save()
                
                # Send email notification to admins for payment upload
                try:
                    from gym.utils.email_notifications import send_payment_upload_notification
                    send_payment_upload_notification(payment, request)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send payment upload notification email: {str(e)}")
                
                # Create the plan request after successful payment upload
                plan_request = PlanRequest.objects.create(
                    user=request.user,
                    plan_type=plan_data['plan_type'],
                    description=plan_data['description']
                )
                
                # Send email notification to admins
                try:
                    from gym.utils.email_notifications import send_plan_request_notification
                    send_plan_request_notification(plan_request, request)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send plan request notification email: {str(e)}")
                
                # Store plan data for status display and clear pending request
                request.session['completed_plan_request'] = {
                    'plan_type': plan_data['plan_type'],
                    'description': plan_data['description'],
                    'request_id': plan_request.id
                }
                del request.session['pending_plan_request']
                
                messages.success(request, 'پرداخت شما با موفقیت ثبت شد و درخواست برنامه شما در انتظار بررسی است.')
                return redirect('gym:plan_request_flow', step='status')
    
    # For GET requests, prepare form for manual payment
    initial_data = {
        'payment_type': 'workout_plan' if plan_data['plan_type'] == 'workout' else 'diet_plan',
        'amount': plan_price
    }
    form = PaymentForm(initial=initial_data)
    
    context = {
        'form': form,
        'plan_data': plan_data,
        'payment_card': payment_card,
        'plan_price': plan_price,
        'plan_type_display': 'برنامه تمرینی' if plan_data['plan_type'] == 'workout' else 'برنامه غذایی'
    }
    return render(request, 'gym/plan_request_payment.html', context)

@login_required
def payment_gateway_callback(request):
    """Handle payment gateway callback"""
    authority = request.GET.get('Authority') or request.POST.get('authority')
    status = request.GET.get('Status')
    
    # Get pending payment from session
    payment_id = request.session.get('pending_payment_id')
    
    if not payment_id:
        messages.error(request, 'اطلاعات پرداخت یافت نشد.')
        return redirect('gym:profile')
    
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user)
    except Payment.DoesNotExist:
        messages.error(request, 'پرداخت مورد نظر یافت نشد.')
        return redirect('gym:profile')
    
    # Clear payment ID from session
    if 'pending_payment_id' in request.session:
        del request.session['pending_payment_id']
    
    if status == 'OK' and authority:
        # Verify payment with gateway
        from gym.utils.payment_gateway import PaymentGateway
        gateway = PaymentGateway(payment.gateway_type)
        
        success, result = gateway.verify_payment(authority, payment.amount)
        
        if success:
            # Payment successful
            payment.status = 'approved'
            payment.gateway_ref_id = result.get('ref_id')
            payment.gateway_response = json.dumps(result)
            payment.save()
            
            # Get plan data from session
            plan_data = request.session.get('pending_plan_request')
            
            if plan_data:
                # Create the plan request after successful payment
                plan_request = PlanRequest.objects.create(
                    user=request.user,
                    plan_type=plan_data['plan_type'],
                    description=plan_data['description']
                )
                
                # Send email notifications
                try:
                    from gym.utils.email_notifications import send_payment_upload_notification, send_plan_request_notification
                    send_payment_upload_notification(payment, request)
                    send_plan_request_notification(plan_request, request)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send notification emails: {str(e)}")
                
                # Store plan data for status display and clear pending request
                request.session['completed_plan_request'] = {
                    'plan_type': plan_data['plan_type'],
                    'description': plan_data['description'],
                    'request_id': plan_request.id
                }
                del request.session['pending_plan_request']
                
                messages.success(request, f'پرداخت با موفقیت انجام شد. شماره پیگیری: {payment.gateway_ref_id}')
                return redirect('gym:plan_request_flow', step='status')
            else:
                messages.success(request, f'پرداخت با موفقیت انجام شد. شماره پیگیری: {payment.gateway_ref_id}')
                return redirect('gym:payments')
        else:
            # Payment verification failed
            payment.status = 'failed'
            payment.gateway_response = json.dumps(result)
            payment.save()
            messages.error(request, f'خطا در تایید پرداخت: {result.get("error", "خطای ناشناخته")}')
    else:
        # Payment cancelled or failed
        payment.status = 'failed'
        payment.gateway_response = f'Status: {status}, Authority: {authority}'
        payment.save()
        
        if status == 'NOK':
            messages.error(request, 'پرداخت توسط کاربر لغو شد.')
        else:
            messages.error(request, 'خطا در انجام پرداخت.')
    
    return redirect('gym:profile')

def password_reset(request):
    """Handle user password reset requests"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        # Check if email exists
        if not email:
            messages.error(request, 'لطفاً ایمیل خود را وارد کنید.')
            return render(request, 'gym/password_reset.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Set a fixed password for testing purposes (TEMPORARY SOLUTION)
            new_password = "123456"
            
            # Update user's password
            user.set_password(new_password)
            user.save()
            
            # Store the new password in session to display on success page
            request.session['temp_password'] = new_password
            request.session['temp_email'] = email
            
            messages.success(request, 'رمز عبور با موفقیت بازنشانی شد. از رمز جدید برای ورود استفاده کنید.')
            return redirect('gym:password_reset_success')
                
        except User.DoesNotExist:
            # Don't reveal that the email doesn't exist for security reasons
            messages.success(request, 'اگر این ایمیل در سیستم ثبت شده باشد، دستورالعمل بازیابی رمز عبور برای آن ارسال خواهد شد.')
            return redirect('gym:password_reset_success')
    
    return render(request, 'gym/password_reset.html')

def password_reset_success(request):
    """Show password reset success page"""
    context = {}
    
    # If we have a temporary password in the session, add it to the context
    if 'temp_password' in request.session:
        context['temp_password'] = request.session['temp_password']
        context['temp_email'] = request.session['temp_email']
        # Clear the session data after showing it once
        del request.session['temp_password']
        del request.session['temp_email']
    
    return render(request, 'gym/password_reset_success.html', context)

def is_profile_complete_for_payment(user_profile):
    """
    Check if a user's profile has all the necessary information for payment
    """
    # Check if essential fields are filled
    if not user_profile.home_address:
        return False, 'آدرس منزل'
    
    # All required fields are filled
    return True, None

@login_required
def verify_profile_for_payment(request, next_url=None):
    """
    Check if the user profile is complete before proceeding to payment
    """
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'پروفایل شما یافت نشد.')
        return redirect('gym:profile')
    
    # Check if profile is complete
    is_complete, missing_field = is_profile_complete_for_payment(user_profile)
    
    if not is_complete:
        messages.warning(request, f'برای انجام پرداخت، لطفاً اطلاعات پروفایل خود را کامل کنید. فیلد "{missing_field}" خالی است.')
        # Store the next_url in session for later redirect
        if next_url:
            request.session['payment_redirect_url'] = next_url
        return redirect('gym:edit_profile')
    
    # If the profile is complete, redirect to the next step
    if next_url:
        return redirect(next_url)
    return redirect('gym:payments')

# Body Analysis Reports
@login_required
def body_analysis_reports(request):
    """View all body analysis reports for a user or all reports for admin"""
    
    if request.user.is_staff:
        # For admin, get all reports with filters
        reports = BodyAnalysisReport.objects.all().order_by('-report_date')
        
        # Get filter parameters
        status = request.GET.get('status')
        user_id = request.GET.get('user_id')
        search_query = request.GET.get('search', '')
        
        # Apply filters
        if status:
            reports = reports.filter(status=status)
        
        if user_id:
            reports = reports.filter(user_id=user_id)
        
        if search_query:
            reports = reports.filter(
                Q(user__username__icontains=search_query) |
                Q(user__userprofile__name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(admin_response__icontains=search_query)
            )
            
        context = {
            'reports': reports,
            'status': status,
            'user_id': user_id,
            'search_query': search_query,
            'is_admin': True
        }
        
        return render(request, 'gym/admin/body_analysis_reports.html', context)
    
    else:
        # For regular users, get only their reports
        reports = BodyAnalysisReport.objects.filter(user=request.user).order_by('-report_date')
        
        if request.method == 'POST':
            form = BodyAnalysisReportForm(request.POST, request.FILES)
            if form.is_valid():
                report = form.save(commit=False)
                report.user = request.user
                report.save()
                messages.success(request, 'گزارش آنالیز بدن با موفقیت ثبت شد و در انتظار بررسی است.')
                return redirect('gym:body_analysis_reports')
        else:
            form = BodyAnalysisReportForm()
        
        context = {
            'reports': reports,
            'form': form
        }
        
        return render(request, 'gym/body_analysis_reports.html', context)

@login_required
def body_analysis_detail(request, report_id):
    """View and respond to a specific body analysis report"""
    report = get_object_or_404(BodyAnalysisReport, id=report_id)
    
    # Check permissions
    if not request.user.is_staff and request.user != report.user:
        messages.error(request, 'شما دسترسی لازم برای مشاهده این گزارش را ندارید.')
        return redirect('gym:body_analysis_reports')
    
    # Handle response from admin
    if request.user.is_staff and request.method == 'POST':
        form = BodyAnalysisResponseForm(request.POST, instance=report)
        if form.is_valid():
            updated_report = form.save(commit=False)
            updated_report.status = 'reviewed'
            updated_report.response_date = timezone.now()
            updated_report.save()
            messages.success(request, 'پاسخ شما با موفقیت ثبت شد.')
            return redirect('gym:body_analysis_reports')
    
    # Prepare form for admin response
    if request.user.is_staff:
        form = BodyAnalysisResponseForm(instance=report)
    else:
        form = None
    
    context = {
        'report': report,
        'form': form,
        'is_admin': request.user.is_staff
    }
    
    return render(request, 'gym/body_analysis_detail.html', context)

# Monthly Goals
@login_required
def monthly_goals(request):
    """View and manage monthly goals for a user or all goals for admin"""
    
    if request.user.is_staff:
        # For admin, get all goals with filters
        goals = MonthlyGoal.objects.all().order_by('-start_date')
        
        # Get filter parameters
        status = request.GET.get('status')
        user_id = request.GET.get('user_id')
        search_query = request.GET.get('search', '')
        
        # Apply filters
        if status:
            goals = goals.filter(status=status)
        
        if user_id:
            goals = goals.filter(user_id=user_id)
        
        if search_query:
            goals = goals.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__userprofile__name__icontains=search_query)
            )
            
        # Add current measurements and progress data to each goal
        goals_with_data = []
        for goal in goals:
            current_measurements = goal.get_current_measurements()
            progress_data = goal.calculate_progress_towards_targets()
            goals_with_data.append({
                'goal': goal,
                'current_measurements': current_measurements,
                'progress_data': progress_data
            })
        
        context = {
            'goals': goals,
            'goals_with_data': goals_with_data,
            'status': status,
            'user_id': user_id,
            'search_query': search_query,
            'is_admin': True
        }
        
        return render(request, 'gym/admin/monthly_goals.html', context)
    
    else:
        # For regular users, get only their goals (read-only)
        goals = MonthlyGoal.objects.filter(user=request.user).order_by('-start_date')
        
        # Add current measurements and progress data for user's goals
        goals_with_data = []
        for goal in goals:
            current_measurements = goal.get_current_measurements()
            progress_data = goal.calculate_progress_towards_targets()
            goals_with_data.append({
                'goal': goal,
                'current_measurements': current_measurements,
                'progress_data': progress_data
            })
        
        context = {
            'goals': goals,
            'goals_with_data': goals_with_data,
            'is_user_view': True
        }
        
        return render(request, 'gym/monthly_goals.html', context)

@login_required
def monthly_goal_detail(request, goal_id):
    """View and update a specific monthly goal"""
    goal = get_object_or_404(MonthlyGoal, id=goal_id)
    
    # Check permissions
    if not request.user.is_staff and request.user != goal.user:
        messages.error(request, 'شما دسترسی لازم برای مشاهده این هدف را ندارید.')
        return redirect('gym:monthly_goals')
    
    # Handle updates from user
    if request.user == goal.user and request.method == 'POST' and 'update_progress' in request.POST:
        form = MonthlyGoalUpdateForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'پیشرفت شما با موفقیت به‌روزرسانی شد.')
            return redirect('gym:monthly_goal_detail', goal_id=goal.id)
    
    # Handle coach notes from admin
    if request.user.is_staff and request.method == 'POST' and 'update_coach_notes' in request.POST:
        form = MonthlyGoalCoachForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'یادداشت مربی با موفقیت ثبت شد.')
            return redirect('gym:monthly_goal_detail', goal_id=goal.id)
    
    # Prepare forms
    user_form = MonthlyGoalUpdateForm(instance=goal) if request.user == goal.user else None
    coach_form = MonthlyGoalCoachForm(instance=goal) if request.user.is_staff else None
    
    context = {
        'goal': goal,
        'user_form': user_form,
        'coach_form': coach_form,
        'is_admin': request.user.is_staff,
        'is_own_goal': request.user == goal.user
    }
    
    return render(request, 'gym/monthly_goal_detail.html', context)

@login_required
@staff_member_required
def add_monthly_goal(request):
    """Admin view to add a new monthly goal for a user"""
    if request.method == 'POST':
        form = MonthlyGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            
            # Set default title only
            if not goal.title:
                goal.title = f"هدف ماهانه {goal.user.userprofile.name or goal.user.username}"
            
            goal.save()
            messages.success(request, f'هدف ماهانه برای {goal.user.userprofile.name or goal.user.username} با موفقیت ایجاد شد.')
            return redirect('gym:monthly_goals')
    else:
        form = MonthlyGoalForm()
    
    # Get list of users for the form
    users = User.objects.exclude(is_staff=True).order_by('username')
    
    context = {
        'form': form,
        'users': users,
        'page_title': 'افزودن هدف ماهانه جدید'
    }
    return render(request, 'gym/admin/add_monthly_goal.html', context)

@login_required
@staff_member_required
def get_user_measurements(request, user_id):
    """API endpoint to get user's current measurements for goal setting"""
    try:
        user = User.objects.get(id=user_id)
        measurements = {}
        
        # Get body information (initial/baseline measurements)
        try:
            body_info = user.userprofile.body_information
            measurements['initial_weight'] = float(body_info.weight_kg)
            measurements['height'] = body_info.height_cm
            measurements['age'] = None
            if body_info.birth_date:
                from datetime import date
                age = date.today().year - body_info.birth_date.year
                measurements['age'] = age
        except:
            pass
        
        # Get latest progress measurements
        latest_weight = user.progress_analyses.filter(measurement_type='weight').order_by('-measurement_date').first()
        if latest_weight:
            measurements['current_weight'] = float(latest_weight.value)
            measurements['current_weight_date'] = latest_weight.measurement_date.strftime('%Y-%m-%d')
        
        latest_body_fat = user.progress_analyses.filter(measurement_type='body_fat').order_by('-measurement_date').first()
        if latest_body_fat:
            measurements['current_body_fat'] = float(latest_body_fat.value)
            measurements['current_body_fat_date'] = latest_body_fat.measurement_date.strftime('%Y-%m-%d')
        
        latest_muscle_mass = user.progress_analyses.filter(measurement_type='muscle_mass').order_by('-measurement_date').first()
        if latest_muscle_mass:
            measurements['current_muscle_mass'] = float(latest_muscle_mass.value)
            measurements['current_muscle_mass_date'] = latest_muscle_mass.measurement_date.strftime('%Y-%m-%d')
        
        # Get user's name
        measurements['user_name'] = user.userprofile.name if hasattr(user, 'userprofile') and user.userprofile.name else user.username
        
        return JsonResponse(measurements)
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'کاربر یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@staff_member_required
def edit_monthly_goal(request, goal_id):
    """Admin view to edit an existing monthly goal"""
    goal = get_object_or_404(MonthlyGoal, id=goal_id)
    
    if request.method == 'POST':
        form = MonthlyGoalForm(request.POST, instance=goal)
        if form.is_valid():
            goal = form.save()
            messages.success(request, 'هدف ماهانه با موفقیت به‌روزرسانی شد.')
            return redirect('gym:monthly_goals')
    else:
        form = MonthlyGoalForm(instance=goal)
    
    # Get list of users for the form
    users = User.objects.exclude(is_staff=True).order_by('username')
    
    context = {
        'form': form,
        'goal': goal,
        'users': users,
        'page_title': 'ویرایش هدف ماهانه'
    }
    return render(request, 'gym/admin/add_monthly_goal.html', context)

@login_required
@staff_member_required
def delete_monthly_goal(request, goal_id):
    """Admin view to delete a monthly goal"""
    goal = get_object_or_404(MonthlyGoal, id=goal_id)
    
    if request.method == 'POST':
        user_name = goal.user.userprofile.name or goal.user.username
        goal_title = goal.title
        goal.delete()
        messages.success(request, f'هدف "{goal_title}" برای {user_name} با موفقیت حذف شد.')
        return redirect('gym:monthly_goals')
    
    context = {
        'goal': goal,
        'page_title': 'حذف هدف ماهانه'
    }
    return render(request, 'gym/admin/delete_monthly_goal.html', context)

# Progress Analysis
@login_required
def progress_analysis(request):
    """آنالیز پیشرفت - Three-color charts for admin, progress percentage for users"""
    
    if request.user.is_staff:
        # Admin View: Three-color line charts showing progress towards monthly goals
        
        # Get all users with active monthly goals
        users_with_goals = User.objects.filter(monthly_goals__isnull=False).distinct()
        
        # Get filter parameters
        user_id = request.GET.get('user_id')
        if user_id:
            users_with_goals = users_with_goals.filter(id=user_id)
        
        # Prepare chart data for each user
        users_chart_data = []
        
        for user in users_with_goals:
            # Get user's active goals
            active_goals = MonthlyGoal.objects.filter(
                user=user,
                status__in=['not_started', 'in_progress']
            ).order_by('-start_date')
            
            if not active_goals.exists():
                continue
                
            # Get progress data for key measurements
            progress_data = ProgressAnalysis.objects.filter(
                user=user,
                measurement_type__in=['weight', 'body_fat', 'muscle_mass']
            ).order_by('measurement_date')
            
            if not progress_data.exists():
                continue
            
            # Calculate progress percentages for latest goal
            latest_goal = active_goals.first()
            goal_progress = latest_goal.calculate_progress_towards_targets()
            current_measurements = latest_goal.get_current_measurements()
            
            # Prepare three-color chart data
            chart_dates = []
            weight_progress = []
            body_fat_progress = []
            muscle_mass_progress = []
            
            # Group measurements by date and calculate progress over time
            measurement_dates = progress_data.values_list('measurement_date', flat=True).distinct().order_by('measurement_date')
            
            for date in measurement_dates:
                chart_dates.append(date.strftime('%Y-%m-%d'))
                
                # Get measurements for this date
                date_measurements = progress_data.filter(measurement_date=date)
                
                # Calculate progress percentage for each measurement type on this date
                weight_entry = date_measurements.filter(measurement_type='weight').first()
                body_fat_entry = date_measurements.filter(measurement_type='body_fat').first() 
                muscle_mass_entry = date_measurements.filter(measurement_type='muscle_mass').first()
                
                # Weight progress calculation
                if weight_entry and latest_goal.target_weight:
                    try:
                        initial_weight = float(user.userprofile.body_information.weight_kg)
                    except:
                        initial_weight = float(progress_data.filter(measurement_type='weight').first().value)
                    
                    current_weight = float(weight_entry.value)
                    target_weight = float(latest_goal.target_weight)
        
                    if initial_weight != target_weight:
                        progress_pct = ((current_weight - initial_weight) / (target_weight - initial_weight)) * 100
                        weight_progress.append(max(0, min(100, progress_pct)))
                    else:
                        weight_progress.append(100 if current_weight == target_weight else 0)
                else:
                    weight_progress.append(0)
                
                # Body fat progress calculation  
                if body_fat_entry and latest_goal.target_body_fat_percentage:
                    initial_bf = float(progress_data.filter(measurement_type='body_fat').first().value)
                    current_bf = float(body_fat_entry.value)
                    target_bf = float(latest_goal.target_body_fat_percentage)
                    
                    if initial_bf != target_bf:
                        progress_pct = ((current_bf - initial_bf) / (target_bf - initial_bf)) * 100
                        body_fat_progress.append(max(0, min(100, progress_pct)))
                    else:
                        body_fat_progress.append(100 if current_bf == target_bf else 0)
                else:
                    body_fat_progress.append(0)
                
                # Muscle mass progress calculation
                if muscle_mass_entry and latest_goal.target_muscle_mass:
                    initial_mm = float(progress_data.filter(measurement_type='muscle_mass').first().value)
                    current_mm = float(muscle_mass_entry.value)
                    target_mm = float(latest_goal.target_muscle_mass)
                    
                    if initial_mm != target_mm:
                        progress_pct = ((current_mm - initial_mm) / (target_mm - initial_mm)) * 100
                        muscle_mass_progress.append(max(0, min(100, progress_pct)))
                    else:
                        muscle_mass_progress.append(100 if current_mm == target_mm else 0)
                else:
                    muscle_mass_progress.append(0)
            
            users_chart_data.append({
                'user': user,
                'user_name': user.userprofile.name if hasattr(user, 'userprofile') and user.userprofile.name else user.username,
                'goal': latest_goal,
                'chart_data': json.dumps({
                    'dates': chart_dates,
                    'weight_progress': weight_progress,
                    'body_fat_progress': body_fat_progress,
                    'muscle_mass_progress': muscle_mass_progress,
                }),
                'current_measurements': current_measurements,
                'goal_progress': goal_progress
            })
        
        # Get all users for filter dropdown
        all_users = User.objects.filter(monthly_goals__isnull=False).distinct()
            
        context = {
            'users_chart_data': users_chart_data,
            'all_users': all_users,
            'selected_user_id': int(user_id) if user_id else None,
            'is_admin': True
        }
        
        return render(request, 'gym/admin/progress_analysis.html', context)
    
    else:
        # User View: Personal progress percentage charts comparing to their goals
        
        # Get user's goals
        user_goals = MonthlyGoal.objects.filter(user=request.user).order_by('-start_date')
        
        # Get user's progress data
        progress_data = ProgressAnalysis.objects.filter(
            user=request.user,
            measurement_type__in=['weight', 'body_fat', 'muscle_mass']
        ).order_by('measurement_date')
        
        # Handle new measurement form
        if request.method == 'POST':
            form = ProgressAnalysisForm(request.POST)
            if form.is_valid():
                progress = form.save(commit=False)
                progress.user = request.user
                progress.save()
                messages.success(request, 'اندازه‌گیری جدید با موفقیت ثبت شد.')
                return redirect('gym:progress_analysis')
        else:
            form = ProgressAnalysisForm()
        
        # Prepare progress percentage chart data
        chart_data = {
            'dates': [],
            'weight_progress': [],
            'body_fat_progress': [],
            'muscle_mass_progress': []
        }
        
        goals_info = []
        
        if user_goals.exists() and progress_data.exists():
            # Get latest goal for calculations
            latest_goal = user_goals.first()
            
            # Get unique measurement dates
            measurement_dates = progress_data.values_list('measurement_date', flat=True).distinct().order_by('measurement_date')
            
            for date in measurement_dates:
                chart_data['dates'].append(date.strftime('%Y-%m-%d'))
                
                # Get measurements for this date
                date_measurements = progress_data.filter(measurement_date=date)
                
                # Calculate progress percentages (same logic as admin view)
                # Weight progress
                weight_entry = date_measurements.filter(measurement_type='weight').first()
                if weight_entry and latest_goal.target_weight:
                    try:
                        initial_weight = float(request.user.userprofile.body_information.weight_kg)
                    except:
                        initial_weight = float(progress_data.filter(measurement_type='weight').first().value)
                    
                    current_weight = float(weight_entry.value)
                    target_weight = float(latest_goal.target_weight)
                    
                    if initial_weight != target_weight:
                        progress_pct = ((current_weight - initial_weight) / (target_weight - initial_weight)) * 100
                        chart_data['weight_progress'].append(max(0, min(100, progress_pct)))
                    else:
                        chart_data['weight_progress'].append(100 if current_weight == target_weight else 0)
                else:
                    chart_data['weight_progress'].append(0)
                
                # Body fat progress
                body_fat_entry = date_measurements.filter(measurement_type='body_fat').first()
                if body_fat_entry and latest_goal.target_body_fat_percentage:
                    initial_bf = float(progress_data.filter(measurement_type='body_fat').first().value)
                    current_bf = float(body_fat_entry.value)
                    target_bf = float(latest_goal.target_body_fat_percentage)
                    
                    if initial_bf != target_bf:
                        progress_pct = ((current_bf - initial_bf) / (target_bf - initial_bf)) * 100
                        chart_data['body_fat_progress'].append(max(0, min(100, progress_pct)))
                    else:
                        chart_data['body_fat_progress'].append(100 if current_bf == target_bf else 0)
                else:
                    chart_data['body_fat_progress'].append(0)
                
                # Muscle mass progress
                muscle_mass_entry = date_measurements.filter(measurement_type='muscle_mass').first()
                if muscle_mass_entry and latest_goal.target_muscle_mass:
                    initial_mm = float(progress_data.filter(measurement_type='muscle_mass').first().value)
                    current_mm = float(muscle_mass_entry.value)
                    target_mm = float(latest_goal.target_muscle_mass)
                    
                    if initial_mm != target_mm:
                        progress_pct = ((current_mm - initial_mm) / (target_mm - initial_mm)) * 100
                        chart_data['muscle_mass_progress'].append(max(0, min(100, progress_pct)))
                    else:
                        chart_data['muscle_mass_progress'].append(100 if current_mm == target_mm else 0)
                else:
                    chart_data['muscle_mass_progress'].append(0)
            
            # Prepare goals info for display
            for goal in user_goals[:3]:  # Show last 3 goals
                goal_info = {
                    'goal': goal,
                    'current_measurements': goal.get_current_measurements(),
                    'progress_data': goal.calculate_progress_towards_targets()
                }
                goals_info.append(goal_info)
        
        context = {
            'chart_data': json.dumps(chart_data),
            'goals_info': goals_info,
            'progress_data': progress_data,
            'form': form,
            'has_goals': user_goals.exists(),
            'has_measurements': progress_data.exists()
        }
        
        return render(request, 'gym/progress_analysis.html', context)

@login_required
def delete_progress_entry(request, entry_id):
    entry = get_object_or_404(ProgressAnalysis, id=entry_id, user=request.user)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'رکورد با موفقیت حذف شد.')
        return redirect('gym:progress_analysis')
        return redirect('gym:progress_analysis')

@login_required
def body_information_form(request):
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'پروفایل شما یافت نشد.')
        return redirect('gym:profile')
    
    try:
        body_info = user_profile.body_information
        form = BodyInformationUserForm(instance=body_info)
        is_edit = True
    except BodyInformationUser.DoesNotExist:
        form = BodyInformationUserForm()
        is_edit = False
    
    if request.method == 'POST':
        if is_edit:
            form = BodyInformationUserForm(request.POST, request.FILES, instance=body_info)
        else:
            form = BodyInformationUserForm(request.POST, request.FILES)
        
        if form.is_valid():
            body_info = form.save(commit=False)
            body_info.user_profile = user_profile
            body_info.save()
            messages.success(request, 'اطلاعات بدنی شما با موفقیت ذخیره شد.')
            
            # Check if user is in the middle of a plan request process
            if 'pending_plan_request' in request.session:
                return redirect('gym:plan_request_flow', step='profile_check')
            
            # Redirect to the page that originally requested this form
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('gym:profile')
    
    context = {
        'form': form,
        'is_edit': is_edit
    }
    return render(request, 'gym/body_information_form.html', context)

@login_required 
def check_body_information_required(request, plan_type):
    """Check if user has filled body information before allowing plan request"""
    try:
        user_profile = request.user.userprofile
        body_info = user_profile.body_information
        # Body information exists, redirect to plan request
        return redirect('gym:request_plan')
    except (UserProfile.DoesNotExist, BodyInformationUser.DoesNotExist):
        # Body information doesn't exist, redirect to fill it first
        messages.warning(request, 'لطفاً ابتدا اطلاعات بدنی خود را تکمیل کنید.')
        return redirect(f'gym:body_information_form?next=gym:request_plan')

@login_required
def plan_request_flow(request, step=None):
    """Continuous 5-step plan request flow"""
    
    # Define the steps
    STEPS = {
        'request': {'name': 'ثبت درخواست', 'order': 1},
        'body_info': {'name': 'بررسی و تکمیل اطلاعات بدنی', 'order': 2},
        'profile_check': {'name': 'بررسی و تکمیل اطلاعات شخصی', 'order': 3},
        'payment': {'name': 'صفحه پرداخت و آپلود فیش', 'order': 4},
        'status': {'name': 'نشان دادن وضعیت درخواست', 'order': 5}
    }
    
    # If no step provided, start from beginning
    if not step:
        step = 'request'
    
    # Handle Step 1: Request submission
    if step == 'request':
        if request.method == 'POST':
            plan_type = request.POST.get('plan_type')
            description = request.POST.get('description')
            
            if plan_type in ['workout', 'diet'] and description:
                # Store plan request data in session
                request.session['pending_plan_request'] = {
                    'plan_type': plan_type,
                    'description': description,
                    'current_step': 'body_info'
                }
                # Don't show success message here as user hasn't completed the process yet
                return redirect('gym:plan_request_flow', step='body_info')
            else:
                messages.error(request, 'لطفاً تمام فیلدهای مورد نیاز را پر کنید.')
        
        context = {
            'steps': STEPS,
            'current_step': step,
            'step_data': STEPS[step]
        }
        return render(request, 'gym/plan_request_flow.html', context)
    
    # Check if plan request exists in session for steps that require it
    if 'pending_plan_request' not in request.session and step not in ['request', 'status']:
        # Only show error if user came from a step that requires session data and it's not a direct access
        messages.error(request, 'درخواستی در حال انجام یافت نشد. لطفاً مجدداً درخواست دهید.')
        return redirect('gym:plan_request_flow', step='request')
    
    # For status step, handle it even without session data (in case user completed payment)
    if step == 'status':
        # Check if we have completed plan request data
        if 'completed_plan_request' in request.session:
            completed_data = request.session['completed_plan_request']
            # Clear the completed data from session
            del request.session['completed_plan_request']
        
        # Clear any remaining session data
        if 'pending_plan_request' in request.session:
            del request.session['pending_plan_request']
        
        # Add a final success message and redirect to profile
        messages.success(request, 'درخواست شما با موفقیت ثبت شد! پس از بررسی پرداخت توسط ادمین، وضعیت درخواست شما به‌روزرسانی خواهد شد.')
        return redirect('gym:profile')
    
    # Get plan data from session (only for steps that need it)
    plan_data = request.session.get('pending_plan_request', {})
    
    # Handle Step 2: Body information check
    if step == 'body_info':
        try:
            user_profile = request.user.userprofile
            body_info = user_profile.body_information
            # Body information exists, move to next step
            plan_data['current_step'] = 'profile_check'
            request.session['pending_plan_request'] = plan_data
            return redirect('gym:plan_request_flow', step='profile_check')
        except (UserProfile.DoesNotExist, BodyInformationUser.DoesNotExist):
            # Need to fill body information
            messages.warning(request, 'لطفاً اطلاعات بدنی خود را تکمیل کنید.')
            return redirect('gym:body_information_form')
    
    # Handle Step 3: Profile completeness check
    elif step == 'profile_check':
        try:
            user_profile = request.user.userprofile
            is_complete, missing_field = is_profile_complete_for_payment(user_profile)
            
            if is_complete:
                # Profile is complete, move to payment
                plan_data['current_step'] = 'payment'
                request.session['pending_plan_request'] = plan_data
                return redirect('gym:plan_request_flow', step='payment')
            else:
                # Need to complete profile
                messages.warning(request, f'لطفاً اطلاعات پروفایل خود را کامل کنید. فیلد "{missing_field}" خالی است.')
                request.session['payment_redirect_url'] = 'gym:plan_request_flow'
                request.session['payment_redirect_step'] = 'payment'
                return redirect('gym:edit_profile')
        except UserProfile.DoesNotExist:
            messages.error(request, 'پروفایل شما یافت نشد.')
            return redirect('gym:profile')
    
    # Handle Step 4: Payment
    elif step == 'payment':
        return redirect('gym:plan_request_payment')
    
    # Default context for progress display
    context = {
        'steps': STEPS,
        'current_step': step,
        'step_data': STEPS[step],
        'plan_data': plan_data
    }
    return render(request, 'gym/plan_request_flow.html', context)

@login_required
@staff_member_required
def plan_request_management_detail(request, request_id):
    """Comprehensive management view for a single plan request"""
    plan_request = get_object_or_404(PlanRequest, id=request_id)
    
    # Get related data
    user_profile = plan_request.user.userprofile
    
    # Get user's payment for this plan type
    payment_type = 'workout_plan' if plan_request.plan_type == 'workout' else 'diet_plan'
    related_payments = Payment.objects.filter(
        user=plan_request.user,
        payment_type=payment_type
    ).order_by('-payment_date')
    
    # Get body information
    try:
        body_info = user_profile.body_information
    except BodyInformationUser.DoesNotExist:
        body_info = None
    
    # Get existing plans for this user and type
    if plan_request.plan_type == 'workout':
        existing_plans = WorkoutPlan.objects.filter(user=plan_request.user).order_by('-created_at')
    else:
        existing_plans = DietPlan.objects.filter(user=plan_request.user).order_by('-created_at')
    
    # Handle form submission
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve_payment':
            payment_id = request.POST.get('payment_id')
            payment = get_object_or_404(Payment, id=payment_id)
            payment.status = 'approved'
            payment.admin_note = request.POST.get('admin_note', '')
            payment.save()
            messages.success(request, 'پرداخت تایید شد.')
            
        elif action == 'reject_payment':
            payment_id = request.POST.get('payment_id')
            payment = get_object_or_404(Payment, id=payment_id)
            payment.status = 'rejected'
            payment.admin_note = request.POST.get('admin_note', '')
            payment.save()
            messages.success(request, 'پرداخت رد شد.')
            
        elif action == 'approve_request':
            plan_request.status = 'approved'
            plan_request.admin_response = request.POST.get('admin_response', '')
            plan_request.save()
            messages.success(request, 'درخواست تایید شد.')
            
        elif action == 'reject_request':
            plan_request.status = 'rejected'
            plan_request.admin_response = request.POST.get('admin_response', '')
            plan_request.save()
            messages.success(request, 'درخواست رد شد.')
            
        elif action == 'complete_request':
            plan_request.status = 'completed'
            plan_request.save()
            messages.success(request, 'درخواست به عنوان تکمیل شده علامت‌گذاری شد.')
        
        return redirect('gym:plan_request_management_detail', request_id=request_id)
    
    context = {
        'plan_request': plan_request,
        'user_profile': user_profile,
        'body_info': body_info,
        'related_payments': related_payments,
        'existing_plans': existing_plans,
        'is_profile_complete': is_profile_complete_for_payment(user_profile)[0],
    }
    
    return render(request, 'gym/admin/plan_request_management_detail.html', context)

@login_required
@staff_member_required
def update_payment_status(request, payment_id):
    """Update payment status (approve/reject)"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        admin_note = request.POST.get('admin_note', '')
        
        if status in ['approved', 'rejected']:
            payment.status = status
            payment.admin_note = admin_note
            payment.save()
            
            status_display = "تایید شد" if status == "approved" else "رد شد"
            messages.success(request, f'پرداخت {status_display}.')
    
    # Redirect back to referring page
    return redirect(request.META.get('HTTP_REFERER', 'gym:payments'))

@login_required
@staff_member_required
def comprehensive_plan_management(request):
    """Main dashboard for plan management with all functionalities"""
    
    # Get filter parameters
    plan_type = request.GET.get('plan_type', '')
    status = request.GET.get('status', '')
    payment_status = request.GET.get('payment_status', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset with related data
    plan_requests = PlanRequest.objects.select_related('user', 'user__userprofile').prefetch_related(
        'user__payments'
    ).all().order_by('-created_at')
    
    # Apply filters
    if plan_type:
        plan_requests = plan_requests.filter(plan_type=plan_type)
    
    if status:
        plan_requests = plan_requests.filter(status=status)
    
    if search_query:
        plan_requests = plan_requests.filter(
            Q(description__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__userprofile__name__icontains=search_query)
        )
    
    # Filter by payment status if specified
    if payment_status:
        user_ids_with_payment_status = Payment.objects.filter(
            status=payment_status,
            payment_type__in=['workout_plan', 'diet_plan']
        ).values_list('user_id', flat=True)
        plan_requests = plan_requests.filter(user_id__in=user_ids_with_payment_status)
    
    # Prepare data for each request
    request_data = []
    for req in plan_requests:
        payment_type = 'workout_plan' if req.plan_type == 'workout' else 'diet_plan'
        latest_payment = req.user.payments.filter(payment_type=payment_type).first()
        
        # Check body information
        try:
            body_info_exists = hasattr(req.user.userprofile, 'body_information') and req.user.userprofile.body_information is not None
        except:
            body_info_exists = False
        
        # Check profile completeness
        profile_complete = is_profile_complete_for_payment(req.user.userprofile)[0]
        
        # Get existing plans count
        if req.plan_type == 'workout':
            plans_count = WorkoutPlan.objects.filter(user=req.user).count()
        else:
            plans_count = DietPlan.objects.filter(user=req.user).count()
        
        request_data.append({
            'request': req,
            'latest_payment': latest_payment,
            'body_info_exists': body_info_exists,
            'profile_complete': profile_complete,
            'plans_count': plans_count,
        })
    
    context = {
        'request_data': request_data,
        'plan_type': plan_type,
        'status': status,
        'payment_status': payment_status,
        'search_query': search_query,
    }
    
    return render(request, 'gym/admin/comprehensive_plan_management.html', context)

@login_required
@staff_member_required
def test_email_notifications(request):
    """Test email notification system"""
    if request.method == 'POST':
        notification_type = request.POST.get('notification_type')
        
        try:
            from gym.utils.email_notifications import EmailNotificationService
            
            if notification_type == 'test_config':
                # Test basic email configuration
                success = EmailNotificationService.test_email_configuration()
                if success:
                    messages.success(request, 'تست اطلاع‌رسانی ایمیل موفق بود! ایمیل تست ارسال شد.')
                else:
                    messages.error(request, 'خطا در ارسال ایمیل تست. لطفاً تنظیمات ایمیل را بررسی کنید.')
            
            elif notification_type == 'create_default_settings':
                # Create default notification settings for current admin
                settings_obj = EmailNotificationService.create_default_notification_settings(request.user)
                if settings_obj:
                    messages.success(request, 'تنظیمات پیش‌فرض اطلاع‌رسانی ایمیل ایجاد شد.')
                else:
                    messages.error(request, 'خطا در ایجاد تنظیمات اطلاع‌رسانی.')
            
        except Exception as e:
            messages.error(request, f'خطا در انجام تست: {str(e)}')
    
    # Get current notification settings
    from gym.models import EmailNotificationSettings
    
    try:
        current_settings = EmailNotificationSettings.objects.get(admin_user=request.user)
    except EmailNotificationSettings.DoesNotExist:
        current_settings = None
    
    # Get all admin notification settings
    all_settings = EmailNotificationSettings.objects.all().select_related('admin_user')
    
    context = {
        'current_settings': current_settings,
        'all_settings': all_settings,
    }
    
    return render(request, 'gym/admin/test_email_notifications.html', context)
