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
    is_vip = models.BooleanField(default=False, verbose_name='کاربر VIP')
    
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
    WORKOUT_TYPE_CHOICES = [
        ('fat_burning', 'چربی سوزی'),
        ('bulk', 'حجم'),
        ('hypertrophy', 'هایپروتروفی'),
        ('corrective', 'اصلاحی'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_plans')
    plan_type = models.CharField(max_length=20, choices=WORKOUT_TYPE_CHOICES, verbose_name='نوع برنامه', default='hypertrophy')
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
        return f"{self.get_plan_type_display()} - {self.user.username}"
    
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
        ('failed', 'ناموفق'),
    ]
    PAYMENT_TYPE_CHOICES = [
        ('membership', 'حق عضویت'),
        ('workout_plan', 'برنامه تمرینی'),
        ('diet_plan', 'برنامه غذایی'),
        ('other', 'سایر'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('manual', 'پرداخت دستی'),
        ('gateway', 'درگاه پرداخت'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.PositiveIntegerField(verbose_name='مبلغ (تومان)')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='other', verbose_name='نوع پرداخت')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='manual', verbose_name='روش پرداخت')
    payment_date = models.DateField(default=timezone.now, verbose_name='تاریخ پرداخت')
    proof_image = models.ImageField(upload_to='payment_proofs/', blank=True, null=True, verbose_name='تصویر رسید پرداخت')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    admin_note = models.TextField(blank=True, null=True, verbose_name='توضیحات مدیر')
    card_number = models.CharField(max_length=16, blank=True, null=True, verbose_name='شماره کارت')
    
    # Gateway payment fields
    gateway_type = models.CharField(max_length=20, blank=True, null=True, verbose_name='نوع درگاه')
    gateway_authority = models.CharField(max_length=100, blank=True, null=True, verbose_name='کد تراکنش درگاه')
    gateway_ref_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='شماره پیگیری')
    gateway_response = models.TextField(blank=True, null=True, verbose_name='پاسخ درگاه')
    
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
        try:
            return f"آنالیز بدن {self.user.userprofile.name} - {self.report_date}"
        except:
            return f"آنالیز بدن {self.user.username} - {self.report_date}"

# اهداف ماهانه (Monthly Goals) - Main section for goal setting
class MonthlyGoal(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'شروع نشده'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_goals')
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name='عنوان هدف')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    start_date = models.DateField(default=timezone.now, verbose_name='تاریخ شروع')
    end_date = models.DateField(verbose_name='تاریخ پایان')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_started', verbose_name='وضعیت')
    progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='پیشرفت (درصد)')
    coach_notes = models.TextField(blank=True, null=True, verbose_name='یادداشت مربی')
    
    # Target measurements - set by admin
    target_weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name='هدف وزن (کیلوگرم)')
    target_body_fat_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name='هدف درصد چربی بدن (%)')
    target_muscle_mass = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name='هدف توده عضلانی (کیلوگرم)')
    
    # Goal directions - specify if target is to lose or gain
    GOAL_DIRECTION_CHOICES = [
        ('lose', 'کاهش'),
        ('gain', 'افزایش'),
        ('maintain', 'حفظ'),
    ]
    
    weight_goal_direction = models.CharField(max_length=10, choices=GOAL_DIRECTION_CHOICES, blank=True, null=True, verbose_name='جهت هدف وزن')
    body_fat_goal_direction = models.CharField(max_length=10, choices=GOAL_DIRECTION_CHOICES, blank=True, null=True, verbose_name='جهت هدف چربی')
    muscle_mass_goal_direction = models.CharField(max_length=10, choices=GOAL_DIRECTION_CHOICES, blank=True, null=True, verbose_name='جهت هدف عضله')
    
    class Meta:
        verbose_name = 'هدف ماهانه'
        verbose_name_plural = 'اهداف ماهانه'
        ordering = ['-start_date']
    
    def __str__(self):
        try:
            return f"{self.title} - {self.user.userprofile.name}"
        except:
            return f"{self.title} - {self.user.username}"
            
    def get_current_measurements(self):
        """Get user's most recent measurements for comparison with targets"""
        measurements = {}
        
        # Get latest weight measurement
        latest_weight = self.user.progress_analyses.filter(measurement_type='weight').order_by('-measurement_date').first()
        if latest_weight:
            measurements['current_weight'] = latest_weight.value
            measurements['current_weight_date'] = latest_weight.measurement_date
        
        # Get latest body fat measurement
        latest_body_fat = self.user.progress_analyses.filter(measurement_type='body_fat').order_by('-measurement_date').first()
        if latest_body_fat:
            measurements['current_body_fat'] = latest_body_fat.value
            measurements['current_body_fat_date'] = latest_body_fat.measurement_date
        
        # Get latest muscle mass measurement
        latest_muscle_mass = self.user.progress_analyses.filter(measurement_type='muscle_mass').order_by('-measurement_date').first()
        if latest_muscle_mass:
            measurements['current_muscle_mass'] = latest_muscle_mass.value
            measurements['current_muscle_mass_date'] = latest_muscle_mass.measurement_date
        
        return measurements
    
    def calculate_progress_towards_targets(self):
        """Calculate progress towards each target based on current measurements and goal directions"""
        current = self.get_current_measurements()
        progress_data = {}
        
        # Calculate weight progress with direction awareness
        if self.target_weight and 'current_weight' in current and self.weight_goal_direction:
            current_weight = float(current['current_weight'])
            target_weight = float(self.target_weight)
            
            # Get initial weight (earliest measurement or user's body info weight)
            try:
                initial_weight = float(self.user.userprofile.body_information.weight_kg)
            except:
                # Fallback to earliest weight measurement
                earliest_weight = self.user.progress_analyses.filter(measurement_type='weight').order_by('measurement_date').first()
                initial_weight = float(earliest_weight.value) if earliest_weight else current_weight
            
            if self.weight_goal_direction == 'lose':
                # For weight loss: progress = (initial - current) / (initial - target) * 100
                if initial_weight > target_weight:
                    weight_progress = ((initial_weight - current_weight) / (initial_weight - target_weight)) * 100
                else:
                    weight_progress = 100 if current_weight <= target_weight else 0
            elif self.weight_goal_direction == 'gain':
                # For weight gain: progress = (current - initial) / (target - initial) * 100
                if target_weight > initial_weight:
                    weight_progress = ((current_weight - initial_weight) / (target_weight - initial_weight)) * 100
                else:
                    weight_progress = 100 if current_weight >= target_weight else 0
            else:  # maintain
                # For maintaining: calculate how close to target
                tolerance = 2.0  # 2kg tolerance
                if abs(current_weight - target_weight) <= tolerance:
                    weight_progress = 100
                else:
                    weight_progress = max(0, 100 - (abs(current_weight - target_weight) / tolerance) * 100)
            
            progress_data['weight_progress'] = max(0, min(100, weight_progress))
        
        # Calculate body fat progress with direction awareness
        if self.target_body_fat_percentage and 'current_body_fat' in current and self.body_fat_goal_direction:
            current_bf = float(current['current_body_fat'])
            target_bf = float(self.target_body_fat_percentage)
            
            # Get initial body fat measurement
            earliest_bf = self.user.progress_analyses.filter(measurement_type='body_fat').order_by('measurement_date').first()
            initial_bf = float(earliest_bf.value) if earliest_bf else current_bf
            
            if self.body_fat_goal_direction == 'lose':
                # For body fat loss: progress = (initial - current) / (initial - target) * 100
                if initial_bf > target_bf:
                    bf_progress = ((initial_bf - current_bf) / (initial_bf - target_bf)) * 100
                else:
                    bf_progress = 100 if current_bf <= target_bf else 0
            elif self.body_fat_goal_direction == 'gain':
                # For body fat gain: progress = (current - initial) / (target - initial) * 100
                if target_bf > initial_bf:
                    bf_progress = ((current_bf - initial_bf) / (target_bf - initial_bf)) * 100
                else:
                    bf_progress = 100 if current_bf >= target_bf else 0
            else:  # maintain
                # For maintaining: calculate how close to target
                tolerance = 2.0  # 2% tolerance
                if abs(current_bf - target_bf) <= tolerance:
                    bf_progress = 100
                else:
                    bf_progress = max(0, 100 - (abs(current_bf - target_bf) / tolerance) * 100)
            
            progress_data['body_fat_progress'] = max(0, min(100, bf_progress))
        
        # Calculate muscle mass progress with direction awareness
        if self.target_muscle_mass and 'current_muscle_mass' in current and self.muscle_mass_goal_direction:
            current_mm = float(current['current_muscle_mass'])
            target_mm = float(self.target_muscle_mass)
            
            # Get initial muscle mass measurement
            earliest_mm = self.user.progress_analyses.filter(measurement_type='muscle_mass').order_by('measurement_date').first()
            initial_mm = float(earliest_mm.value) if earliest_mm else current_mm
            
            if self.muscle_mass_goal_direction == 'lose':
                # For muscle mass loss: progress = (initial - current) / (initial - target) * 100
                if initial_mm > target_mm:
                    mm_progress = ((initial_mm - current_mm) / (initial_mm - target_mm)) * 100
                else:
                    mm_progress = 100 if current_mm <= target_mm else 0
            elif self.muscle_mass_goal_direction == 'gain':
                # For muscle mass gain: progress = (current - initial) / (target - initial) * 100
                if target_mm > initial_mm:
                    mm_progress = ((current_mm - initial_mm) / (target_mm - initial_mm)) * 100
                else:
                    mm_progress = 100 if current_mm >= target_mm else 0
            else:  # maintain
                # For maintaining: calculate how close to target
                tolerance = 1.0  # 1kg tolerance
                if abs(current_mm - target_mm) <= tolerance:
                    mm_progress = 100
                else:
                    mm_progress = max(0, 100 - (abs(current_mm - target_mm) / tolerance) * 100)
            
            progress_data['muscle_mass_progress'] = max(0, min(100, mm_progress))
        
        return progress_data

