from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    UserProfile, WorkoutPlan, DietPlan, Payment, 
    Ticket, Document, PlanRequest, BodyAnalysisReport, InBodyReport,
    MonthlyGoal, ProgressAnalysis, BodyInformationUser, TuitionCategory, TuitionReceipt
)
import jdatetime
from datetime import datetime, date

class PersianDateWidget(forms.DateInput):
    """Persian date widget that displays Persian dates but submits Gregorian dates"""
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control persian-date-input',
            'placeholder': '۱۴۰۳/۰۱/۰۱',
            'dir': 'ltr'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
    
    def format_value(self, value):
        if value is None:
            return ''
        
        # Convert Gregorian date to Persian for display
        if isinstance(value, (datetime, date)):
            try:
                if isinstance(value, datetime):
                    persian_date = jdatetime.datetime.fromgregorian(datetime=value)
                else:
                    persian_date = jdatetime.date.fromgregorian(date=value)
                return f"{persian_date.year}/{persian_date.month:02d}/{persian_date.day:02d}"
            except:
                return ''
        return str(value)
    
    def value_from_datadict(self, data, files, name):
        # Get the Persian date string from form
        persian_date_str = data.get(name)
        if not persian_date_str:
            return None
        
        try:
            # Parse Persian date (expected format: YYYY/MM/DD)
            parts = persian_date_str.split('/')
            if len(parts) == 3:
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                # Convert Persian date to Gregorian
                persian_date = jdatetime.date(year, month, day)
                gregorian_date = persian_date.togregorian()
                return gregorian_date.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            pass
        
        return persian_date_str

def persian_to_gregorian_date(persian_date_str):
    """Convert Persian date string to Gregorian date object"""
    if not persian_date_str:
        return None
    
    try:
        parts = persian_date_str.split('/')
        if len(parts) == 3:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            persian_date = jdatetime.date(year, month, day)
            return persian_date.togregorian()
    except (ValueError, AttributeError):
        pass
    
    return None

