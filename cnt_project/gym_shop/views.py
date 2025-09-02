from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
from datetime import datetime, timedelta
import json
from django.contrib.auth.models import User

from .models import Category, Product, Cart, CartItem, Order, OrderItem, Wishlist, ProductImage, UserShippingAddress
from gym.templatetags.custom_filters import format_price
from .forms import ProductForm, CategoryForm, ProductImageForm, ProductSearchForm

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

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
    
    # فیلتر رنگ
    color = request.GET.get('color')
    if color:
        products = products.filter(color=color)
    
    # صفحه‌بندی
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get color choices for filter
    color_choices = Product.COLOR_CHOICES
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
        'color': color,
        'color_choices': color_choices,
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
    cart_items = cart.items.all()
    
    # Calculate total discount
    total_original_price = sum(item.quantity * item.product.price for item in cart_items)
    total_discount = total_original_price - cart.total_price if cart.total_price < total_original_price else 0
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_discount': total_discount,
    }
    return render(request, 'gym_shop/cart.html', context)

@login_required
@require_POST
def add_to_cart(request):
    """اضافه کردن محصول به سبد خرید"""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    size = request.POST.get('size', '')
    color = request.POST.get('color', '')
    
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # بررسی موجودی
    if quantity > product.stock:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'تعداد درخواستی بیشتر از موجودی انبار است.'
            })
        messages.error(request, 'تعداد درخواستی بیشتر از موجودی انبار است.')
        return redirect('gym_shop:product_detail', slug=product.slug)
    
    # اضافه کردن یا بروزرسانی آیتم سبد خرید
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=size,
        color=color,
        defaults={'quantity': quantity}
    )
    
    if not created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'تعداد درخواستی بیشتر از موجودی انبار است.'
                })
            messages.error(request, 'تعداد درخواستی بیشتر از موجودی انبار است.')
            return redirect('gym_shop:product_detail', slug=product.slug)
        cart_item.quantity = new_quantity
        cart_item.save()
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.name} به سبد خرید اضافه شد.',
            'cart_count': cart.total_items
        })
    
    # Handle regular form submissions
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
@require_POST
def toggle_wishlist(request):
    """اضافه/حذف محصول از لیست علاقه‌مندی‌ها"""
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # بررسی وجود محصول در لیست علاقه‌مندی‌ها
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        # محصول به لیست علاقه‌مندی‌ها اضافه شد
        is_favorited = True
        message = f'{product.name} به لیست علاقه‌مندی‌ها اضافه شد!'
    else:
        # محصول از لیست علاقه‌مندی‌ها حذف شد
        wishlist_item.delete()
        is_favorited = False
        message = f'{product.name} از لیست علاقه‌مندی‌ها حذف شد!'
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_favorited': is_favorited,
            'message': message
        })
    
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'gym_shop:product_list'))

@login_required
def wishlist_view(request):
    """نمایش لیست علاقه‌مندی‌های کاربر"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    
    context = {
        'wishlist_items': wishlist_items,
        'total_items': wishlist_items.count()
    }
    
    return render(request, 'gym_shop/wishlist.html', context)

def product_quick_view(request, product_id):
    """API endpoint for quick view modal"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Generate the HTML content for the modal
        html_content = f"""
        <div class="row">
            <div class="col-md-6">
                <div class="text-center">
                    {f'<img src="{product.image.url}" class="img-fluid rounded" alt="{product.name}" style="max-height: 300px;">' if product.image else '<div class="bg-light rounded d-flex align-items-center justify-content-center" style="height: 300px;"><i class="fas fa-image fa-3x text-muted"></i></div>'}
                </div>
            </div>
            <div class="col-md-6">
                <h4 class="mb-3">{product.name}</h4>
                <p class="text-muted mb-3">{product.short_description}</p>
                
                <div class="mb-3">
                    <span class="badge bg-primary">{product.category.name}</span>
                    {f'<span class="badge bg-secondary ms-2">{product.brand}</span>' if product.brand else ''}
                </div>
                
                <div class="price-section mb-3">
                    {f'''
                    <div class="d-flex align-items-center">
                        <span class="h4 text-success me-3">{format_price(product.discount_price)} تومان</span>
                        <span class="text-muted text-decoration-line-through">{format_price(product.price)} تومان</span>
                        <span class="badge bg-danger ms-2">{((product.price - product.discount_price) / product.price * 100):.0f}% تخفیف</span>
                    </div>
                    ''' if hasattr(product, 'discount_price') and product.discount_price else f'<span class="h4 text-success">{format_price(product.price)} تومان</span>'}
                </div>
                
                <div class="stock-info mb-3">
                    {f'<span class="text-success"><i class="fas fa-check-circle me-1"></i> موجود ({product.stock} عدد)</span>' if product.stock > 0 else '<span class="text-danger"><i class="fas fa-times-circle me-1"></i> ناموجود</span>'}
                </div>
                
                {f'''
                <div class="mb-3">
                    <small class="text-muted">رنگ‌های موجود:</small><br>
                    {product.available_colors}
                </div>
                ''' if product.available_colors else ''}
                
                {f'''
                <div class="mb-3">
                    <small class="text-muted">سایزهای موجود:</small><br>
                    {product.available_sizes}
                </div>
                ''' if product.available_sizes else ''}
                
                {f'''
                <div class="mb-3">
                    <small class="text-muted">وزن:</small> {product.weight} کیلوگرم
                </div>
                ''' if product.weight else ''}
            </div>
        </div>
        
        {f'''
        <div class="row mt-4">
            <div class="col-12">
                <h6>توضیحات:</h6>
                <p class="text-muted">{product.description[:200]}{'...' if len(product.description) > 200 else ''}</p>
            </div>
        </div>
        ''' if product.description else ''}
        """
        
        return JsonResponse({
            'success': True,
            'html': html_content,
            'product_url': request.build_absolute_uri(product.get_absolute_url())
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطا در بارگیری اطلاعات محصول'
        })

