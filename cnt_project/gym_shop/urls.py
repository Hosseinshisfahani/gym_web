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
    
    # لیست علاقه‌مندی‌ها
    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    
    # API endpoints
    path('api/product/<int:product_id>/quick-view/', views.product_quick_view, name='product_quick_view'),
    
    # تسویه حساب و سفارش
    path('checkout/', views.checkout, name='checkout'),
    path('invoice/<int:order_id>/', views.invoice_preview, name='invoice_preview'),
    path('proceed-payment/<int:order_id>/', views.proceed_to_payment, name='proceed_to_payment'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('apply-discount/', views.apply_discount, name='apply_discount'),
    path('orders/', views.order_list, name='order_list'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/', views.order_detail_by_id, name='order_detail_by_id'),  # For backward compatibility
    path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    
    # مدیریت مالی فروشگاه (Shop Financial Management)
    path('admin/financial/', views.shop_financial_dashboard, name='shop_financial_dashboard'),
    path('admin/income/', views.shop_income_management, name='shop_income_management'),
    path('admin/expense/', views.shop_expense_management, name='shop_expense_management'),
    path('admin/income/add/', views.add_shop_income, name='add_shop_income'),
    path('admin/expense/add/', views.add_shop_expense, name='add_shop_expense'),
    path('admin/reports/', views.shop_sales_reports, name='shop_sales_reports'),
    path('admin/reports/generate/', views.generate_sales_report, name='generate_sales_report'),
    path('admin/income/update/<int:income_id>/', views.update_income_status, name='update_income_status'),
    path('admin/expense/update/<int:expense_id>/', views.update_expense_status, name='update_expense_status'),
    path('admin/financial/api/', views.financial_api_data, name='financial_api_data'),
    
    # مدیریت محصولات (Product Management)
    path('admin/products/', views.product_management, name='product_management'),
    path('admin/products/add/', views.add_product, name='add_product'),
    path('admin/products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('admin/products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('admin/products/toggle-status/<int:product_id>/', views.toggle_product_status, name='toggle_product_status'),
    path('admin/products/toggle-featured/<int:product_id>/', views.toggle_product_featured, name='toggle_product_featured'),
    
    # مدیریت دسته‌بندی‌ها (Category Management)
    path('admin/categories/', views.category_management, name='category_management'),
    path('admin/categories/add/', views.add_category, name='add_category'),
    path('admin/categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('admin/categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('admin/categories/toggle-status/<int:category_id>/', views.toggle_category_status, name='toggle_category_status'),
    
    # مدیریت سفارشات (Order Management)
    path('admin/orders/', views.order_management, name='order_management'),
    path('admin/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('admin/orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
    path('admin/orders/export/', views.order_export, name='order_export'),
    path('admin/orders/statistics/', views.order_statistics, name='order_statistics'),
    
    # مدیریت نرخ تبدیل ارز (Exchange Rate Management)
    path('admin/exchange-rate/add/', views.add_exchange_rate, name='add_exchange_rate'),
    path('admin/exchange-rate/activate/', views.activate_exchange_rate, name='activate_exchange_rate'),
    path('admin/update-dollar-prices/', views.update_dollar_prices_view, name='update_dollar_prices'),
] 