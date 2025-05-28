from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True, verbose_name='عکس پروفایل')
    full_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='نام و نام خانوادگی')
    father_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='نام پدر')
    birth_year = models.IntegerField(blank=True, null=True, verbose_name='سال تولد')
    melli_code = models.CharField(max_length=10, unique=True, verbose_name='کد ملی')
    education_place = models.CharField(max_length=200, blank=True, null=True, verbose_name='محل تحصیل')
    education_level = models.CharField(max_length=100, blank=True, null=True, verbose_name='مقطع تحصیلی')
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name='شماره تلفن')
    agreement_accepted = models.BooleanField(default=False, verbose_name='توافقنامه پذیرفته شده')
    
    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'
    
    def __str__(self):
        return f"{self.full_name} ({self.melli_code})"

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
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='workout_plans/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'برنامه تمرینی'
        verbose_name_plural = 'برنامه‌های تمرینی'
        permissions = [
            ('can_view_private_workout_plans', 'Can view private workout plans'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class DietPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diet_plans')
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='diet_plans/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'برنامه غذایی'
        verbose_name_plural = 'برنامه‌های غذایی'
        permissions = [
            ('can_view_private_diet_plans', 'Can view private diet plans'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class Certificate(models.Model):
    STATUS_CHOICES = [
        ('pending', 'درحال تایید'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    title = models.CharField(max_length=100, verbose_name='عنوان گواهی')
    image = models.ImageField(upload_to='certificates/', verbose_name='تصویر گواهی', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    issue_date = models.DateField(verbose_name='تاریخ صدور', default=timezone.now)
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    approval_message = models.TextField(blank=True, null=True, verbose_name='پیام تایید')
    
    class Meta:
        verbose_name = 'گواهی ورزشی'
        verbose_name_plural = 'گواهی‌های ورزشی'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def save(self, *args, **kwargs):
        # Add a flag to prevent recursion
        if not hasattr(self, '_saving'):
            self._saving = True
            try:
                # Check if status is being changed to approved
                if self.pk:
                    try:
                        old_instance = Certificate.objects.get(pk=self.pk)
                        if old_instance.status != 'approved' and self.status == 'approved':
                            # Save first to trigger the signal
                            super().save(*args, **kwargs)
                            return
                    except Certificate.DoesNotExist:
                        pass
                super().save(*args, **kwargs)
            finally:
                delattr(self, '_saving')

class CertificateComment(models.Model):
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(verbose_name='پیام')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'نظر گواهی'
        verbose_name_plural = 'نظرات گواهی'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.certificate.title}"

class Attendance(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    present = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['user_profile', 'date']
        ordering = ['-date']
        verbose_name = 'حضور و غیاب'
        verbose_name_plural = 'حضور و غیاب'

    def __str__(self):
        return f"{self.user_profile.full_name} - {self.date} - {'حاضر' if self.present else 'غایب'}"

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_image = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"

class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.subject}"

class TicketResponse(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Response to {self.ticket.subject}"

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='documents/')
    is_paid = models.BooleanField(default=False)
    upload_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class Booklet(models.Model):
    title = models.CharField(max_length=200, verbose_name='عنوان جزوه')
    description = models.TextField(verbose_name='توضیحات')
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='قیمت (تومان)')
    file = models.FileField(upload_to='booklets/', verbose_name='فایل PDF')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'جزوه درسی'
        verbose_name_plural = 'جزوات درسی'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class BookletPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار تایید'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    booklet = models.ForeignKey(Booklet, on_delete=models.CASCADE, verbose_name='جزوه')
    payment_image = models.ImageField(upload_to='booklet_payments/', verbose_name='تصویر فیش واریزی')
    amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='مبلغ پرداختی')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'پرداخت جزوه'
        verbose_name_plural = 'پرداخت‌های جزوات'
        ordering = ['-created_at']
        unique_together = ['user', 'booklet']

    def __str__(self):
        return f"{self.user.username} - {self.booklet.title}"

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