@login_required
def checkout(request):
    """صفحه تسویه حساب"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.exists():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'success': False,
                'message': 'سبد خرید شما خالی است.'
            }, encoder=DecimalEncoder)
        messages.error(request, 'سبد خرید شما خالی است.')
        return redirect('gym_shop:cart')
    
    if request.method == 'POST':
        try:
            # Use cart's shipping cost calculation
            shipping_cost = cart.shipping_cost
            
            # Handle combined full name field
            full_name = request.POST.get('full_name', '').strip()
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
            elif len(name_parts) == 1:
                first_name = name_parts[0]
                last_name = ''
            else:
                first_name = ''
                last_name = ''
            
            # Calculate tax (12% on subtotal + shipping)
            taxable_amount = cart.total_price + shipping_cost
            tax_amount = int(taxable_amount * Decimal('0.12'))
            final_total = cart.total_price + shipping_cost + tax_amount
            
            # Create pending order first
            order = Order.objects.create(
                user=request.user,
                first_name=first_name,
                last_name=last_name,
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                postal_code=request.POST.get('postal_code'),
                subtotal=cart.total_price,
                shipping_cost=shipping_cost,
                tax_amount=tax_amount,
                total=final_total,
                notes=request.POST.get('notes', ''),
                status='pending',  # Set status to pending until payment is verified
                payment_status='pending',  # Payment is pending
                payment_method='online'  # Default to online payment
            )
            
            # Add order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    size=cart_item.size,
                    color=cart_item.color,
                    price=cart_item.product.final_price,
                    total=cart_item.total_price
                )
            
            # Save shipping address for future use
            try:
                # Check if this exact address already exists for the user
                existing_address = UserShippingAddress.objects.filter(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    phone=request.POST.get('phone'),
                    address=request.POST.get('address'),
                    city=request.POST.get('city'),
                    postal_code=request.POST.get('postal_code'),
                ).first()
                
                if not existing_address:
                    # Create new shipping address
                    UserShippingAddress.objects.create(
                        user=request.user,
                        first_name=first_name,
                        last_name=last_name,
                        phone=request.POST.get('phone'),
                        address=request.POST.get('address'),
                        city=request.POST.get('city'),
                        postal_code=request.POST.get('postal_code'),
                        # Set as default if user doesn't have any addresses yet
                        is_default=not UserShippingAddress.objects.filter(user=request.user).exists()
                    )
            except Exception as e:
                # Log error but don't fail the order
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving shipping address: {str(e)}")
            
            # Redirect to invoice preview page instead of directly to payment gateway
            from django.urls import reverse
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({
                    'success': True,
                    'message': 'در حال انتقال به صفحه پیش‌فاکتور...',
                    'redirect_url': reverse('gym_shop:invoice_preview', kwargs={'order_id': order.id})
                }, encoder=DecimalEncoder)
            else:
                # Redirect to invoice preview
                return redirect('gym_shop:invoice_preview', order_id=order.id)
                
        except Exception as e:
            # Handle any errors during order creation
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating order: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({
                    'success': False,
                    'message': 'خطا در ثبت سفارش. لطفاً مجدداً تلاش کنید.'
                }, encoder=DecimalEncoder)
            else:
                messages.error(request, 'خطا در ثبت سفارش. لطفاً مجدداً تلاش کنید.')
                return redirect('gym_shop:checkout')
    
    # Get user's saved shipping addresses
    user_addresses = UserShippingAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    default_address = user_addresses.filter(is_default=True).first()
    
    # Calculate tax for display
    taxable_amount = cart.total_price + cart.shipping_cost
    tax_amount = int(taxable_amount * Decimal('0.12'))
    total_with_tax = cart.total_price + cart.shipping_cost + tax_amount
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
        'subtotal': cart.total_price,
        'shipping_cost': cart.shipping_cost,
        'tax_amount': tax_amount,
        'total_with_tax': total_with_tax,
        'total': cart.final_total,
        'user_addresses': user_addresses,
        'default_address': default_address,
    }
    return render(request, 'gym_shop/checkout.html', context)

@login_required
def invoice_preview(request, order_id):
    """نمایش پیش‌فاکتور سفارش"""
    order = get_object_or_404(Order, id=order_id, user=request.user, status='pending')
    
    context = {
        'order': order,
    }
    return render(request, 'gym_shop/invoice_preview.html', context)

@login_required
def proceed_to_payment(request, order_id):
    """ادامه به درگاه پرداخت"""
    if request.method != 'POST':
        return redirect('gym_shop:invoice_preview', order_id=order_id)
    
    order = get_object_or_404(Order, id=order_id, user=request.user, status='pending')
    
    try:
        # Initialize payment gateway
        from gym.utils.payment_gateway import PaymentGateway
        from django.urls import reverse
        
        payment_gateway = PaymentGateway()
        callback_url = request.build_absolute_uri(reverse('gym_shop:payment_verify'))
        
        # Create payment request (convert Toman to Rial - multiply by 10)
        amount_in_rial = int(order.total * 10)
        success, payment_data = payment_gateway.create_payment_request(
            amount=amount_in_rial,
            description=f"سفارش {order.order_number} - {order.first_name} {order.last_name}",
            callback_url=callback_url,
            mobile=order.phone,
            email=order.email
        )
        
        if success:
            # Store payment authority in session for verification
            request.session['payment_authority'] = payment_data['authority']
            request.session['order_id'] = order.id
            
            # Clear cart (only after successful payment gateway connection)
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart.items.all().delete()
            
            # Redirect to payment gateway
            return redirect(payment_data['gateway_url'])
        else:
            # Payment gateway error
            error_message = payment_data.get('error', 'خطا در اتصال به درگاه پرداخت')
            messages.error(request, error_message)
            return redirect('gym_shop:invoice_preview', order_id=order.id)
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in payment gateway: {str(e)}")
        messages.error(request, 'خطا در اتصال به درگاه پرداخت. لطفاً مجدداً تلاش کنید.')
        return redirect('gym_shop:invoice_preview', order_id=order.id)

@login_required
def apply_discount(request):
    """اعمال کد تخفیف"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            discount_code = data.get('discount_code', '').strip()
            
            if not discount_code:
                return JsonResponse({
                    'success': False,
                    'message': 'کد تخفیف وارد نشده است.'
                }, encoder=DecimalEncoder)
            
            # بررسی کد تخفیف (در حال حاضر فقط یک کد نمونه)
            # می‌توانید مدل DiscountCode اضافه کنید
            if discount_code.lower() == 'welcome10':
                # کد تخفیف 10 درصد
                discount_percentage = 10
                return JsonResponse({
                    'success': True,
                    'message': f'کد تخفیف {discount_percentage}% با موفقیت اعمال شد.',
                    'discount_percentage': discount_percentage
                }, encoder=DecimalEncoder)
            elif discount_code.lower() == 'summer20':
                # کد تخفیف 20 درصد
                discount_percentage = 20
                return JsonResponse({
                    'success': True,
                    'message': f'کد تخفیف {discount_percentage}% با موفقیت اعمال شد.',
                    'discount_percentage': discount_percentage
                }, encoder=DecimalEncoder)
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'کد تخفیف وارد شده معتبر نیست.'
                }, encoder=DecimalEncoder)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'خطا در پردازش داده‌ها.'
            }, encoder=DecimalEncoder)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'خطا در اعمال کد تخفیف.'
            }, encoder=DecimalEncoder)
    
    return JsonResponse({
        'success': False,
        'message': 'روش درخواست نامعتبر است.'
    }, encoder=DecimalEncoder)

