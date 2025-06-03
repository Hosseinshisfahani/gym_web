from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Category, Product, Cart, CartItem, Order, OrderItem

def shop_home(request):
    """صفحه اصلی فروشگاه"""
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    categories = Category.objects.filter(is_active=True)
    latest_products = Product.objects.filter(is_active=True)[:12]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'latest_products': latest_products,
    }
    return render(request, 'gym_shop/home.html', context)

def product_list(request):
    """لیست محصولات با قابلیت فیلتر و جستجو"""
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)
    
    # فیلتر بر اساس دسته‌بندی
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # جستجو
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__icontains=search_query)
        )
    
    # مرتب‌سازی
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    
    # فیلتر قیمت
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # صفحه‌بندی
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'gym_shop/product_list.html', context)

def product_detail(request, slug):
    """جزئیات محصول"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'gym_shop/product_detail.html', context)

def category_detail(request, slug):
    """محصولات یک دسته‌بندی"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True)
    
    # مرتب‌سازی
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    
    # صفحه‌بندی
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'sort_by': sort_by,
    }
    return render(request, 'gym_shop/category_detail.html', context)

@login_required
def cart_view(request):
    """مشاهده سبد خرید"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
    }
    return render(request, 'gym_shop/cart.html', context)

@login_required
@require_POST
def add_to_cart(request):
    """اضافه کردن محصول به سبد خرید"""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    size = request.POST.get('size', '')
    
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # بررسی موجودی
    if quantity > product.stock:
        messages.error(request, 'تعداد درخواستی بیشتر از موجودی انبار است.')
        return redirect('gym_shop:product_detail', slug=product.slug)
    
    # اضافه کردن یا بروزرسانی آیتم سبد خرید
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=size,
        defaults={'quantity': quantity}
    )
    
    if not created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            messages.error(request, 'تعداد درخواستی بیشتر از موجودی انبار است.')
            return redirect('gym_shop:product_detail', slug=product.slug)
        cart_item.quantity = new_quantity
        cart_item.save()
    
    messages.success(request, f'{product.name} به سبد خرید اضافه شد.')
    return redirect('gym_shop:cart')

@login_required
def update_cart_item(request):
    """بروزرسانی آیتم سبد خرید"""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        if quantity > cart_item.product.stock:
            messages.error(request, 'تعداد درخواستی بیشتر از موجودی انبار است.')
        elif quantity <= 0:
            cart_item.delete()
            messages.success(request, 'محصول از سبد خرید حذف شد.')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'سبد خرید بروزرسانی شد.')
    
    return redirect('gym_shop:cart')

@login_required
def remove_from_cart(request, item_id):
    """حذف آیتم از سبد خرید"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, f'{cart_item.product.name} از سبد خرید حذف شد.')
    return redirect('gym_shop:cart')

@login_required
def checkout(request):
    """صفحه تسویه حساب"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.exists():
        messages.error(request, 'سبد خرید شما خالی است.')
        return redirect('gym_shop:cart')
    
    if request.method == 'POST':
        # ایجاد سفارش جدید
        order = Order.objects.create(
            user=request.user,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            postal_code=request.POST.get('postal_code'),
            subtotal=cart.total_price,
            shipping_cost=50000,  # هزینه ارسال ثابت
            total=cart.total_price + 50000,
            notes=request.POST.get('notes', '')
        )
        
        # اضافه کردن آیتم‌های سفارش
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                size=cart_item.size,
                price=cart_item.product.final_price,
                total=cart_item.total_price
            )
            
            # کم کردن از موجودی
            cart_item.product.stock -= cart_item.quantity
            cart_item.product.save()
        
        # خالی کردن سبد خرید
        cart.items.all().delete()
        
        messages.success(request, f'سفارش شما با شماره {order.order_number} ثبت شد.')
        return redirect('gym_shop:order_detail', order_number=order.order_number)
    
    context = {
        'cart': cart,
        'shipping_cost': 50000,
        'total_with_shipping': cart.total_price + 50000,
    }
    return render(request, 'gym_shop/checkout.html', context)

@login_required
def order_detail(request, order_number):
    """جزئیات سفارش"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'gym_shop/order_detail.html', context)

@login_required
def order_list(request):
    """لیست سفارشات کاربر"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'gym_shop/order_list.html', context)

@csrf_exempt
def get_cart_count(request):
    """دریافت تعداد آیتم‌های سبد خرید برای AJAX"""
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.total_items
        except Cart.DoesNotExist:
            count = 0
    else:
        count = 0
    
    return JsonResponse({'count': count})
