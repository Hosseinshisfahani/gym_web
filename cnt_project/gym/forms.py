from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    UserProfile, WorkoutPlan, DietPlan, Payment, 
    Ticket, Document, PlanRequest, BodyAnalysisReport, 
    MonthlyGoal, ProgressAnalysis
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
        error_messages={
            'required': 'لطفا رمز عبور را وارد کنید.'
        }
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(),
        label='تکرار رمز عبور',
        required=True,
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
        if User.objects.filter(username=phone_number).exists():
            raise forms.ValidationError('این شماره تلفن قبلا ثبت شده است.')
        return phone_number
    
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
        fields = ['title', 'description', 'plan_file', 'duration_weeks', 'start_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class DietPlanForm(forms.ModelForm):
    class Meta:
        model = DietPlan
        fields = ['title', 'description', 'plan_file', 'duration_weeks', 'start_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

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