@login_required
def order_detail(request, order_number):
    """جزئیات سفارش با شماره سفارش"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'gym_shop/order_detail.html', context)

@login_required
def order_detail_by_id(request, order_id):
    """جزئیات سفارش با ID (برای سازگاری با نسخه‌های قبلی)"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'gym_shop/order_detail.html', context)

@login_required
def cancel_order(request, order_id):
    """لغو سفارش"""
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, id=order_id, user=request.user)
            
            # بررسی اینکه آیا سفارش قابل لغو است یا نه
            if order.status not in ['pending', 'paid']:
                return JsonResponse({
                    'success': False,
                    'message': 'این سفارش قابل لغو نیست.'
                }, encoder=DecimalEncoder)
            
            # تغییر وضعیت سفارش به لغو شده
            order.status = 'cancelled'
            order.save()
            
            # بازگرداندن موجودی محصولات
            for order_item in order.items.all():
                product = order_item.product
                product.stock += order_item.quantity
                product.save()
            
            return JsonResponse({
                'success': True,
                'message': 'سفارش با موفقیت لغو شد.'
            }, encoder=DecimalEncoder)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error cancelling order: {str(e)}")
            
            return JsonResponse({
                'success': False,
                'message': 'خطا در لغو سفارش.'
            }, encoder=DecimalEncoder)
    
    return JsonResponse({
        'success': False,
        'message': 'روش درخواست نامعتبر است.'
    })