class UserRegistrationForm(UserCreationForm):
    name = forms.CharField(
        max_length=200, 
        required=True, 
        label='نام و نام خانوادگی',
        error_messages={
            'required': 'لطفا نام خود را وارد کنید.'
        }
    )
    phone_number = forms.CharField(
        max_length=15, 
        required=True,
        label='شماره تلفن',
        help_text='لطفا شماره تلفن خود را وارد کنید.',
        error_messages={
            'required': 'لطفا شماره تلفن خود را وارد کنید.'
        }
    )
    melli_code = forms.CharField(
        max_length=10, 
        required=True,
        label='کد ملی',
        help_text='لطفا کد ملی ۱۰ رقمی خود را وارد کنید.',
        error_messages={
            'required': 'لطفا کد ملی خود را وارد کنید.'
        }
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'رمز عبور شما'}),
        label='رمز عبور',
        required=True,
        help_text='رمز عبور شما باید حداقل ۸ کاراکتر داشته باشد و نمی‌تواند کاملاً عددی یا شبیه اطلاعات شخصی شما باشد.',
        error_messages={
            'required': 'لطفا رمز عبور را وارد کنید.'
        }
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'تکرار رمز عبور'}),
        label='تکرار رمز عبور',
        required=True,
        help_text='رمز عبور مشابه بالا را وارد کنید.',
        error_messages={
            'required': 'لطفا تکرار رمز عبور را وارد کنید.'
        }
    )
    
    class Meta:
        model = User
        fields = ['name', 'phone_number', 'melli_code', 'password1', 'password2']
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError('لطفا نام خود را وارد کنید.')
            
        # Check if this name is already used by another user
        from .models import UserProfile
        if UserProfile.objects.filter(name=name).exists():
            raise forms.ValidationError('این نام قبلاً استفاده شده است. لطفاً نام دیگری انتخاب کنید.')
        
        import re
        # Allow Persian/Farsi characters, English letters, numbers, spaces, and common symbols
        persian_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
        english_pattern = r'[A-Za-z]'
        
        # Check if name contains valid characters (Persian, English, numbers, spaces, common symbols)
        if not re.match(r'^[A-Za-z0-9\s\.\-\_\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+$', name):
            raise forms.ValidationError('نام باید شامل حروف فارسی، انگلیسی، اعداد، فاصله و علائم مجاز باشد')
        
        return name
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError('لطفا شماره تلفن خود را وارد کنید.')
            
        if not phone_number.isdigit():
            raise forms.ValidationError('شماره تلفن باید فقط شامل اعداد باشد.')
        # Check for non-English characters in phone number
        import re
        if not re.match(r'^[0-9]+$', phone_number):
            raise forms.ValidationError('زبان کیبورد شما باید انگلیسی باشد')
        # Check if phone number is already used by another user - import here to avoid circular import
        from .models import UserProfile
        if UserProfile.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError('این شماره تلفن قبلا ثبت شده است.')
        return phone_number
    
    def clean_melli_code(self):
        melli_code = self.cleaned_data.get('melli_code')
        if not melli_code:
            raise forms.ValidationError('لطفا کد ملی خود را وارد کنید.')
            
        if not melli_code.isdigit():
            raise forms.ValidationError('کد ملی باید فقط شامل اعداد باشد.')
            
        if len(melli_code) != 10:
            raise forms.ValidationError('کد ملی باید ۱۰ رقم باشد.')
            
        # Check if melli code is already used by another user
        from .models import UserProfile
        if UserProfile.objects.filter(melli_code=melli_code).exists():
            raise forms.ValidationError('این کد ملی قبلا ثبت شده است.')
        return melli_code
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        
        if password1:
            # Custom validation with Persian messages
            if len(password1) < 8:
                raise forms.ValidationError('رمز عبور شما باید حداقل ۸ کاراکتر داشته باشد.')
            
            if password1.isdigit():
                raise forms.ValidationError('رمز عبور شما نمی‌تواند کاملاً عددی باشد.')
            
            # Check for common passwords
            common_passwords = ['12345678', 'password', 'qwerty', '123456789', 'password123']
            if password1.lower() in common_passwords:
                raise forms.ValidationError('رمز عبور شما نمی‌تواند از رمزهای عمومی باشد.')
        
        return password1
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('رمز عبور و تکرار آن مطابقت ندارند.')
        
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['name']  # Set username to name instead of phone number
        
        if commit:
            user.save()
            # Create or get the user profile to avoid duplicates
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'name': self.cleaned_data['name'],
                    'phone_number': self.cleaned_data['phone_number'],
                    'melli_code': self.cleaned_data['melli_code'],
                }
            )
            if not created:
                # Update existing profile
                profile.name = self.cleaned_data['name']
                profile.phone_number = self.cleaned_data['phone_number']
                profile.melli_code = self.cleaned_data['melli_code']
                profile.save()
        return user

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False, label='ایمیل')
    password = forms.CharField(widget=forms.PasswordInput(), required=False, label='رمز عبور جدید')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False, label='تکرار رمز عبور جدید')
    
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'name', 'melli_code', 'phone_number', 'birth_date', 'post_code', 'home_address']
        labels = {
            'profile_image': 'عکس پروفایل',
            'name': 'نام و نام خانوادگی',
            'melli_code': 'کد ملی',
            'phone_number': 'شماره تلفن',
            'birth_date': 'تاریخ تولد',
            'post_code': 'کد پستی (اختیاری)',
            'home_address': 'آدرس منزل',
        }
        widgets = {
            'home_address': forms.Textarea(attrs={'rows': 3}),
            'melli_code': forms.TextInput(attrs={'maxlength': '10', 'placeholder': 'مثال: 1234567890'}),
            'post_code': forms.TextInput(attrs={'maxlength': '10', 'placeholder': 'مثال: 1234567890'}),
            'birth_date': PersianDateWidget(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
    
    def clean_profile_image(self):
        profile_image = self.cleaned_data.get('profile_image')
        if profile_image:
            # Check file size (5MB = 5 * 1024 * 1024 bytes)
            if profile_image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('حجم فایل نباید بیشتر از 5 مگابایت باشد.')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            content_type = profile_image.content_type
            if content_type not in allowed_types:
                raise forms.ValidationError('فقط فایل‌های تصویری با فرمت JPG، PNG یا GIF مجاز است.')
        
        return profile_image
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and password != confirm_password:
            raise forms.ValidationError('رمز عبور و تکرار آن مطابقت ندارند')
        
        return cleaned_data

class WorkoutPlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ['plan_type', 'description', 'image', 'plan_file', 'duration_weeks', 'start_date', 'is_active']
        widgets = {
            'start_date': PersianDateWidget(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'plan_type': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'image': 'تصویر برنامه (ضروری)',
            'plan_type': 'نوع برنامه تمرینی',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = True

class DietPlanForm(forms.ModelForm):
    class Meta:
        model = DietPlan
        fields = ['title', 'description', 'image', 'plan_file', 'duration_weeks', 'start_date', 'is_active']
        widgets = {
            'start_date': PersianDateWidget(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'image': 'تصویر برنامه (ضروری)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = True

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_type', 'payment_date', 'proof_image', 'description']
        widgets = {
            'payment_date': PersianDateWidget(),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }

class TicketResponseForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label='پیام')

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'document_type', 'file', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class PlanRequestForm(forms.ModelForm):
    class Meta:
        model = PlanRequest
        fields = ['plan_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

# Forms for new models
class BodyAnalysisReportForm(forms.ModelForm):
    class Meta:
        model = BodyAnalysisReport
        fields = ['image', 'description', 'report_date']
        widgets = {
            'report_date': PersianDateWidget(),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'توضیحات اضافی خود را وارد کنید...'}),
        }

class BodyAnalysisResponseForm(forms.ModelForm):
    class Meta:
        model = BodyAnalysisReport
        fields = ['admin_response', 'status']
        widgets = {
            'admin_response': forms.Textarea(attrs={'rows': 4, 'placeholder': 'پاسخ خود را بنویسید...'}),
        }

class InBodyReportForm(forms.ModelForm):
    class Meta:
        model = InBodyReport
        fields = ['image', 'description', 'report_date']
        widgets = {
            'report_date': PersianDateWidget(),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'توضیحات اضافی خود را وارد کنید...'}),
        }

class InBodyResponseForm(forms.ModelForm):
    class Meta:
        model = InBodyReport
        fields = ['admin_response', 'status']
        widgets = {
            'admin_response': forms.Textarea(attrs={'rows': 4, 'placeholder': 'پاسخ خود را بنویسید...'}),
        }

class MonthlyGoalForm(forms.ModelForm):
    class Meta:
        model = MonthlyGoal
        fields = [
            'user', 'start_date', 'end_date', 'status', 
            'target_weight', 'weight_goal_direction',
            'target_body_fat_percentage', 'body_fat_goal_direction',
            'target_muscle_mass', 'muscle_mass_goal_direction',
            'coach_notes'
        ]
        widgets = {
            'start_date': PersianDateWidget(),
            'end_date': PersianDateWidget(),
            'coach_notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'توصیه‌ها، راهنمایی‌ها و نکات مربی...'}),
            'target_weight': forms.NumberInput(attrs={'min': 30, 'max': 200, 'step': 0.1, 'placeholder': 'مثال: 70.5'}),
            'target_body_fat_percentage': forms.NumberInput(attrs={'min': 5, 'max': 50, 'step': 0.1, 'placeholder': 'مثال: 15.5'}),
            'target_muscle_mass': forms.NumberInput(attrs={'min': 20, 'max': 100, 'step': 0.1, 'placeholder': 'مثال: 45.2'}),
            'weight_goal_direction': forms.Select(attrs={'class': 'form-select'}),
            'body_fat_goal_direction': forms.Select(attrs={'class': 'form-select'}),
            'muscle_mass_goal_direction': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'user': 'انتخاب کاربر',
            'start_date': 'تاریخ شروع',
            'end_date': 'تاریخ پایان',
            'status': 'وضعیت',
            'target_weight': 'هدف وزن (کیلوگرم)',
            'weight_goal_direction': 'نوع هدف وزن',
            'target_body_fat_percentage': 'هدف درصد چربی بدن (%)',
            'body_fat_goal_direction': 'نوع هدف چربی',
            'target_muscle_mass': 'هدف توده عضلانی (کیلوگرم)',
            'muscle_mass_goal_direction': 'نوع هدف عضله',
            'coach_notes': 'یادداشت مربی',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users to show only non-staff users with their names
        from django.contrib.auth.models import User
        user_choices = []
        users = User.objects.exclude(is_staff=True).select_related('userprofile').order_by('username')
        for user in users:
            try:
                name = user.userprofile.name if user.userprofile.name else user.username
                user_choices.append((user.id, f"{name} ({user.username})"))
            except:
                user_choices.append((user.id, user.username))
        
        self.fields['user'].choices = user_choices
        self.fields['user'].widget.attrs.update({'class': 'form-select'})
        
        # Set default values for new goals
        if not self.instance.pk:
            self.fields['status'].initial = 'not_started'

class MonthlyGoalUpdateForm(forms.ModelForm):
    class Meta:
        model = MonthlyGoal
        fields = ['progress', 'status']
        widgets = {
            'progress': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 5}),
        }

class MonthlyGoalCoachForm(forms.ModelForm):
    class Meta:
        model = MonthlyGoal
        fields = ['coach_notes', 'status']
        widgets = {
            'coach_notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'یادداشت خود را برای کاربر بنویسید...'}),
        }

class ProgressAnalysisForm(forms.ModelForm):
    class Meta:
        model = ProgressAnalysis
        fields = ['measurement_type', 'value', 'unit', 'measurement_date', 'notes']
        widgets = {
            'measurement_date': PersianDateWidget(),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'یادداشت...'}),
        }

