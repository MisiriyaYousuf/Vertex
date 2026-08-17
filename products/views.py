from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from .models import Product

def products(request):

    products_list = Product.objects.all().order_by('-id')     
    paginator = Paginator(products_list, 6)  
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
        'paginator': paginator,
        'is_paginated': True if paginator.num_pages > 1 else False,
        'page_obj': products,  
    }
    
    return render(request, 'products.html', context)

def products_details(request,product_id):
    product = get_object_or_404(Product, id=product_id, is_deleted=False)
    
    # Get related variants and images if needed
    variants = product.variants.all()
    context = {
        'product': product,
        'variants': variants,
    }
    return render(request,'product_details.html', context)