@login_required
def order_list(request):
    """لیست سفارشات کاربر"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Filter by payment status
    payment_status = request.GET.get('payment_status')
    if payment_status:
        orders = orders.filter(payment_status=payment_status)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        orders = orders.filter(order_number__icontains=search_query)
    
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
    
    return JsonResponse({'count': count}, encoder=DecimalEncoder)


# مدیریت مالی فروشگاه (Shop Financial Management)
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ShopIncome, ShopExpense, ShopSalesReport
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator

@staff_member_required
def shop_financial_dashboard(request):
    """داشبورد مالی فروشگاه"""
    # محاسبه آمار کلی
    today = timezone.now().date()
    current_month = today.replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    # درآمد ماه جاری
    current_month_income = ShopIncome.objects.filter(
        date__gte=current_month,
        status='confirmed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # هزینه ماه جاری
    current_month_expense = ShopExpense.objects.filter(
        date__gte=current_month,
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # سود ماه جاری
    current_month_profit = current_month_income - current_month_expense
    
    # درآمد ماه قبل
    last_month_income = ShopIncome.objects.filter(
        date__gte=last_month,
        date__lt=current_month,
        status='confirmed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # هزینه ماه قبل
    last_month_expense = ShopExpense.objects.filter(
        date__gte=last_month,
        date__lt=current_month,
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # محاسبه رشد درآمد
    income_growth = 0
    if last_month_income > 0:
        income_growth = ((current_month_income - last_month_income) / last_month_income) * 100
    
    # آمار سفارشات
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='delivered').count()
    
    # آخرین درآمدها و هزینه‌ها
    recent_incomes = ShopIncome.objects.order_by('-date')[:5]
    recent_expenses = ShopExpense.objects.order_by('-date')[:5]
    
    # محصولات پرفروش
    best_selling_products = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).filter(total_sold__gt=0).order_by('-total_sold')[:5]
    
    context = {
        'current_month_income': current_month_income,
        'current_month_expense': current_month_expense,
        'current_month_profit': current_month_profit,
        'income_growth': income_growth,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'recent_incomes': recent_incomes,
        'recent_expenses': recent_expenses,
        'best_selling_products': best_selling_products,
    }
    return render(request, 'gym_shop/admin/financial_dashboard.html', context)

@staff_member_required
def shop_income_management(request):
    """مدیریت درآمدهای فروشگاه"""
    incomes = ShopIncome.objects.all().order_by('-date')
    
    # فیلتر بر اساس نوع درآمد
    income_type = request.GET.get('income_type')
    if income_type:
        incomes = incomes.filter(income_type=income_type)
    
    # فیلتر بر اساس وضعیت
    status = request.GET.get('status')
    if status:
        incomes = incomes.filter(status=status)
    
    # فیلتر بر اساس تاریخ
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        incomes = incomes.filter(date__gte=date_from)
    if date_to:
        incomes = incomes.filter(date__lte=date_to)
    
    # صفحه‌بندی
    paginator = Paginator(incomes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # محاسبه مجموع درآمد
    total_income = incomes.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'total_income': total_income,
        'income_type': income_type,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'income_types': ShopIncome.INCOME_TYPE_CHOICES,
        'statuses': ShopIncome.INCOME_STATUS_CHOICES,
    }
    return render(request, 'gym_shop/admin/income_management.html', context)

@staff_member_required
def shop_expense_management(request):
    """مدیریت هزینه‌های فروشگاه"""
    expenses = ShopExpense.objects.all().order_by('-date')
    
    # فیلتر بر اساس نوع هزینه
    expense_type = request.GET.get('expense_type')
    if expense_type:
        expenses = expenses.filter(expense_type=expense_type)
    
    # فیلتر بر اساس وضعیت
    status = request.GET.get('status')
    if status:
        expenses = expenses.filter(status=status)
    
    # فیلتر بر اساس تاریخ
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        expenses = expenses.filter(date__gte=date_from)
    if date_to:
        expenses = expenses.filter(date__lte=date_to)
    
    # صفحه‌بندی
    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # محاسبه مجموع هزینه
    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'total_expense': total_expense,
        'expense_type': expense_type,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'expense_types': ShopExpense.EXPENSE_TYPE_CHOICES,
        'statuses': ShopExpense.EXPENSE_STATUS_CHOICES,
    }
    return render(request, 'gym_shop/admin/expense_management.html', context)

@staff_member_required
def add_shop_income(request):
    """افزودن درآمد جدید"""
    if request.method == 'POST':
        title = request.POST.get('title')
        income_type = request.POST.get('income_type')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        related_order_id = request.POST.get('related_order')
        
        # اعتبارسنجی
        if not title or not income_type or not amount:
            messages.error(request, 'لطفاً تمام فیلدهای اجباری را پر کنید.')
            return redirect('gym_shop:add_shop_income')
        
        try:
            amount = float(amount)
        except ValueError:
            messages.error(request, 'مبلغ وارد شده معتبر نیست.')
            return redirect('gym_shop:add_shop_income')
        
        # ایجاد درآمد
        income = ShopIncome.objects.create(
            title=title,
            income_type=income_type,
            amount=amount,
            description=description,
        )
        
        # ارتباط با سفارش (اختیاری)
        if related_order_id:
            try:
                order = Order.objects.get(id=related_order_id)
                income.related_order = order
                income.save()
            except Order.DoesNotExist:
                pass
        
        messages.success(request, 'درآمد جدید با موفقیت اضافه شد.')
        return redirect('gym_shop:shop_income_management')
    
    # دریافت سفارشات برای لیست انتخاب
    orders = Order.objects.all().order_by('-created_at')[:20]
    
    context = {
        'income_types': ShopIncome.INCOME_TYPE_CHOICES,
        'orders': orders,
    }
    return render(request, 'gym_shop/admin/add_income.html', context)

@staff_member_required
def add_shop_expense(request):
    """افزودن هزینه جدید"""
    if request.method == 'POST':
        title = request.POST.get('title')
        expense_type = request.POST.get('expense_type')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        related_product_id = request.POST.get('related_product')
        receipt_file = request.FILES.get('receipt_file')
        
        # اعتبارسنجی
        if not title or not expense_type or not amount:
            messages.error(request, 'لطفاً تمام فیلدهای اجباری را پر کنید.')
            return redirect('gym_shop:add_shop_expense')
        
        try:
            amount = float(amount)
        except ValueError:
            messages.error(request, 'مبلغ وارد شده معتبر نیست.')
            return redirect('gym_shop:add_shop_expense')
        
        # ایجاد هزینه
        expense = ShopExpense.objects.create(
            title=title,
            expense_type=expense_type,
            amount=amount,
            description=description,
            receipt_file=receipt_file,
        )
        
        # ارتباط با محصول (اختیاری)
        if related_product_id:
            try:
                product = Product.objects.get(id=related_product_id)
                expense.related_product = product
                expense.save()
            except Product.DoesNotExist:
                pass
        
        messages.success(request, 'هزینه جدید با موفقیت اضافه شد.')
        return redirect('gym_shop:shop_expense_management')
    
    # دریافت محصولات برای لیست انتخاب
    products = Product.objects.all().order_by('name')
    
    context = {
        'expense_types': ShopExpense.EXPENSE_TYPE_CHOICES,
        'products': products,
    }
    return render(request, 'gym_shop/admin/add_expense.html', context)

@staff_member_required
def shop_sales_reports(request):
    """گزارشات فروش فروشگاه"""
    reports = ShopSalesReport.objects.all().order_by('-start_date')
    
    # فیلتر بر اساس دوره
    report_period = request.GET.get('report_period')
    if report_period:
        reports = reports.filter(report_period=report_period)
    
    # صفحه‌بندی
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'report_period': report_period,
        'report_periods': ShopSalesReport.REPORT_PERIOD_CHOICES,
    }
    return render(request, 'gym_shop/admin/sales_reports.html', context)

@staff_member_required
def generate_sales_report(request):
    """تولید گزارش فروش"""
    if request.method == 'POST':
        title = request.POST.get('title')
        report_period = request.POST.get('report_period')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # اعتبارسنجی
        if not title or not report_period or not start_date or not end_date:
            messages.error(request, 'لطفاً تمام فیلدهای اجباری را پر کنید.')
            return redirect('gym_shop:generate_sales_report')
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'تاریخ وارد شده معتبر نیست.')
            return redirect('gym_shop:generate_sales_report')
        
        if start_date > end_date:
            messages.error(request, 'تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد.')
            return redirect('gym_shop:generate_sales_report')
        
        # محاسبه آمار
        orders_in_period = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        total_orders = orders_in_period.count()
        total_revenue = orders_in_period.aggregate(total=Sum('total'))['total'] or 0
        
        # محاسبه تعداد محصولات فروخته شده
        total_products_sold = OrderItem.objects.filter(
            order__in=orders_in_period
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # پرفروش‌ترین محصول
        best_selling_product = None
        best_selling_data = OrderItem.objects.filter(
            order__in=orders_in_period
        ).values('product').annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold').first()
        
        if best_selling_data:
            best_selling_product = Product.objects.get(id=best_selling_data['product'])
        
        # آمار مشتریان
        customer_data = orders_in_period.values('user').distinct()
        new_customers = 0
        returning_customers = 0
        
        for customer in customer_data:
            first_order = Order.objects.filter(user=customer['user']).order_by('created_at').first()
            if first_order.created_at.date() >= start_date:
                new_customers += 1
            else:
                returning_customers += 1
        
        # وضعیت سفارشات
        pending_orders = orders_in_period.filter(status='pending').count()
        completed_orders = orders_in_period.filter(status='delivered').count()
        cancelled_orders = orders_in_period.filter(status='cancelled').count()
        
        # محاسبه سود (فرض: سود 30% از درآمد)
        total_profit = total_revenue * 0.3
        
        # ایجاد گزارش
        report = ShopSalesReport.objects.create(
            title=title,
            report_period=report_period,
            start_date=start_date,
            end_date=end_date,
            total_orders=total_orders,
            total_revenue=total_revenue,
            total_profit=total_profit,
            total_products_sold=total_products_sold,
            best_selling_product=best_selling_product,
            new_customers=new_customers,
            returning_customers=returning_customers,
            pending_orders=pending_orders,
            completed_orders=completed_orders,
            cancelled_orders=cancelled_orders,
        )
        
        messages.success(request, 'گزارش فروش با موفقیت تولید شد.')
        return redirect('gym_shop:shop_sales_reports')
    
    context = {
        'report_periods': ShopSalesReport.REPORT_PERIOD_CHOICES,
    }
    return render(request, 'gym_shop/admin/generate_report.html', context)

@staff_member_required
def update_income_status(request, income_id):
    """تغییر وضعیت درآمد"""
    if request.method == 'POST':
        income = get_object_or_404(ShopIncome, id=income_id)
        new_status = request.POST.get('status')
        
        if new_status in ['pending', 'confirmed', 'cancelled']:
            income.status = new_status
            income.save()
            messages.success(request, 'وضعیت درآمد بروزرسانی شد.')
        else:
            messages.error(request, 'وضعیت انتخاب شده معتبر نیست.')
    
    return redirect('gym_shop:shop_income_management')

@staff_member_required
def update_expense_status(request, expense_id):
    """تغییر وضعیت هزینه"""
    if request.method == 'POST':
        expense = get_object_or_404(ShopExpense, id=expense_id)
        new_status = request.POST.get('status')
        
        if new_status in ['pending', 'paid', 'cancelled']:
            expense.status = new_status
            expense.save()
            messages.success(request, 'وضعیت هزینه بروزرسانی شد.')
        else:
            messages.error(request, 'وضعیت انتخاب شده معتبر نیست.')
    
    return redirect('gym_shop:shop_expense_management')

@staff_member_required
def financial_api_data(request):
    """API برای دریافت داده‌های مالی جهت نمایش نمودار"""
    # داده‌های درآمد و هزینه 6 ماه اخیر
    months_data = []
    for i in range(6):
        date = timezone.now().date().replace(day=1) - timedelta(days=30*i)
        next_month = (date + timedelta(days=32)).replace(day=1)
        
        income = ShopIncome.objects.filter(
            date__gte=date,
            date__lt=next_month,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expense = ShopExpense.objects.filter(
            date__gte=date,
            date__lt=next_month,
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        months_data.append({
            'month': date.strftime('%Y-%m'),
            'income': float(income),
            'expense': float(expense),
            'profit': float(income - expense)
        })
    
    months_data.reverse()
    
    return JsonResponse({
        'months_data': months_data,
        'success': True
    }, encoder=DecimalEncoder)


# Product Management Views
@staff_member_required
def product_management(request):
    """مدیریت محصولات"""
    # فرم جستجو
    search_form = ProductSearchForm(request.GET)
    products = Product.objects.all()
    
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        category = search_form.cleaned_data.get('category')
        is_active = search_form.cleaned_data.get('is_active')
        is_featured = search_form.cleaned_data.get('is_featured')
        color = search_form.cleaned_data.get('color')
        
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(brand__icontains=search_query)
            )
        
        if category:
            products = products.filter(category=category)
        
        if is_active == 'true':
            products = products.filter(is_active=True)
        elif is_active == 'false':
            products = products.filter(is_active=False)
        
        if is_featured == 'true':
            products = products.filter(is_featured=True)
        elif is_featured == 'false':
            products = products.filter(is_featured=False)
        
        if color:
            products = products.filter(color=color)
    
    # صفحه‌بندی
    paginator = Paginator(products, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # آمار
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    featured_products = Product.objects.filter(is_featured=True).count()
    out_of_stock = Product.objects.filter(stock=0).count()
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_products': total_products,
        'active_products': active_products,
        'featured_products': featured_products,
        'out_of_stock': out_of_stock,
    }
    return render(request, 'gym_shop/admin/product_management.html', context)

@staff_member_required
def add_product(request):
    """افزودن محصول جدید"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'محصول "{product.name}" با موفقیت اضافه شد.')
            return redirect('gym_shop:product_management')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'افزودن محصول جدید',
    }
    return render(request, 'gym_shop/admin/add_edit_product.html', context)

