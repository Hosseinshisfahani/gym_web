from django.contrib import admin
from .models import Category, Product, ProductImage, Cart, CartItem, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'name_en', 'description']
    prepopulated_fields = {'slug': ('name_en',)}
    list_editable = ['is_active']

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'discount_price', 'stock', 'is_featured', 'is_active', 'created_at']
    list_filter = ['category', 'is_featured', 'is_active', 'created_at', 'brand']
    search_fields = ['name', 'name_en', 'description', 'brand']
    prepopulated_fields = {'slug': ('name_en',)}
    list_editable = ['price', 'discount_price', 'stock', 'is_featured', 'is_active']
    inlines = [ProductImageInline]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'name_en', 'slug', 'category', 'short_description', 'description')
        }),
        ('قیمت و موجودی', {
            'fields': ('price', 'discount_price', 'stock')
        }),
        ('مشخصات محصول', {
            'fields': ('available_sizes', 'weight', 'brand', 'material', 'color')
        }),
        ('تصویر', {
            'fields': ('image',)
        }),
        ('تنظیمات', {
            'fields': ('is_featured', 'is_active')
        })
    )

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['total_price']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    inlines = [CartItemInline]
    readonly_fields = ['total_price', 'total_items']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total', 'created_at']
    list_filter = ['status', 'created_at', 'city']
    search_fields = ['order_number', 'user__username', 'first_name', 'last_name', 'email', 'phone']
    list_editable = ['status']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات سفارش', {
            'fields': ('order_number', 'user', 'status', 'notes')
        }),
        ('اطلاعات تماس', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('آدرس', {
            'fields': ('address', 'city', 'postal_code')
        }),
        ('مبالغ', {
            'fields': ('subtotal', 'shipping_cost', 'total')
        }),
        ('تاریخ', {
            'fields': ('created_at', 'updated_at')
        })
    )

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text', 'image']
    list_filter = ['product__category']
    search_fields = ['product__name', 'alt_text']
