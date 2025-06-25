from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True, verbose_name='عکس پروفایل')
    name = models.CharField(max_length=200, blank=True, null=True, verbose_name='نام')
    melli_code = models.CharField(max_length=10, unique=True, null=True, blank=True, verbose_name='کد ملی')
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name='شماره تلفن')
    post_code = models.CharField(max_length=10, blank=True, null=True, verbose_name='کد پستی')
    home_address = models.TextField(blank=True, null=True, verbose_name='آدرس منزل')
    agreement_accepted = models.BooleanField(default=False, verbose_name='توافقنامه پذیرفته شده')
    
    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'
    
    def __str__(self):
        return f"{self.name} ({self.melli_code})"

@receiver(post_save, sender=UserProfile)
def update_user_username(sender, instance, created, **kwargs):
    """
    Signal to update the username to match melli_code when UserProfile is created or updated,
    but only if the username is still available or already belongs to this user
    """
    if instance.melli_code and instance.user.username != instance.melli_code:
        # Check if any other user already has this username
        if not User.objects.exclude(id=instance.user.id).filter(username=instance.melli_code).exists():
            instance.user.username = instance.melli_code
            instance.user.save()
        else:
            # Log that we couldn't update the username due to a conflict
            print(f"Cannot update username to {instance.melli_code} for user {instance.user.id} due to conflict")

class WorkoutPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_plans')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    image = models.ImageField(upload_to='workout_plans/images/', blank=True, null=True, verbose_name='تصویر برنامه')
    plan_file = models.FileField(upload_to='workout_plans/', blank=True, null=True, verbose_name='فایل برنامه')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    duration_weeks = models.PositiveIntegerField(default=4, verbose_name='مدت (هفته)')
    start_date = models.DateField(default=timezone.now, verbose_name='تاریخ شروع')
    end_date = models.DateField(blank=True, null=True, verbose_name='تاریخ پایان')
    
    class Meta:
        verbose_name = 'برنامه تمرینی'
        verbose_name_plural = 'برنامه‌های تمرینی'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Calculate end date based on start date and duration
        if self.start_date and self.duration_weeks:
            self.end_date = self.start_date + datetime.timedelta(weeks=self.duration_weeks)
        super().save(*args, **kwargs)

class DietPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diet_plans')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    image = models.ImageField(upload_to='diet_plans/images/', blank=True, null=True, verbose_name='تصویر برنامه')
    plan_file = models.FileField(upload_to='diet_plans/', blank=True, null=True, verbose_name='فایل برنامه')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    duration_weeks = models.PositiveIntegerField(default=4, verbose_name='مدت (هفته)')
    start_date = models.DateField(default=timezone.now, verbose_name='تاریخ شروع')
    end_date = models.DateField(blank=True, null=True, verbose_name='تاریخ پایان')
    
    class Meta:
        verbose_name = 'برنامه غذایی'
        verbose_name_plural = 'برنامه‌های غذایی'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Calculate end date based on start date and duration
        if self.start_date and self.duration_weeks:
            self.end_date = self.start_date + datetime.timedelta(weeks=self.duration_weeks)
        super().save(*args, **kwargs)

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'در انتظار تایید'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    ]
    PAYMENT_TYPE_CHOICES = [
        ('membership', 'حق عضویت'),
        ('workout_plan', 'برنامه تمرینی'),
        ('diet_plan', 'برنامه غذایی'),
        ('other', 'سایر'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.PositiveIntegerField(verbose_name='مبلغ (تومان)')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='other', verbose_name='نوع پرداخت')
    payment_date = models.DateField(default=timezone.now, verbose_name='تاریخ پرداخت')
    proof_image = models.ImageField(upload_to='payment_proofs/', blank=True, null=True, verbose_name='تصویر رسید پرداخت')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    admin_note = models.TextField(blank=True, null=True, verbose_name='توضیحات مدیر')
    
    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} تومان - {self.get_status_display()}"

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'باز'),
        ('in_progress', 'در حال بررسی'),
        ('closed', 'بسته'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=200, verbose_name='موضوع')
    message = models.TextField(verbose_name='پیام')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open', verbose_name='وضعیت')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    
    class Meta:
        verbose_name = 'تیکت پشتیبانی'
        verbose_name_plural = 'تیکت‌های پشتیبانی'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.user.username}"

class TicketResponse(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_responses')
    message = models.TextField(verbose_name='پیام')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    is_staff = models.BooleanField(default=False, verbose_name='پاسخ کارمند')
    
    class Meta:
        verbose_name = 'پاسخ تیکت'
        verbose_name_plural = 'پاسخ‌های تیکت'
        ordering = ['created_at']
    
    def __str__(self):
        return f"پاسخ به {self.ticket.subject} توسط {self.user.username}"

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('certificate', 'گواهینامه'),
        ('education', 'مدرک تحصیلی'),
        ('medical', 'مدارک پزشکی'),
        ('other', 'سایر'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='other', verbose_name='نوع سند')
    file = models.FileField(upload_to='documents/', verbose_name='فایل')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ آپلود')
    
    class Meta:
        verbose_name = 'سند'
        verbose_name_plural = 'اسناد'
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class PlanRequest(models.Model):
    PLAN_TYPES = [
        ('workout', 'برنامه ورزشی'),
        ('diet', 'برنامه غذایی'),
    ]
    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
        ('completed', 'تکمیل شده'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plan_requests')
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPES, verbose_name='نوع برنامه')
    description = models.TextField(verbose_name='توضیحات')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ درخواست')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    admin_response = models.TextField(blank=True, null=True, verbose_name='پاسخ ادمین')
    
    class Meta:
        verbose_name = 'درخواست برنامه'
        verbose_name_plural = 'درخواست‌های برنامه'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_plan_type_display()} - {self.user.username}"