@staff_member_required
def edit_product(request, product_id):
    """ویرایش محصول"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'محصول "{product.name}" با موفقیت ویرایش شد.')
            return redirect('gym_shop:product_management')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': 'ویرایش محصول',
    }
    return render(request, 'gym_shop/admin/add_edit_product.html', context)

@staff_member_required
def delete_product(request, product_id):
    """حذف محصول"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'محصول "{product_name}" با موفقیت حذف شد.')
        return redirect('gym_shop:product_management')
    
    context = {
        'product': product,
    }
    return render(request, 'gym_shop/admin/delete_product.html', context)

@staff_member_required
def toggle_product_status(request, product_id):
    """تغییر وضعیت فعال/غیرفعال محصول"""
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save()
    
    status = 'فعال' if product.is_active else 'غیرفعال'
    messages.success(request, f'وضعیت محصول "{product.name}" به {status} تغییر کرد.')
    
    return redirect('gym_shop:product_management')

@staff_member_required
def toggle_product_featured(request, product_id):
    """تغییر وضعیت محصول ویژه"""
    product = get_object_or_404(Product, id=product_id)
    product.is_featured = not product.is_featured
    product.save()
    
    status = 'ویژه' if product.is_featured else 'معمولی'
    messages.success(request, f'محصول "{product.name}" به {status} تغییر کرد.')
    
    return redirect('gym_shop:product_management')