class BodyInformationUserForm(forms.ModelForm):
    class Meta:
        model = BodyInformationUser
        fields = [
            'birth_date', 'gender', 'height_cm', 'weight_kg', 
            'disease_history', 'disease_description',
            'body_image_front', 'body_image_back', 
            'body_image_left', 'body_image_right'
        ]
        widgets = {
            'birth_date': PersianDateWidget(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'height_cm': forms.NumberInput(attrs={'class': 'form-control', 'min': '100', 'max': '250', 'placeholder': 'مثال: 175'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'min': '30', 'max': '200', 'placeholder': 'مثال: 70'}),
            'disease_history': forms.Select(attrs={'class': 'form-control'}),
            'disease_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3, 
                'placeholder': 'در صورت داشتن سابقه بیماری، لطفاً توضیح دهید...'
            }),
            'body_image_front': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'body_image_back': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'body_image_left': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'body_image_right': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'birth_date': 'تاریخ تولد',
            'gender': 'جنسیت',
            'height_cm': 'قد (سانتی متر)',
            'weight_kg': 'وزن (کیلوگرم)',
            'disease_history': 'سابقه بیماری',
            'disease_description': 'توضیحات بیماری',
            'body_image_front': 'عکس از جلو (اختیاری)',
            'body_image_back': 'عکس از پشت (اختیاری)',
            'body_image_left': 'عکس از سمت چپ (اختیاری)',
            'body_image_right': 'عکس از سمت راست (اختیاری)',
        }
    
    def validate_image_size(self, image):
        """Validate that uploaded image is not larger than 5MB"""
        if image and hasattr(image, 'size'):
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if image.size > max_size:
                raise forms.ValidationError('حجم عکس نباید بیشتر از ۵ مگابایت باشد.')
        return image
    
    def clean_body_image_front(self):
        image = self.cleaned_data.get('body_image_front')
        return self.validate_image_size(image)
    
    def clean_body_image_back(self):
        image = self.cleaned_data.get('body_image_back')
        return self.validate_image_size(image)
    
    def clean_body_image_left(self):
        image = self.cleaned_data.get('body_image_left')
        return self.validate_image_size(image)
    
    def clean_body_image_right(self):
        image = self.cleaned_data.get('body_image_right')
        return self.validate_image_size(image)
    
    def clean(self):
        cleaned_data = super().clean()
        disease_history = cleaned_data.get('disease_history')
        disease_description = cleaned_data.get('disease_description')
        
        if disease_history == 'yes' and not disease_description:
            raise forms.ValidationError({
                'disease_description': 'لطفاً در صورت داشتن سابقه بیماری، توضیحات را وارد کنید.'
            })
        
        return cleaned_data 