# New models for the dashboard sections

class BodyAnalysisReport(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('reviewed', 'بررسی شده'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='body_analysis_reports')
    report_date = models.DateField(default=timezone.now, verbose_name='تاریخ آزمایش')
    image = models.ImageField(upload_to='body_analysis/', verbose_name='تصویر آزمایش')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    admin_response = models.TextField(blank=True, null=True, verbose_name='پاسخ مربی')
    response_date = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ پاسخ')
    
    class Meta:
        verbose_name = 'گزارش آنالیز بدن'
        verbose_name_plural = 'گزارش‌های آنالیز بدن'
        ordering = ['-report_date']
    
    def __str__(self):
        return f"آنالیز بدن {self.user.userprofile.name} - {self.report_date}"

class MonthlyGoal(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'شروع نشده'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_goals')
    title = models.CharField(max_length=200, verbose_name='عنوان هدف')
    description = models.TextField(verbose_name='توضیحات')
    start_date = models.DateField(default=timezone.now, verbose_name='تاریخ شروع')
    end_date = models.DateField(verbose_name='تاریخ پایان')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_started', verbose_name='وضعیت')
    progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='پیشرفت (درصد)')
    coach_notes = models.TextField(blank=True, null=True, verbose_name='یادداشت مربی')
    
    class Meta:
        verbose_name = 'هدف ماهانه'
        verbose_name_plural = 'اهداف ماهانه'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} - {self.user.userprofile.name}"

class ProgressAnalysis(models.Model):
    MEASUREMENT_TYPES = [
        ('weight', 'وزن'),
        ('body_fat', 'درصد چربی بدن'),
        ('muscle_mass', 'توده عضلانی'),
        ('waist', 'دور کمر'),
        ('chest', 'دور سینه'),
        ('arm', 'دور بازو'),
        ('thigh', 'دور ران'),
        ('other', 'سایر'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_analyses')
    measurement_type = models.CharField(max_length=20, choices=MEASUREMENT_TYPES, verbose_name='نوع اندازه‌گیری')
    value = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='مقدار')
    unit = models.CharField(max_length=10, default='kg', verbose_name='واحد')
    measurement_date = models.DateField(default=timezone.now, verbose_name='تاریخ اندازه‌گیری')
    notes = models.TextField(blank=True, null=True, verbose_name='یادداشت')
    
    class Meta:
        verbose_name = 'آنالیز پیشرفت'
        verbose_name_plural = 'آنالیزهای پیشرفت'
        ordering = ['-measurement_date']
    
    def __str__(self):
        return f"{self.get_measurement_type_display()} - {self.user.userprofile.name} - {self.measurement_date}"

class BodyInformationUser(models.Model):
    GENDER_CHOICES = [
        ('male', 'مرد'),
        ('female', 'زن'),
    ]
    
    DISEASE_CHOICES = [
        ('yes', 'دارم'),
        ('no', 'ندارم'),
    ]
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='body_information')
    birth_date = models.DateField(verbose_name='تاریخ تولد')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='جنسیت')
    height_cm = models.PositiveIntegerField(verbose_name='قد (سانتی متر)')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='وزن (کیلوگرم)')
    disease_history = models.CharField(max_length=3, choices=DISEASE_CHOICES, verbose_name='سابقه بیماری')
    disease_description = models.TextField(blank=True, null=True, verbose_name='توضیحات بیماری')
    
    # Body images (all optional)
    body_image_front = models.ImageField(upload_to='body_images/', blank=True, null=True, verbose_name='عکس از جلو')
    body_image_back = models.ImageField(upload_to='body_images/', blank=True, null=True, verbose_name='عکس از پشت')
    body_image_left = models.ImageField(upload_to='body_images/', blank=True, null=True, verbose_name='عکس از طرف چپ')
    body_image_right = models.ImageField(upload_to='body_images/', blank=True, null=True, verbose_name='عکس از طرف راست')
    
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    
    class Meta:
        verbose_name = 'اطلاعات بدنی کاربر'
        verbose_name_plural = 'اطلاعات بدنی کاربران'
    
    def __str__(self):
        return f"اطلاعات بدنی {self.user_profile.name}"

class PaymentCard(models.Model):
    PLAN_TYPE_CHOICES = [
        ('workout_plan', 'برنامه تمرینی'),
        ('diet_plan', 'برنامه غذایی'),
        ('both', 'هر دو برنامه'),
    ]
    
    card_number = models.CharField(max_length=16, verbose_name='شماره کارت')
    card_holder_name = models.CharField(max_length=100, verbose_name='نام صاحب کارت')
    price_workout = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='قیمت برنامه تمرینی (تومان)')
    price_diet = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='قیمت برنامه غذایی (تومان)')
    price_both = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='قیمت هر دو برنامه (تومان)')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    
    class Meta:
        verbose_name = 'کارت پرداخت'
        verbose_name_plural = 'کارت‌های پرداخت'
    
    def __str__(self):
        return f"{self.card_holder_name} - {self.card_number}"
    
    def get_formatted_card_number(self):
        """Return complete formatted card number like: 1234-5678-9012-3456"""
        if len(self.card_number) == 16:
            return f"{self.card_number[:4]}-{self.card_number[4:8]}-{self.card_number[8:12]}-{self.card_number[12:]}"
        return self.card_number
    
    def get_price_for_plan_type(self, plan_type):
        """Return price based on plan type"""
        if plan_type == 'workout':
            return self.price_workout
        elif plan_type == 'diet':
            return self.price_diet
        else:
            return self.price_both