# Category Management Views
@staff_member_required
def category_management(request):
    """مدیریت دسته‌بندی‌ها"""
    categories = Category.objects.all()
    
    # آمار
    total_categories = Category.objects.count()
    active_categories = Category.objects.filter(is_active=True).count()
    
    context = {
        'categories': categories,
        'total_categories': total_categories,
        'active_categories': active_categories,
    }
    return render(request, 'gym_shop/admin/category_management.html', context)

@staff_member_required
def add_category(request):
    """افزودن دسته‌بندی جدید"""
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'دسته‌بندی "{category.name}" با موفقیت اضافه شد.')
            return redirect('gym_shop:category_management')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'افزودن دسته‌بندی جدید',
    }
    return render(request, 'gym_shop/admin/add_edit_category.html', context)

@staff_member_required
def edit_category(request, category_id):
    """ویرایش دسته‌بندی"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'دسته‌بندی "{category.name}" با موفقیت ویرایش شد.')
            return redirect('gym_shop:category_management')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': 'ویرایش دسته‌بندی',
    }
    return render(request, 'gym_shop/admin/add_edit_category.html', context)

@staff_member_required
def delete_category(request, category_id):
    """حذف دسته‌بندی"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'دسته‌بندی "{category_name}" با موفقیت حذف شد.')
        return redirect('gym_shop:category_management')
    
    context = {
        'category': category,
    }
    return render(request, 'gym_shop/admin/delete_category.html', context)