# آنالیز پیشرفت (Progress Analysis) - Main section for tracking measurements
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
        try:
            return f"{self.get_measurement_type_display()} - {self.user.userprofile.name} - {self.measurement_date}"
        except:
            return f"{self.get_measurement_type_display()} - {self.user.username} - {self.measurement_date}"

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
        card_str = str(self.card_number)
        if len(card_str) == 16:
            return f"{card_str[:4]}-{card_str[4:8]}-{card_str[8:12]}-{card_str[12:]}"
        return card_str
    
    def get_price_for_plan_type(self, plan_type):
        """Return price based on plan type"""
        if plan_type == 'workout':
            return self.price_workout
        elif plan_type == 'diet':
            return self.price_diet
        else:
            return self.price_both

# Additional models for Booklet functionality
class Booklet(models.Model):
    title = models.CharField(max_length=200, verbose_name='عنوان')
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='قیمت (تومان)')
    file = models.FileField(upload_to='booklets/', verbose_name='فایل')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = 'جزوه'
        verbose_name_plural = 'جزوات'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class BookletPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'در انتظار تایید'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booklet_payments')
    booklet = models.ForeignKey(Booklet, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='مبلغ (تومان)')
    payment_date = models.DateField(default=timezone.now, verbose_name='تاریخ پرداخت')
    proof_image = models.ImageField(upload_to='booklet_payment_proofs/', verbose_name='تصویر رسید پرداخت')
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    admin_note = models.TextField(blank=True, null=True, verbose_name='توضیحات مدیر')
    card_number = models.CharField(max_length=16, blank=True, null=True, verbose_name='شماره کارت')
    
    class Meta:
        verbose_name = 'پرداخت جزوه'
        verbose_name_plural = 'پرداخت‌های جزوه'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.booklet.title} - {self.amount} تومان"

