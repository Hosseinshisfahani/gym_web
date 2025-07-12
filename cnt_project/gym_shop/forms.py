from django import forms
from .models import Product, Category, ProductImage

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'name_en', 'slug', 'category', 'description', 'short_description',
            'price', 'discount_price', 'image', 'stock', 'available_sizes',
            'weight', 'brand', 'material', 'color', 'is_featured', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام محصول به فارسی...'
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product name in English...'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'product-slug'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'توضیحات کامل محصول...'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'توضیح کوتاه محصول...'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'قیمت به تومان'
            }),
            'discount_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'قیمت تخفیف‌دار (اختیاری)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'تعداد موجودی'
            }),
            'available_sizes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'S,M,L,XL (با کاما جدا کنید)'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'وزن به کیلوگرم'
            }),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام برند'
            }),
            'material': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'جنس محصول'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رنگ محصول'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'name_en', 'slug', 'description', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام دسته‌بندی به فارسی...'
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name in English...'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'category-slug'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'توضیحات دسته‌بندی...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'متن توضیحی تصویر...'
            }),
        }

class ProductSearchForm(forms.Form):
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'جستجو در محصولات...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label='همه دسته‌بندی‌ها',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    is_active = forms.ChoiceField(
        choices=[('', 'همه محصولات'), ('true', 'فعال'), ('false', 'غیرفعال')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    is_featured = forms.ChoiceField(
        choices=[('', 'همه محصولات'), ('true', 'محصولات ویژه'), ('false', 'محصولات معمولی')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    ) 