@staff_member_required
def toggle_category_status(request, category_id):
    """تغییر وضعیت فعال/غیرفعال دسته‌بندی"""
    category = get_object_or_404(Category, id=category_id)
    category.is_active = not category.is_active
    category.save()
    
    status = 'فعال' if category.is_active else 'غیرفعال'
    messages.success(request, f'وضعیت دسته‌بندی "{category.name}" به {status} تغییر کرد.')
    
    return redirect('gym_shop:category_management')

# Order Management Views
@staff_member_required
def order_management(request):
    """مدیریت سفارشات"""
    orders = Order.objects.all().order_by('-created_at')
    
    # فیلتر بر اساس وضعیت
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # فیلتر بر اساس تاریخ
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        orders = orders.filter(created_at__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__lte=date_to)
    
    # جستجو
    search_query = request.GET.get('search')
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # صفحه‌بندی
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # آمار
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    processing_orders = Order.objects.filter(status='processing').count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    
    # محاسبه مجموع فروش
    total_sales = Order.objects.exclude(status='cancelled').aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # محاسبه میانگین سفارش
    average_order_value = 0
    if total_orders > 0:
        average_order_value = total_sales / (total_orders - cancelled_orders)
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
        'order_statuses': Order.ORDER_STATUS,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_sales': total_sales,
        'average_order_value': average_order_value,
    }
    return render(request, 'gym_shop/admin/order_management.html', context)

@staff_member_required
def admin_order_detail(request, order_id):
    """جزئیات سفارش برای ادمین"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
        'order_statuses': Order.ORDER_STATUS,
    }
    return render(request, 'gym_shop/admin/order_detail.html', context)

@staff_member_required
def update_order_status(request, order_id):
    """به‌روزرسانی وضعیت سفارش"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        if new_status in dict(Order.ORDER_STATUS):
            old_status = order.get_status_display()
            order.status = new_status
            order.save()
            
            # اگر سفارش لغو شد، موجودی محصولات را بازگردان
            if new_status == 'cancelled' and order.status != 'cancelled':
                for item in order.items.all():
                    item.product.stock += item.quantity
                    item.product.save()
            
            new_status_display = order.get_status_display()
            messages.success(request, f'وضعیت سفارش {order.order_number} از "{old_status}" به "{new_status_display}" تغییر کرد.')
            
            # اگر درخواست AJAX باشد، پاسخ JSON برگردان
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'وضعیت سفارش به {new_status_display} تغییر کرد.',
                    'new_status': new_status,
                    'new_status_display': new_status_display
                }, encoder=DecimalEncoder)
        else:
            messages.error(request, 'وضعیت انتخاب شده معتبر نیست.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'وضعیت انتخاب شده معتبر نیست.'
                }, encoder=DecimalEncoder)
    
    return redirect('gym_shop:admin_order_detail', order_id=order_id)

