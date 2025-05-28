from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, WorkoutPlan, DietPlan, Certificate, Payment, Ticket, Document, Booklet, BookletPayment, PlanRequest

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='ایمیل',
        help_text='لطفا ایمیل معتبر خود را وارد کنید.',
        error_messages={
            'required': 'لطفا ایمیل خود را وارد کنید.',
            'invalid': 'لطفا یک ایمیل معتبر وارد کنید.',
            'unique': 'این ایمیل قبلا ثبت شده است.'
        }
    )
    melli_code = forms.CharField(
        max_length=10, 
        required=True, 
        label='کد ملی',
        help_text='لطفا کد ملی خود را وارد کنید. این کد به عنوان رمز عبور شما نیز تنظیم خواهد شد.',
        error_messages={
            'required': 'لطفا کد ملی خود را وارد کنید.',
            'unique': 'کد ملی شما تکراری است. لطفا آن را تصحیح کنید.'
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
    full_name = forms.CharField(max_length=200, required=True, label='نام و نام خانوادگی')
    father_name = forms.CharField(max_length=100, required=True, label='نام پدر')
    
    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']
        labels = {
            'email': 'ایمیل',
            'password1': 'رمز عبور',
            'password2': 'تکرار رمز عبور',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set password fields to use melli_code
        self.fields['password1'].widget = forms.HiddenInput()
        self.fields['password2'].widget = forms.HiddenInput()
        self.fields['password1'].required = False
        self.fields['password2'].required = False
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('این ایمیل قبلا ثبت شده است.')
        return email
    
    def clean_melli_code(self):
        melli_code = self.cleaned_data.get('melli_code')
        if not melli_code.isdigit() or len(melli_code) != 10:
            raise forms.ValidationError('کد ملی باید 10 رقم باشد.')
        if UserProfile.objects.filter(melli_code=melli_code).exists():
            raise forms.ValidationError('کد ملی شما تکراری است. لطفا آن را تصحیح کنید.')
        return melli_code
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise forms.ValidationError('شماره تلفن باید فقط شامل اعداد باشد.')
        return phone_number
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['melli_code']  # Set username to melli_code
        
        # Set password to melli_code
        melli_code = self.cleaned_data['melli_code']
        user.set_password(melli_code)
        
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                melli_code=self.cleaned_data['melli_code'],
                full_name=self.cleaned_data['full_name'],
                father_name=self.cleaned_data['father_name'],
                phone_number=self.cleaned_data['phone_number']
            )
        return user

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='ایمیل')
    password = forms.CharField(widget=forms.PasswordInput(), required=False, label='رمز عبور جدید')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False, label='تکرار رمز عبور جدید')
    
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'full_name', 'father_name', 'birth_year', 'melli_code', 
                 'education_place', 'education_level', 'phone_number']
        labels = {
            'profile_image': 'عکس پروفایل',
            'full_name': 'نام و نام خانوادگی',
            'father_name': 'نام پدر',
            'birth_year': 'سال تولد',
            'melli_code': 'کد ملی',
            'education_place': 'محل تحصیل',
            'education_level': 'مقطع تحصیلی',
            'phone_number': 'شماره تلفن',
        }
        widgets = {
            'birth_year': forms.NumberInput(attrs={'type': 'number'}),
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

class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['title', 'issue_date', 'description']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'})
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

class BookletForm(forms.ModelForm):
    class Meta:
        model = Booklet
        fields = ['title', 'description', 'price', 'file', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class BookletPaymentForm(forms.ModelForm):
    class Meta:
        model = BookletPayment
        fields = ['payment_image', 'amount', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

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