from django.urls import path
from . import views

app_name = 'gym_shop'

urlpatterns = [
    # صفحه اصلی فروشگاه
    path('', views.shop_home, name='home'),
    
    # محصولات
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # دسته‌بندی‌ها
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # سبد خرید
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/count/', views.get_cart_count, name='cart_count'),
    
    # تسویه حساب و سفارش
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
] 