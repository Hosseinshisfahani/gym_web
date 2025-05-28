from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, FileResponse, StreamingHttpResponse, HttpResponseForbidden, JsonResponse
from .forms import (
    UserRegistrationForm, UserProfileForm, WorkoutPlanForm, 
    DietPlanForm, CertificateForm, PaymentForm, TicketForm,
    TicketResponseForm, DocumentForm, BookletForm, BookletPaymentForm,
    PlanRequestForm
)
from .models import (
    UserProfile, WorkoutPlan, DietPlan, Certificate, 
    Attendance, Payment, Ticket, TicketResponse, Document, CertificateComment,
    Booklet, BookletPayment, PlanRequest
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
                
            # Set password fields to melli_code before saving
            form.cleaned_data['password1'] = form.cleaned_data['melli_code']
            form.cleaned_data['password2'] = form.cleaned_data['melli_code']
            user = form.save()
            
            # Mark the agreement as accepted in the user profile
            profile = user.userprofile
            profile.agreement_accepted = True
            profile.save()
            
            login(request, user)
            messages.success(request, 'ثبت نام با موفقیت انجام شد. رمز عبور شما همان کد ملی شما می‌باشد. می‌توانید از طریق صفحه پروفایل آن را تغییر دهید.')
            return redirect('gym:profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'gym/register.html', {'form': form})

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('gym:profile')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور نامعتبر است. لطفاً مطمئن شوید که از کد ملی خود به عنوان نام کاربری و رمز عبور استفاده می‌کنید.')
            # Debug message to check input
            messages.info(request, f'ورودی‌ها - نام کاربری: {username}')
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
    
    context = {
        'user_profile': user_profile,
        'is_own_profile': not user_id or user_id == request.user.id,
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
                Q(user__userprofile__full_name__icontains=search_query)
            )
            plan_requests = plan_requests.filter(
                Q(user__username__icontains=search_query) |
                Q(user__userprofile__full_name__icontains=search_query) |
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
        full_name = plan.user.userprofile.full_name if hasattr(plan.user, 'userprofile') else plan.user.username
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
                Q(user__userprofile__full_name__icontains=search_query)
            )
            plan_requests = plan_requests.filter(
                Q(user__username__icontains=search_query) |
                Q(user__userprofile__full_name__icontains=search_query) |
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
        full_name = plan.user.userprofile.full_name if hasattr(plan.user, 'userprofile') else plan.user.username
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

# Certificate views
@login_required
def certificates(request):
    certificates = Certificate.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'gym/certificates.html', {
        'certificates': certificates
    })

@login_required
def add_certificate(request):
    if request.method == 'POST':
        try:
            certificate = Certificate.objects.create(
                user=request.user,
                title=request.POST.get('title'),
                image=request.FILES.get('image'),
                issue_date=request.POST.get('issue_date'),
                description=request.POST.get('description'),
                status='pending'  # Default status is pending
            )
            messages.success(request, 'گواهی شما با موفقیت آپلود شد و در انتظار تایید است.')
        except Exception as e:
            messages.error(request, 'خطا در آپلود گواهی. لطفا دوباره تلاش کنید.')
    
    return redirect('gym:certificates')

@login_required
def add_certificate_comment(request, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            CertificateComment.objects.create(
                certificate=certificate,
                user=request.user,
                message=message
            )
            messages.success(request, 'نظر شما با موفقیت ثبت شد.')
        else:
            messages.error(request, 'لطفا متن نظر را وارد کنید.')
    
    return redirect('gym:certificates')

@login_required
def manage_certificates(request):
    if not request.user.is_staff:
        messages.error(request, 'شما دسترسی لازم برای مدیریت گواهینامه‌ها را ندارید.')
        return redirect('gym:profile')
    
    certificates = Certificate.objects.all().order_by('-created_at')
    return render(request, 'gym/manage_certificates.html', {
        'certificates': certificates
    })

@login_required
def update_certificate_status(request, certificate_id):
    if not request.user.is_staff:
        messages.error(request, 'شما دسترسی لازم برای مدیریت گواهینامه‌ها را ندارید.')
        return redirect('gym:profile')
    
    try:
        certificate = Certificate.objects.get(id=certificate_id)
        if request.method == 'POST':
            status = request.POST.get('status')
            approval_message = request.POST.get('approval_message', '')
            
            if status in ['approved', 'rejected']:
                certificate.status = status
                certificate.approval_message = approval_message
                certificate.save()
                
                if status == 'approved':
                    messages.success(request, f'گواهی "{certificate.title}" با موفقیت تایید شد.')
                else:
                    messages.warning(request, f'گواهی "{certificate.title}" رد شد.')
            else:
                messages.error(request, 'وضعیت نامعتبر است.')
    except Certificate.DoesNotExist:
        messages.error(request, 'گواهی مورد نظر یافت نشد.')
    
    return redirect('gym:manage_certificates')

# Attendance views
@login_required
def attendance(request):
    user_profile = request.user.userprofile
    context = {}
    
    # Admin view
    if request.user.is_staff:
        # Get filter parameters
        selected_date = request.GET.get('date', timezone.now().date().isoformat())
        selected_class = request.GET.get('class')
        search_query = request.GET.get('search', '')
        
        # Get all classes for filtering
        classes = Class.objects.all()
        
        # Base queryset
        attendances = Attendance.objects.select_related('user_profile').all()
        
        # Apply filters
        if selected_date:
            attendances = attendances.filter(date=selected_date)
        
        if selected_class:
            attendances = attendances.filter(user_profile__class_obj_id=selected_class)
        
        if search_query:
            attendances = attendances.filter(
                Q(user_profile__full_name__icontains=search_query) |
                Q(user_profile__melli_code__icontains=search_query)
            )
        
        # Group attendances by class
        attendance_by_class = {}
        for attendance in attendances:
            class_name = 'بدون کلاس'
            if hasattr(attendance.user_profile, 'class_obj'):
                class_name = attendance.user_profile.class_obj.name
            if class_name not in attendance_by_class:
                attendance_by_class[class_name] = []
            attendance_by_class[class_name].append(attendance)
        
        # Calculate statistics
        total_students = attendances.values('user_profile').distinct().count()
        present_count = attendances.filter(present=True).count()
        absent_count = total_students - present_count
        
        # Handle attendance update
        if request.method == 'POST':
            try:
                attendance_id = request.POST.get('attendance_id')
                present = request.POST.get('present') == 'true'
                description = request.POST.get('description', '')
                
                attendance = Attendance.objects.get(id=attendance_id)
                attendance.present = present
                attendance.description = description
                attendance.save()
                
                messages.success(request, 'وضعیت حضور و غیاب با موفقیت به‌روزرسانی شد.')
            except Exception as e:
                messages.error(request, f'خطا در به‌روزرسانی حضور و غیاب: {str(e)}')
            
            return redirect('gym:attendance')
        
        context.update({
            'attendances': attendances,
            'attendance_by_class': attendance_by_class,
            'classes': classes,
            'selected_date': selected_date,
            'selected_class': selected_class,
            'search_query': search_query,
            'is_admin': True,
            'total_students': total_students,
            'present_count': present_count,
            'absent_count': absent_count,
        })
    
    # Student view
    else:
        # Get student's attendance records
        attendances = Attendance.objects.filter(
            user_profile=user_profile
        ).order_by('-date')
        
        # Calculate statistics
        total_days = attendances.count()
        present_days = attendances.filter(present=True).count()
        absent_days = total_days - present_days
        attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        # Get monthly attendance
        monthly_attendance = {}
        for attendance in attendances:
            month = attendance.date.strftime('%Y-%m')
            if month not in monthly_attendance:
                monthly_attendance[month] = {'present': 0, 'total': 0}
            monthly_attendance[month]['total'] += 1
            if attendance.present:
                monthly_attendance[month]['present'] += 1
        
        context.update({
            'attendances': attendances,
            'is_admin': False,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'attendance_percentage': attendance_percentage,
            'monthly_attendance': monthly_attendance,
        })
    
    return render(request, 'gym/attendance.html', context)

# Payment views
@login_required
def payments(request):
    # Get regular payments
    if request.user.is_staff:
        # For admin users, get all payments
        regular_payments = Payment.objects.all().order_by('-date')
        booklet_payments = BookletPayment.objects.all().order_by('-created_at')
    else:
        # For regular users, get only their payments
        regular_payments = Payment.objects.filter(user=request.user).order_by('-date')
        booklet_payments = BookletPayment.objects.filter(user=request.user).order_by('-created_at')
    
    # Combine all types of payments
    all_payments = []
    
    # Add regular payments
    for payment in regular_payments:
        all_payments.append({
            'type': 'regular',
            'date': payment.date,
            'amount': payment.amount,
            'description': payment.description,
            'status': payment.status,
            'receipt': payment.payment_image,
            'created_at': payment.date,
            'user': payment.user.username if request.user.is_staff else None
        })
    
    # Add booklet payments
    for payment in booklet_payments:
        all_payments.append({
            'type': 'booklet',
            'date': payment.created_at.date(),
            'amount': payment.amount,
            'description': f'خرید جزوه: {payment.booklet.title}',
            'status': payment.status,
            'receipt': payment.payment_image,
            'created_at': payment.created_at,
            'user': payment.user.username if request.user.is_staff else None
        })
    
    # Sort all payments by date (newest first)
    all_payments.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render(request, 'gym/payments.html', {
        'payments': all_payments,
        'is_admin': request.user.is_staff
    })

@login_required
def add_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.save()
            messages.success(request, 'Payment record added successfully!')
            return redirect('gym:payments')
    else:
        form = PaymentForm()
    
    return render(request, 'gym/add_payment.html', {'form': form})

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
                Q(user__userprofile__full_name__icontains=search_query)
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
        messages.error(request, "You don't have permission to access this page.")
        return redirect('gym:home')
    
    users = User.objects.all().order_by('username')
    return render(request, 'gym/admin/user_management.html', {'users': users})

@login_required
@staff_member_required
def attendance_management(request):
    # Get the date from the request or use today's date
    date_param = request.GET.get('date')
    attendance_date = None
    
    # Handle empty or invalid date parameter
    if date_param and date_param.strip():
        try:
            attendance_date = datetime.datetime.strptime(date_param, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            attendance_date = timezone.now().date()
    else:
        attendance_date = timezone.now().date()
    
    # Get class filter
    selected_class = request.GET.get('class')
    
    # Get all classes for filtering
    classes = Class.objects.all().order_by('name')
    
    # Get all users with their profiles
    users = User.objects.select_related('userprofile').all()
    
    # Filter users by class if selected
    if selected_class:
        try:
            class_obj = Class.objects.get(id=selected_class)
            # Filter users who are in the selected class
            users = users.filter(enrolled_classes=class_obj)
        except Class.DoesNotExist:
            pass
    
    # Get attendance records for the selected date
    attendance_records = {
        record.user_profile.user.id: record
        for record in Attendance.objects.filter(date=attendance_date)
    }
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        date = request.POST.get('date')
        present = request.POST.get('present') == 'true'
        
        # Validate the date
        post_date = None
        try:
            post_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            post_date = timezone.now().date()
        
        try:
            user = User.objects.get(id=user_id)
            user_profile = user.userprofile
            attendance, created = Attendance.objects.get_or_create(
                user_profile=user_profile,
                date=post_date,
                defaults={'present': present}
            )
            
            if not created:
                attendance.present = present
                attendance.save()
            
            messages.success(request, f'وضعیت حضور و غیاب برای {user_profile.full_name} به‌روزرسانی شد.')
            
            # Redirect with the same filters to maintain state
            redirect_url = f'?date={post_date}'
            if selected_class:
                redirect_url += f'&class={selected_class}'
            return redirect(f'{request.path}{redirect_url}')
        except Exception as e:
            messages.error(request, f'خطا در به‌روزرسانی حضور و غیاب: {str(e)}')
        
        return redirect('gym:attendance_management')
    
    return render(request, 'gym/admin/attendance.html', {
        'users': users,
        'attendance_records': attendance_records,
        'attendance_date': attendance_date,
        'classes': classes,
        'selected_class': selected_class
    })

@login_required
def admin_plans(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('gym:home')
    
    workout_plans = WorkoutPlan.objects.all().order_by('-created_at')
    diet_plans = DietPlan.objects.all().order_by('-created_at')
    

    context = {
        'workout_plans': workout_plans,
        'diet_plans': diet_plans,
    }
    
    return render(request, 'gym/admin/plans.html', context)

@login_required
def booklets(request):
    if request.user.is_staff:
        booklets = Booklet.objects.all()
        if request.method == 'POST':
            form = BookletForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, 'جزوه با موفقیت اضافه شد.')
                return redirect('gym:booklets')
        else:
            form = BookletForm()
        return render(request, 'gym/booklets.html', {'booklets': booklets, 'form': form})
    else:
        booklets = Booklet.objects.filter(is_active=True)
        return render(request, 'gym/booklets.html', {'booklets': booklets})

@login_required
def booklet_detail(request, booklet_id):
    booklet = get_object_or_404(Booklet, id=booklet_id)
    
    # Check if user has paid for this booklet
    has_paid = BookletPayment.objects.filter(
        user=request.user,
        booklet=booklet,
        status='approved'
    ).exists()
    
    if request.method == 'POST' and not request.user.is_staff:
        form = BookletPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.booklet = booklet
            payment.status = 'pending'
            payment.save()
            messages.success(request, 'درخواست پرداخت با موفقیت ثبت شد.')
            return redirect('gym:booklet_detail', booklet_id=booklet_id)
    else:
        form = BookletPaymentForm()
    
    return render(request, 'gym/booklet_detail.html', {
        'booklet': booklet,
        'form': form,
        'has_paid': has_paid or request.user.is_staff
    })

@login_required
@staff_member_required
def booklet_payments(request, booklet_id):
    booklet = get_object_or_404(Booklet, id=booklet_id)
    payments = BookletPayment.objects.filter(booklet=booklet).select_related('user')
    
    context = {
        'booklet': booklet,
        'payments': payments,
    }
    return render(request, 'gym/booklet_payments.html', context)

@login_required
@staff_member_required
def update_payment_status(request, payment_id):
    payment = get_object_or_404(BookletPayment, id=payment_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['pending', 'approved', 'rejected']:
            payment.status = status
            payment.save()
            messages.success(request, 'وضعیت پرداخت با موفقیت به‌روزرسانی شد.')
    return redirect('gym:booklet_payments', booklet_id=payment.booklet.id)

@login_required
@staff_member_required
def edit_booklet(request, booklet_id):
    booklet = get_object_or_404(Booklet, id=booklet_id)
    if request.method == 'POST':
        form = BookletForm(request.POST, request.FILES, instance=booklet)
        if form.is_valid():
            form.save()
            messages.success(request, 'جزوه با موفقیت ویرایش شد.')
            return redirect('gym:booklet_detail', booklet_id=booklet.id)
    else:
        form = BookletForm(instance=booklet)
    return render(request, 'gym/edit_booklet.html', {
        'form': form,
        'booklet': booklet
    })

@login_required
def payment_upload(request, product_id=None):
    # Get the product (booklet) information
    booklet = get_object_or_404(Booklet, id=product_id)
    
    # Check if the user has already paid for this booklet
    existing_payment = BookletPayment.objects.filter(
        user=request.user,
        booklet=booklet
    ).first()
    
    if existing_payment:
        if existing_payment.status == 'approved':
            messages.warning(request, 'شما قبلا برای این جزوه پرداخت موفق داشته‌اید.')
            return redirect('gym:booklet_detail', booklet_id=booklet.id)
        elif existing_payment.status == 'pending':
            messages.warning(request, 'پرداخت قبلی شما برای این جزوه در انتظار تایید است.')
            return redirect('gym:booklet_detail', booklet_id=booklet.id)
        # If the payment was rejected, we'll allow them to try again
    
    if request.method == 'POST':
        # Handle existing payment case
        if existing_payment and existing_payment.status == 'rejected':
            # Update existing payment instead of creating a new one
            existing_payment.status = 'pending'
            
            # Update description if provided
            if request.POST.get('description'):
                existing_payment.description = request.POST.get('description')
            
            # Update receipt if uploaded
            if 'receipt' in request.FILES:
                existing_payment.payment_image = request.FILES['receipt']
                
            existing_payment.save()
            messages.success(request, 'رسید پرداخت شما با موفقیت آپلود شد و در انتظار تایید است.')
            return redirect('gym:booklets')
        else:
            # Create a new payment record
            try:
                payment = BookletPayment(
                    user=request.user,
                    booklet=booklet,
                    amount=booklet.price,
                    status='pending',
                    description=request.POST.get('description', '')
                )
                
                # Handle the receipt image upload
                if 'receipt' in request.FILES:
                    payment.payment_image = request.FILES['receipt']
                    payment.save()
                    messages.success(request, 'رسید پرداخت شما با موفقیت آپلود شد و در انتظار تایید است.')
                    return redirect('gym:booklets')
                else:
                    messages.error(request, 'لطفاً تصویر رسید پرداخت را آپلود کنید.')
            except Exception as e:
                messages.error(request, f'خطا در ثبت پرداخت: {str(e)}')
    
    context = {
        'product_name': booklet.title,
        'price': booklet.price,
    }
    return render(request, 'gym/payment_upload.html', context)

@login_required
def view_pdf(request, booklet_id):
    booklet = get_object_or_404(Booklet, id=booklet_id)
    
    # Check if user has paid for this booklet
    has_paid = BookletPayment.objects.filter(
        user=request.user,
        booklet=booklet,
        status='approved'
    ).exists()
    
    # Check if user has access
    if not request.user.is_staff and not has_paid:
        messages.error(request, 'شما دسترسی لازم برای مشاهده این جزوه را ندارید.')
        return redirect('gym:booklets')
    
    context = {
        'booklet': booklet,
    }
    return render(request, 'gym/pdf_viewer.html', context)

@login_required
def stream_pdf(request, booklet_id):
    booklet = get_object_or_404(Booklet, id=booklet_id)
    
    # Check if user has paid for this booklet
    has_paid = BookletPayment.objects.filter(
        user=request.user,
        booklet=booklet,
        status='approved'
    ).exists()
    
    # Check if user has access
    if not request.user.is_staff and not has_paid:
        return HttpResponseForbidden('شما دسترسی لازم برای مشاهده این جزوه را ندارید.')
    
    # Get the PDF file path
    pdf_path = booklet.file.path
    
    def file_iterator(file_path, chunk_size=8192):
        with open(file_path, "rb") as pdf_file:
            while chunk := pdf_file.read(chunk_size):
                yield chunk
    
    response = StreamingHttpResponse(
        file_iterator(pdf_path),
        content_type="application/pdf"
    )
    
    # Prevent download by setting inline content disposition
    response["Content-Disposition"] = "inline"
    # Prevent embedding in iframes
    response["X-Frame-Options"] = "DENY"
    # Add cache control headers
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    
    return response

@login_required
def log_screenshot_attempt(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            booklet_id = data.get('booklet_id')
            user = request.user
            
            # Log the attempt (you can store this in your database)
            print(f"Screenshot attempt detected - User: {user.username}, Booklet ID: {booklet_id}")
            
            return JsonResponse({'status': 'logged'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
def submit_feedback(request):
    if request.method == 'POST':
        try:
            issue_type = request.POST.get('issue_type')
            description = request.POST.get('description')
            
            # Log the feedback (you can store this in your database)
            print(f"Feedback received - User: {request.user.username}, Type: {issue_type}, Description: {description}")
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
def search_users(request):
    """
    API endpoint to search for users by username, first name, last name, or email.
    Only accessible by staff members.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) | 
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query) | 
        Q(email__icontains=query)
    )[:20]  # Limit to 20 results
    
    users_data = []
    for user in users:
        try:
            full_name = user.userprofile.full_name if hasattr(user, 'userprofile') else ""
        except UserProfile.DoesNotExist:
            full_name = ""
            
        users_data.append({
            'id': user.id,
            'username': user.username,
            'full_name': full_name or user.username,
            'email': user.email
        })
    
    return JsonResponse({'users': users_data})

@login_required
def request_plan(request):
    if request.method == 'POST':
        form = PlanRequestForm(request.POST)
        if form.is_valid():
            plan_request = form.save(commit=False)
            plan_request.user = request.user
            plan_request.save()
            
            messages.success(request, 'درخواست شما با موفقیت ثبت شد.')
            
            # Redirect based on plan type
            if plan_request.plan_type == 'workout':
                return redirect('gym:workout_plans')
            else:
                return redirect('gym:diet_plans')
    
    return redirect('gym:workout_plans')  # Default redirect

@login_required
def manage_plan_requests(request):
    if not request.user.is_staff:
        messages.error(request, 'شما دسترسی لازم برای این صفحه را ندارید.')
        return redirect('gym:home')
    
    # Get filter parameters
    plan_type = request.GET.get('plan_type')
    status = request.GET.get('status')
    
    # Start with all requests
    plan_requests = PlanRequest.objects.all().order_by('-created_at')
    
    # Apply filters if provided
    if plan_type:
        plan_requests = plan_requests.filter(plan_type=plan_type)
    if status:
        plan_requests = plan_requests.filter(status=status)
    
    context = {
        'plan_requests': plan_requests,
    }
    return render(request, 'gym/admin/manage_plan_requests.html', context)

@login_required
def update_plan_request(request, request_id):
    if not request.user.is_staff:
        messages.error(request, 'شما دسترسی لازم برای این عملیات را ندارید.')
        return redirect('gym:home')
    
    plan_request = get_object_or_404(PlanRequest, id=request_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        admin_response = request.POST.get('admin_response')
        
        if status in ['approved', 'rejected']:
            plan_request.status = status
            plan_request.admin_response = admin_response
            plan_request.save()
            
            # Send appropriate message
            status_msg = 'تایید' if status == 'approved' else 'رد'
            messages.success(request, f'درخواست با موفقیت {status_msg} شد.')
            
            # If approved, redirect to create plan page
            if status == 'approved':
                if plan_request.plan_type == 'workout':
                    return redirect('gym:add_workout_plan_for_user', user_id=plan_request.user.id)
                else:
                    return redirect('gym:add_diet_plan_for_user', user_id=plan_request.user.id)
    
    return redirect('gym:manage_plan_requests')

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
