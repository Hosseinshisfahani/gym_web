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
    
    @property
    def shipping_cost(self):
        """Calculate shipping cost based on total price"""
        return 0 if self.total_price >= 1000000 else 90000
    
    @property
    def final_total(self):
        """Calculate final total including shipping"""
        return self.total_price + self.shipping_cost

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
    
    @property
    def original_total_price(self):
        return self.quantity * self.product.price

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
    
    PAYMENT_STATUS = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('failed', 'پرداخت ناموفق'),
        ('refunded', 'بازگشت وجه'),
    ]
    
    PAYMENT_METHOD = [
        ('online', 'پرداخت آنلاین'),
        ('cod', 'پرداخت در محل'),
        ('transfer', 'انتقال بانکی'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='کاربر')
    order_number = models.CharField(max_length=20, unique=True, verbose_name='شماره سفارش')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending', verbose_name='وضعیت')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending', verbose_name='وضعیت پرداخت')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='online', verbose_name='روش پرداخت')
    
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
    
    # Shipping
    tracking_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='کد رهگیری')

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


# User Shipping Address Model
class UserShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses', verbose_name='کاربر')
    first_name = models.CharField(max_length=50, verbose_name='نام')
    last_name = models.CharField(max_length=50, verbose_name='نام خانوادگی')
    phone = models.CharField(max_length=15, verbose_name='شماره تلفن')
    address = models.TextField(verbose_name='آدرس کامل')
    city = models.CharField(max_length=50, verbose_name='شهر')
    postal_code = models.CharField(max_length=10, verbose_name='کد پستی')
    is_default = models.BooleanField(default=False, verbose_name='آدرس پیش‌فرض')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'آدرس ارسال کاربر'
        verbose_name_plural = 'آدرس‌های ارسال کاربران'

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.city}'

    def save(self, *args, **kwargs):
        # If this is set as default, remove default from other addresses
        if self.is_default:
            UserShippingAddress.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# مدیریت مالی فروشگاه (Shop Financial Management)
class ShopIncome(models.Model):
    INCOME_TYPE_CHOICES = [
        ('product_sale', 'فروش محصول'),
        ('shipping_fee', 'هزینه ارسال'),
        ('other', 'سایر درآمدها'),
    ]
    
    INCOME_STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('confirmed', 'تایید شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='عنوان درآمد')
    income_type = models.CharField(max_length=20, choices=INCOME_TYPE_CHOICES, verbose_name='نوع درآمد')
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='مبلغ (تومان)')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    status = models.CharField(max_length=20, choices=INCOME_STATUS_CHOICES, default='confirmed', verbose_name='وضعیت')
    date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ')
    
    # ارتباط با سفارش (اختیاری)
    related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='incomes', verbose_name='سفارش مرتبط')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'درآمد فروشگاه'
        verbose_name_plural = 'درآمدهای فروشگاه'
        ordering = ['-date']

    def __str__(self):
        return f'{self.title} - {self.amount:,} تومان'

class ShopExpense(models.Model):
    EXPENSE_TYPE_CHOICES = [
        ('product_purchase', 'خرید محصول'),
        ('shipping_cost', 'هزینه ارسال'),
        ('marketing', 'تبلیغات'),
        ('rent', 'اجاره'),
        ('salary', 'حقوق'),
        ('utilities', 'آب، برق، گاز'),
        ('maintenance', 'نگهداری'),
        ('packaging', 'بسته‌بندی'),
        ('website', 'وب‌سایت'),
        ('other', 'سایر هزینه‌ها'),
    ]
    
    EXPENSE_STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('paid', 'پرداخت شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='عنوان هزینه')
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, verbose_name='نوع هزینه')
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='مبلغ (تومان)')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    status = models.CharField(max_length=20, choices=EXPENSE_STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ')
    
    # فایل رسید (اختیاری)
    receipt_file = models.FileField(upload_to='shop/receipts/', blank=True, null=True, verbose_name='فایل رسید')
    
    # ارتباط با محصول (اختیاری)
    related_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses', verbose_name='محصول مرتبط')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'هزینه فروشگاه'
        verbose_name_plural = 'هزینه‌های فروشگاه'
        ordering = ['-date']

    def __str__(self):
        return f'{self.title} - {self.amount:,} تومان'

class ShopSalesReport(models.Model):
    REPORT_PERIOD_CHOICES = [
        ('daily', 'روزانه'),
        ('weekly', 'هفتگی'),
        ('monthly', 'ماهانه'),
        ('yearly', 'سالانه'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='عنوان گزارش')
    report_period = models.CharField(max_length=20, choices=REPORT_PERIOD_CHOICES, verbose_name='دوره گزارش')
    start_date = models.DateField(verbose_name='تاریخ شروع')
    end_date = models.DateField(verbose_name='تاریخ پایان')
    
    # آمار فروش
    total_orders = models.PositiveIntegerField(default=0, verbose_name='تعداد سفارشات')
    total_revenue = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='کل درآمد')
    total_profit = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='کل سود')
    
    # آمار محصولات
    total_products_sold = models.PositiveIntegerField(default=0, verbose_name='تعداد محصولات فروخته شده')
    best_selling_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='best_selling_reports', verbose_name='پرفروش‌ترین محصول')
    
    # آمار مشتریان
    new_customers = models.PositiveIntegerField(default=0, verbose_name='مشتریان جدید')
    returning_customers = models.PositiveIntegerField(default=0, verbose_name='مشتریان برگشتی')
    
    # وضعیت سفارشات
    pending_orders = models.PositiveIntegerField(default=0, verbose_name='سفارشات در انتظار')
    completed_orders = models.PositiveIntegerField(default=0, verbose_name='سفارشات تکمیل شده')
    cancelled_orders = models.PositiveIntegerField(default=0, verbose_name='سفارشات لغو شده')
    
    # گزارش خودکار
    is_auto_generated = models.BooleanField(default=False, verbose_name='گزارش خودکار')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'گزارش فروش'
        verbose_name_plural = 'گزارشات فروش'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.title} ({self.start_date} تا {self.end_date})'
    
    def calculate_profit_margin(self):
        """محاسبه درصد سود"""
        if self.total_revenue > 0:
            return (self.total_profit / self.total_revenue) * 100
        return 0
    
    @property
    def average_order_value(self):
        """محاسبه میانگین مبلغ سفارش"""
        if self.total_orders > 0:
            return self.total_revenue / self.total_orders
        return 0
