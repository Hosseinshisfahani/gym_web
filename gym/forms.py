from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, WorkoutPlan, DietPlan, Payment, Ticket, Document, PlanRequest

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
                melli_code=f"temp_{user.id}"  # Temporary melli_code to satisfy unique constraint
            )
        return user

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False, label='ایمیل')
    password = forms.CharField(widget=forms.PasswordInput(), required=False, label='رمز عبور جدید')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False, label='تکرار رمز عبور جدید')
    
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'name', 'melli_code', 'phone_number', 'post_code', 'home_address']
        labels = {
            'profile_image': 'عکس پروفایل',
            'name': 'نام',
            'melli_code': 'کد ملی',
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
    
    def clean_melli_code(self):
        melli_code = self.cleaned_data.get('melli_code')
        
        # Check if this melli_code is already used by another user
        if melli_code and self.instance and self.instance.pk:
            existing = UserProfile.objects.filter(melli_code=melli_code).exclude(pk=self.instance.pk).exists()
            if existing:
                raise forms.ValidationError('این کد ملی قبلا ثبت شده است.')
        
        return melli_code
    
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
        fields = ['title', 'description', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class DietPlanForm(forms.ModelForm):
    class Meta:
        model = DietPlan
        fields = ['title', 'description', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'description', 'date', 'payment_image']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['subject', 'message']

class TicketResponseForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file']

class PlanRequestForm(forms.ModelForm):
    class Meta:
        model = PlanRequest
        fields = ['plan_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'لطفا توضیحات خود را وارد کنید...'}),
        }
        labels = {
            'plan_type': 'نوع برنامه',
            'description': 'توضیحات',
        } 