from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from PIL import Image
import os

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام دسته‌بندی')
    name_en = models.CharField(max_length=100, verbose_name='نام انگلیسی')
    slug = models.SlugField(unique=True, verbose_name='شناسه')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    image = models.ImageField(upload_to='shop/categories/', blank=True, null=True, verbose_name='تصویر')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('gym_shop:category_detail', kwargs={'slug': self.slug})

class Product(models.Model):
    SIZES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
        ('XXXL', 'XXXL'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='نام محصول')
    name_en = models.CharField(max_length=200, verbose_name='نام انگلیسی')
    slug = models.SlugField(unique=True, verbose_name='شناسه')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='دسته‌بندی')
    description = models.TextField(verbose_name='توضیحات')
    short_description = models.CharField(max_length=300, verbose_name='توضیح کوتاه')
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='قیمت (تومان)')
    discount_price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, verbose_name='قیمت تخفیف‌دار')
    image = models.ImageField(upload_to='shop/products/', verbose_name='تصویر اصلی')
    stock = models.PositiveIntegerField(verbose_name='موجودی')
    available_sizes = models.CharField(max_length=100, blank=True, verbose_name='سایزهای موجود')
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name='وزن (کیلوگرم)')
    brand = models.CharField(max_length=100, blank=True, verbose_name='برند')
    material = models.CharField(max_length=100, blank=True, verbose_name='جنس')
    color = models.CharField(max_length=50, blank=True, verbose_name='رنگ')
    is_featured = models.BooleanField(default=False, verbose_name='محصول ویژه')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en)
        super().save(*args, **kwargs)

        # Resize image if too large
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                output_size = (800, 800)
                img.thumbnail(output_size)
                img.save(self.image.path)

    def get_absolute_url(self):
        return reverse('gym_shop:product_detail', kwargs={'slug': self.slug})

    @property
    def discount_percentage(self):
        if self.discount_price and self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def final_price(self):
        return self.discount_price if self.discount_price else self.price

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images', verbose_name='محصول')
    image = models.ImageField(upload_to='shop/products/gallery/', verbose_name='تصویر')
    alt_text = models.CharField(max_length=100, blank=True, verbose_name='متن جایگزین')

    class Meta:
        verbose_name = 'تصویر محصول'
        verbose_name_plural = 'تصاویر محصولات'

    def __str__(self):
        return f'{self.product.name} - تصویر {self.id}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                output_size = (800, 800)
                img.thumbnail(output_size)
                img.save(self.image.path)

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='کاربر')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'سبد خرید'
        verbose_name_plural = 'سبدهای خرید'

    def __str__(self):
        return f'سبد خرید {self.user.username}'

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name='سبد خرید')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='محصول')
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد')
    size = models.CharField(max_length=10, blank=True, verbose_name='سایز')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ اضافه')

    class Meta:
        verbose_name = 'آیتم سبد خرید'
        verbose_name_plural = 'آیتم‌های سبد خرید'
        unique_together = ['cart', 'product', 'size']

    def __str__(self):
        return f'{self.product.name} - {self.quantity}'

    @property
    def total_price(self):
        return self.quantity * self.product.final_price

class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('processing', 'در حال پردازش'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
        ('returned', 'مرجوع شده'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='کاربر')
    order_number = models.CharField(max_length=20, unique=True, verbose_name='شماره سفارش')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending', verbose_name='وضعیت')
    
    # Contact Information
    first_name = models.CharField(max_length=50, verbose_name='نام')
    last_name = models.CharField(max_length=50, verbose_name='نام خانوادگی')
    email = models.EmailField(verbose_name='ایمیل')
    phone = models.CharField(max_length=15, verbose_name='شماره تلفن')
    
    # Address Information
    address = models.TextField(verbose_name='آدرس')
    city = models.CharField(max_length=50, verbose_name='شهر')
    postal_code = models.CharField(max_length=10, verbose_name='کد پستی')
    
    # Order Details
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='جمع اولیه')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name='هزینه ارسال')
    total = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='مجموع')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    
    # Notes
    notes = models.TextField(blank=True, verbose_name='یادداشت')

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارشات'
        ordering = ['-created_at']

    def __str__(self):
        return f'سفارش {self.order_number}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            import random
            import string
            self.order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='سفارش')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='محصول')
    quantity = models.PositiveIntegerField(verbose_name='تعداد')
    size = models.CharField(max_length=10, blank=True, verbose_name='سایز')
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='قیمت واحد')
    total = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='قیمت کل')

    class Meta:
        verbose_name = 'آیتم سفارش'
        verbose_name_plural = 'آیتم‌های سفارش'

    def __str__(self):
        return f'{self.product.name} - {self.quantity}'

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.price
        super().save(*args, **kwargs)