class TuitionCategoryForm(forms.ModelForm):
    """Form for creating and editing tuition categories"""
    class Meta:
        model = TuitionCategory
        fields = ['name', 'description', 'amount', 'duration_months', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: ماهانه، فصلی، سالانه'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'توضیحات دسته‌بندی'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مبلغ به تومان'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مدت به ماه'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'نام دسته‌بندی',
            'description': 'توضیحات',
            'amount': 'مبلغ (تومان)',
            'duration_months': 'مدت (ماه)',
            'is_active': 'فعال',
        }

class TuitionReceiptForm(forms.ModelForm):
    """Form for athletes to upload tuition receipts"""
    class Meta:
        model = TuitionReceipt
        fields = ['category', 'receipt_image', 'amount_paid', 'payment_date', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'receipt_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مبلغ پرداخت شده به تومان'}),
            'payment_date': PersianDateWidget(),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'یادداشت‌های اضافی (اختیاری)'}),
        }
        labels = {
            'category': 'نوع شهریه',
            'receipt_image': 'تصویر رسید',
            'amount_paid': 'مبلغ پرداخت شده (تومان)',
            'payment_date': 'تاریخ پرداخت',
            'notes': 'یادداشت‌ها',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active categories
        self.fields['category'].queryset = TuitionCategory.objects.filter(is_active=True)
    
    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        category = self.cleaned_data.get('category')
        
        if amount and category:
            if amount != category.amount:
                raise forms.ValidationError(f'مبلغ باید دقیقاً {category.amount:,} تومان باشد.')
        
        return amount

class TuitionReceiptAdminForm(forms.ModelForm):
    """Form for admins to review and update tuition receipts"""
    class Meta:
        model = TuitionReceipt
        fields = ['status', 'admin_notes', 'expiry_date']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'یادداشت‌های ادمین'}),
            'expiry_date': PersianDateWidget(),
        }
        labels = {
            'status': 'وضعیت',
            'admin_notes': 'یادداشت‌های ادمین',
            'expiry_date': 'تاریخ انقضا',
        } 