# Email Notification Settings Model
class EmailNotificationSettings(models.Model):
    """Model to store email notification preferences for admins"""
    
    # Admin user who owns these settings
    admin_user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='email_notification_settings',
        limit_choices_to={'is_staff': True},
        verbose_name='کاربر ادمین'
    )
    
    # Email address to send notifications to (can be different from admin's email)
    notification_email = models.EmailField(verbose_name='ایمیل دریافت اطلاع‌رسانی')
    
    # Shop order notifications
    notify_shop_orders = models.BooleanField(default=True, verbose_name='اطلاع‌رسانی سفارشات فروشگاه')
    notify_shop_order_status_change = models.BooleanField(default=True, verbose_name='اطلاع‌رسانی تغییر وضعیت سفارش')
    
    # Plan request notifications  
    notify_workout_plan_requests = models.BooleanField(default=True, verbose_name='اطلاع‌رسانی درخواست برنامه تمرینی')
    notify_diet_plan_requests = models.BooleanField(default=True, verbose_name='اطلاع‌رسانی درخواست برنامه غذایی')
    
    # General notification settings
    notify_new_user_registration = models.BooleanField(default=False, verbose_name='اطلاع‌رسانی کاربران جدید')
    notify_payment_uploads = models.BooleanField(default=True, verbose_name='اطلاع‌رسانی آپلود رسید پرداخت')
    
    # Notification frequency (for bundled notifications)
    NOTIFICATION_FREQUENCY_CHOICES = [
        ('immediate', 'بلافاصله'),
        ('hourly', 'هر ساعت'),
        ('daily', 'روزانه'),
        ('weekly', 'هفتگی'),
    ]
    notification_frequency = models.CharField(
        max_length=20,
        choices=NOTIFICATION_FREQUENCY_CHOICES,
        default='immediate',
        verbose_name='فرکانس اطلاع‌رسانی'
    )
    
    # Active status
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'تنظیمات اطلاع‌رسانی ایمیل'
        verbose_name_plural = 'تنظیمات اطلاع‌رسانی ایمیل'
        ordering = ['-created_at']

    def __str__(self):
        return f'تنظیمات اطلاع‌رسانی {self.admin_user.username}'

    @classmethod
    def get_active_notification_emails(cls, notification_type):
        """Get all active admin emails for a specific notification type"""
        field_mapping = {
            'shop_order': 'notify_shop_orders',
            'workout_plan_request': 'notify_workout_plan_requests',
            'diet_plan_request': 'notify_diet_plan_requests',
            'new_user': 'notify_new_user_registration',
            'payment_upload': 'notify_payment_uploads',
        }
        
        if notification_type not in field_mapping:
            return []
        
        field_name = field_mapping[notification_type]
        filter_kwargs = {
            'is_active': True,
            field_name: True
        }
        
        return cls.objects.filter(**filter_kwargs).values_list('notification_email', flat=True)

    def save(self, *args, **kwargs):
        # Set default notification email to admin's email if not provided
        if not self.notification_email and self.admin_user.email:
            self.notification_email = self.admin_user.email
        super().save(*args, **kwargs)