@staff_member_required
def delete_order(request, order_id):
    """حذف سفارش"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        # بازگرداندن موجودی محصولات
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()
        
        order_number = order.order_number
        order.delete()
        
        messages.success(request, f'سفارش {order_number} با موفقیت حذف شد.')
        return redirect('gym_shop:order_management')
    
    context = {
        'order': order,
    }
    return render(request, 'gym_shop/admin/delete_order.html', context)

@staff_member_required
def order_export(request):
    """صادرات سفارشات به فایل Excel"""
    import xlsxwriter
    from django.http import HttpResponse
    import io
    
    # ایجاد فایل Excel در حافظه
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('سفارشات')
    
    # تنظیم فرمت
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D7E4BC',
        'border': 1
    })
    
    # سرستون‌ها
    headers = [
        'شماره سفارش', 'کاربر', 'نام', 'نام خانوادگی', 'ایمیل', 'تلفن',
        'وضعیت', 'مجموع', 'تاریخ ایجاد', 'آدرس', 'شهر'
    ]
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # دریافت سفارشات
    orders = Order.objects.all().order_by('-created_at')
    
    # نوشتن داده‌ها
    for row, order in enumerate(orders, 1):
        worksheet.write(row, 0, order.order_number)
        worksheet.write(row, 1, order.user.username)
        worksheet.write(row, 2, order.first_name)
        worksheet.write(row, 3, order.last_name)
        worksheet.write(row, 4, order.email)
        worksheet.write(row, 5, order.phone)
        worksheet.write(row, 6, order.get_status_display())
        worksheet.write(row, 7, float(order.total))
        worksheet.write(row, 8, order.created_at.strftime('%Y-%m-%d %H:%M'))
        worksheet.write(row, 9, order.address)
        worksheet.write(row, 10, order.city)
    
    # بستن فایل
    workbook.close()
    output.seek(0)
    
    # ایجاد پاسخ HTTP
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="orders.xlsx"'
    
    return response

@staff_member_required
def order_statistics(request):
    """آمار سفارشات"""
    # آمار کلی
    total_orders = Order.objects.count()
    total_revenue = Order.objects.exclude(status='cancelled').aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # آمار بر اساس وضعیت
    status_stats = {}
    for status_code, status_name in Order.ORDER_STATUS:
        count = Order.objects.filter(status=status_code).count()
        status_stats[status_code] = {
            'name': status_name,
            'count': count,
            'percentage': (count / total_orders * 100) if total_orders > 0 else 0
        }
    
    # آمار ماهانه (12 ماه گذشته)
    monthly_stats = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        
        orders_count = Order.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        revenue = Order.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end,
            status__in=['paid', 'processing', 'shipped', 'delivered']
        ).aggregate(total=Sum('total'))['total'] or 0
        
        monthly_stats.append({
            'month': month_start.strftime('%Y-%m'),
            'orders': orders_count,
            'revenue': revenue
        })
    
    monthly_stats.reverse()
    
    # پرفروش‌ترین محصولات
    top_products = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).filter(total_sold__gt=0).order_by('-total_sold')[:10]
    
    # بهترین مشتریان
    top_customers = User.objects.annotate(
        total_orders=Count('orders'),
        total_spent=Sum('orders__total')
    ).filter(total_orders__gt=0).order_by('-total_spent')[:10]
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'status_stats': status_stats,
        'monthly_stats': monthly_stats,
        'top_products': top_products,
        'top_customers': top_customers,
    }
    return render(request, 'gym_shop/admin/order_statistics.html', context)

@login_required
def payment_verify(request):
    """Payment verification - handles payment gateway callback"""
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')
    
    if not authority:
        messages.error(request, 'کد پیگیری یافت نشد.')
        return redirect('gym_shop:order_list')
    
    # Get order from session
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request, 'سفارش یافت نشد.')
        return redirect('gym_shop:order_list')
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, 'سفارش یافت نشد.')
        return redirect('gym_shop:order_list')
    
    if status == 'OK':
        # Payment was successful, verify with gateway
        from gym.utils.payment_gateway import PaymentGateway
        
        payment_gateway = PaymentGateway()
        # Convert Toman to Rial for verification (multiply by 10)
        amount_in_rial = int(order.total * 10)
        success, verification_data = payment_gateway.verify_payment(authority, amount_in_rial)
        
        if success:
            # Update order status to paid
            order.status = 'paid'
            order.payment_status = 'paid'
            order.save()
            
            # Reduce product stock
            for item in order.items.all():
                item.product.stock -= item.quantity
                item.product.save()
            
            # Send email notification
            try:
                from gym.utils.email_notifications import send_shop_order_notification
                send_shop_order_notification(order, request)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send order notification email: {str(e)}")
            
            # Clear session data
            request.session.pop('payment_authority', None)
            request.session.pop('order_id', None)
            
            messages.success(request, f'پرداخت شما با موفقیت انجام شد. شماره سفارش: {order.order_number}')
            return redirect('gym_shop:order_detail', order_number=order.order_number)
        else:
            # Payment verification failed
            order.status = 'cancelled'
            order.payment_status = 'failed'
            order.save()
            
            error_message = verification_data.get('error', 'خطا در تایید پرداخت')
            messages.error(request, f'خطا در تایید پرداخت: {error_message}')
            return redirect('gym_shop:order_list')
    else:
        # Payment was cancelled or failed
        order.status = 'cancelled'
        order.payment_status = 'failed'
        order.save()
        
        messages.error(request, 'پرداخت لغو شد یا با خطا مواجه شد.')
        return redirect('gym_shop:order_list')


def sitemap_xml(request):
    """Generate dynamic sitemap.xml"""
    base_url = "https://shirneshansport.ir"
    
    # Static URLs
    static_urls = [
        {'url': base_url + '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'url': base_url + reverse('gym_shop:home'), 'priority': '0.9', 'changefreq': 'daily'},
        {'url': base_url + reverse('gym_shop:product_list'), 'priority': '0.8', 'changefreq': 'daily'},
    ]
    
    # Category URLs
    category_urls = []
    categories = Category.objects.filter(is_active=True)
    for category in categories:
        category_urls.append({
            'url': base_url + reverse('gym_shop:category_detail', args=[category.slug]),
            'priority': '0.7',
            'changefreq': 'weekly',
            'lastmod': category.updated_at.strftime('%Y-%m-%d') if hasattr(category, 'updated_at') else timezone.now().strftime('%Y-%m-%d')
        })
    
    # Product URLs
    product_urls = []
    products = Product.objects.filter(is_active=True)
    for product in products:
        product_urls.append({
            'url': base_url + reverse('gym_shop:product_detail', args=[product.slug]),
            'priority': '0.6',
            'changefreq': 'weekly',
            'lastmod': product.updated_at.strftime('%Y-%m-%d') if hasattr(product, 'updated_at') else timezone.now().strftime('%Y-%m-%d')
        })
    
    # Combine all URLs
    all_urls = static_urls + category_urls + product_urls
    
    # Generate XML
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'''
    
    for url_data in all_urls:
        xml_content += f'''
    <url>
        <loc>{url_data['url']}</loc>
        <priority>{url_data['priority']}</priority>
        <changefreq>{url_data['changefreq']}</changefreq>'''
        if 'lastmod' in url_data:
            xml_content += f'''
        <lastmod>{url_data['lastmod']}</lastmod>'''
        xml_content += '''
    </url>'''
    
    xml_content += '''
</urlset>'''
    
    return HttpResponse(xml_content, content_type='application/xml')
