from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Product

@login_required
@never_cache
def products(request):
    product_list = (
        Product.objects
        .filter(
            is_active=True,
            is_deleted=False
        )
        .select_related("category", "main_image")
        .prefetch_related("images", "variants")
        .order_by("-id")
    )

    paginator = Paginator(product_list, 9)
    page_number = request.GET.get("page")
    products_page = paginator.get_page(page_number)

    return render(
        request,
        "product.html",
        {
            "products": products_page
        }
    )

@login_required
@never_cache
def products_details(request, name):

    product = (
        Product.objects
        .filter(
            name=name,
            is_deleted=False
        )
        .select_related("category", "main_image")
        .prefetch_related("images", "variants")
        .first()
    )

    if product is None:
        return render(
            request,
            "products_details.html",
            {
                "product": None,
                "message": "Product not found."
            },
            status=404
        )


    related_products = (
        Product.objects
        .filter(
            category=product.category,
            is_active=True,
            is_deleted=False
        )
        .exclude(id=product.id)
        .select_related("category", "main_image")
        .prefetch_related("images")
        .order_by("-id")[:3]
    )


    return render(
        request,
        "products_details.html",
        {
            "product": product,
            "related_products": related_products
        }
    )

