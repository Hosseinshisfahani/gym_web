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
    ProgressAnalysisForm
)
from .models import (
    UserProfile, WorkoutPlan, DietPlan, 
    Payment, Ticket, TicketResponse, Document, PlanRequest,
    BodyAnalysisReport, MonthlyGoal, ProgressAnalysis
)
from django.db.models import Q, Avg
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
        
        # Try to find the user by their name
        try:
            # First, get the profile by name
            profile = UserProfile.objects.get(name=name)
            # Then, get the user object
            user = profile.user
            # Finally, authenticate with username (phone_number) and password
            authenticated_user = authenticate(request, username=user.username, password=password)
            
            if authenticated_user is not None:
                login(request, authenticated_user)
                return redirect('gym:profile')
            else:
                messages.error(request, 'نام یا رمز عبور نامعتبر است.')
        except UserProfile.DoesNotExist:
            messages.error(request, 'کاربری با این نام یافت نشد.')
        except UserProfile.MultipleObjectsReturned:
            # In case there are multiple users with the same name
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
    
    # Get most recent progress data for quick view
    recent_progress = ProgressAnalysis.objects.filter(user=user).order_by('-measurement_date')[:5]
    
    context = {
        'user_profile': user_profile,
        'is_own_profile': not user_id or user_id == request.user.id,
        'stats': stats,
        'recent_progress': recent_progress,
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
                    return redirect('gym:add_workout_plan')
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
                    return redirect('gym:add_diet_plan')
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
    """View for submitting a new plan request (workout or diet)"""
    if request.method == 'POST':
        plan_type = request.POST.get('plan_type')
        description = request.POST.get('description')
        
        if plan_type in ['workout', 'diet'] and description:
            # Create a new plan request
            plan_request = PlanRequest.objects.create(
                user=request.user,
                plan_type=plan_type,
                description=description
            )
            
            messages.success(request, 'درخواست شما با موفقیت ثبت شد و در انتظار بررسی است.')
            
            # Redirect to appropriate page based on plan type
            if plan_type == 'workout':
                return redirect('gym:workout_plans')
            else:
                return redirect('gym:diet_plans')
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
    else:
        # For regular users, get only their payments
        payments = Payment.objects.filter(user=request.user).order_by('-payment_date')
    
    return render(request, 'gym/payments.html', {
        'payments': payments,
        'is_admin': request.user.is_staff
    })

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
    if not user_profile.post_code:
        return False, 'کد پستی'
    
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
            
        context = {
            'goals': goals,
            'status': status,
            'user_id': user_id,
            'search_query': search_query,
            'is_admin': True
        }
        
        return render(request, 'gym/admin/monthly_goals.html', context)
    
    else:
        # For regular users, get only their goals
        goals = MonthlyGoal.objects.filter(user=request.user).order_by('-start_date')
        
        if request.method == 'POST':
            form = MonthlyGoalForm(request.POST)
            if form.is_valid():
                goal = form.save(commit=False)
                goal.user = request.user
                goal.status = 'not_started'  # Default status for new goals
                goal.save()
                messages.success(request, 'هدف ماهانه جدید با موفقیت ثبت شد.')
                return redirect('gym:monthly_goals')
        else:
            form = MonthlyGoalForm()
        
        context = {
            'goals': goals,
            'form': form
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

# Progress Analysis
@login_required
def progress_analysis(request):
    """View and manage progress measurements for a user or all progress for admin"""
    
    if request.user.is_staff:
        # For admin, get all progress measurements with filters
        progress_data = ProgressAnalysis.objects.all().order_by('-measurement_date')
        
        # Get filter parameters
        measurement_type = request.GET.get('measurement_type')
        user_id = request.GET.get('user_id')
        search_query = request.GET.get('search', '')
        
        # Apply filters
        if measurement_type:
            progress_data = progress_data.filter(measurement_type=measurement_type)
        
        if user_id:
            progress_data = progress_data.filter(user_id=user_id)
        
        if search_query:
            progress_data = progress_data.filter(
                Q(user__username__icontains=search_query) |
                Q(user__userprofile__name__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
            
        context = {
            'progress_data': progress_data,
            'measurement_type': measurement_type,
            'user_id': user_id,
            'search_query': search_query,
            'is_admin': True
        }
        
        return render(request, 'gym/admin/progress_analysis.html', context)
    
    else:
        # For regular users, get only their progress data
        progress_data = ProgressAnalysis.objects.filter(user=request.user).order_by('-measurement_date')
        
        # Group data by measurement type for charts
        chart_data = {}
        measurement_types = ProgressAnalysis.MEASUREMENT_TYPES
        
        for m_type, m_label in measurement_types:
            type_data = progress_data.filter(measurement_type=m_type).order_by('measurement_date')
            if type_data.exists():
                chart_data[m_type] = {
                    'label': m_label,
                    'dates': [entry.measurement_date.strftime('%Y-%m-%d') for entry in type_data],
                    'values': [float(entry.value) for entry in type_data],
                    'unit': type_data.first().unit
                }
        
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
        
        context = {
            'progress_data': progress_data,
            'chart_data': json.dumps(chart_data),
            'form': form
        }
        
        return render(request, 'gym/progress_analysis.html', context)

@login_required
def delete_progress_entry(request, entry_id):
    """Delete a progress analysis entry"""
    entry = get_object_or_404(ProgressAnalysis, id=entry_id)
    
    # Check permissions
    if not request.user.is_staff and request.user != entry.user:
        messages.error(request, 'شما دسترسی لازم برای حذف این اندازه‌گیری را ندارید.')
        return redirect('gym:progress_analysis')
    
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'اندازه‌گیری با موفقیت حذف شد.')
        
    return redirect('gym:progress_analysis')
