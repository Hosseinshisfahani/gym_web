from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    UserProfile, WorkoutPlan, DietPlan, Payment, 
    Ticket, Document, PlanRequest, BodyAnalysisReport, 
    MonthlyGoal, ProgressAnalysis, BodyInformationUser
)

class UserRegistrationForm(UserCreationForm):
    name = forms.CharField(
        max_length=200, 
        required=True, 
        label='نام',
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
    password1 = forms.CharField(
        widget=forms.PasswordInput(),
        label='رمز عبور',
        required=True,
        help_text='رمز عبور شما باید حداقل ۸ کاراکتر داشته باشد و نمی‌تواند کاملاً عددی یا شبیه اطلاعات شخصی شما باشد.',
        error_messages={
            'required': 'لطفا رمز عبور را وارد کنید.'
        }
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(),
        label='تکرار رمز عبور',
        required=True,
        help_text='رمز عبور مشابه بالا را وارد کنید.',
        error_messages={
            'required': 'لطفا تکرار رمز عبور را وارد کنید.'
        }
    )
    
    class Meta:
        model = User
        fields = ['name', 'phone_number', 'password1', 'password2']
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise forms.ValidationError('شماره تلفن باید فقط شامل اعداد باشد.')
        # Check for non-English characters in phone number
        import re
        if not re.match(r'^[0-9]+$', phone_number):
            raise forms.ValidationError('زبان کیبورد شما باید انگلیسی باشد')
        if User.objects.filter(username=phone_number).exists():
            raise forms.ValidationError('این شماره تلفن قبلا ثبت شده است.')
        return phone_number
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        import re
        # Allow English letters, numbers, spaces, and common symbols
        if not re.match(r'^[A-Za-z0-9\s\.\-\_]+$', name):
            raise forms.ValidationError('نام باید شامل حروف انگلیسی، اعداد، فاصله و علائم مجاز باشد')
        # Check if name contains any Persian/Arabic characters
        persian_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
        if re.search(persian_pattern, name):
            raise forms.ValidationError('لطفاً از حروف انگلیسی استفاده کنید')
        return name
    
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
        user.username = self.cleaned_data['phone_number']  # Set username to phone_number
        
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                phone_number=self.cleaned_data['phone_number'],
            )
        return user

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False, label='ایمیل')
    password = forms.CharField(widget=forms.PasswordInput(), required=False, label='رمز عبور جدید')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False, label='تکرار رمز عبور جدید')
    
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'name', 'phone_number', 'post_code', 'home_address']
        labels = {
            'profile_image': 'عکس پروفایل',
            'name': 'نام',
            'phone_number': 'شماره تلفن',
            'post_code': 'کد پستی',
            'home_address': 'آدرس منزل',
        }
        widgets = {
            'home_address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
    
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
        fields = ['title', 'description', 'image', 'plan_file', 'duration_weeks', 'start_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'image': 'تصویر برنامه (ضروری)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = True

class DietPlanForm(forms.ModelForm):
    class Meta:
        model = DietPlan
        fields = ['title', 'description', 'image', 'plan_file', 'duration_weeks', 'start_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
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
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
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
            'report_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'توضیحات اضافی خود را وارد کنید...'}),
        }

class BodyAnalysisResponseForm(forms.ModelForm):
    class Meta:
        model = BodyAnalysisReport
        fields = ['admin_response', 'status']
        widgets = {
            'admin_response': forms.Textarea(attrs={'rows': 4, 'placeholder': 'پاسخ خود را بنویسید...'}),
        }

class MonthlyGoalForm(forms.ModelForm):
    class Meta:
        model = MonthlyGoal
        fields = ['title', 'description', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'جزئیات هدف خود را وارد کنید...'}),
        }

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
            'measurement_date': forms.DateInput(attrs={'type': 'date'}),
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
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
    
    def clean(self):
        cleaned_data = super().clean()
        disease_history = cleaned_data.get('disease_history')
        disease_description = cleaned_data.get('disease_description')
        
        if disease_history == 'yes' and not disease_description:
            raise forms.ValidationError({
                'disease_description': 'لطفاً در صورت داشتن سابقه بیماری، توضیحات را وارد کنید.'
            })
        
        return cleaned_data 