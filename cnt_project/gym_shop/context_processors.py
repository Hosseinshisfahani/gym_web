from .models import Category

def categories_processor(request):
    """Context processor to make categories available globally"""
    categories = Category.objects.filter(is_active=True).order_by('name')
    return {'categories': categories} 