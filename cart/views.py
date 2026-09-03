from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from products.models import Product
from .models import Cart,Wishlist

MAX_CART_QUANTITY = 5

@login_required
def cart_view(request):
    
    cart_items = Cart.objects.filter(
        user=request.user
    ).select_related(
        "product",
        "product__category"
    )

    cart_total = 0

    has_invalid_items = False
    has_out_of_stock_items = False
    has_exceeded_stock_items = False

    for item in cart_items:

        product = item.product
        item.is_invalid = False
        item.is_out_of_stock = False
        item.has_exceeded_stock = False

        if not product:
            item.is_invalid = True
            has_invalid_items = True

            item.subtotal = 0
            continue


        product_invalid = (
            not product.is_active
            or getattr(product, "is_blocked", False)
        )

        
        category_invalid = False

        if not product.category:
            category_invalid = True
        else:
            category_invalid = (
                product.category.is_trashed
                or getattr(
                    product.category,
                    "is_blocked",
                    False
                )
            )


        if product_invalid or category_invalid:
            item.is_invalid = True
            has_invalid_items = True

    
        if product.quantity <= 0:

            item.is_out_of_stock = True
            has_out_of_stock_items = True

        elif item.quantity > product.quantity:

            item.has_exceeded_stock = True
            has_exceeded_stock_items = True

        if product.discount_price:
            price = product.discount_price
        else:
            price = product.sale_price

        if (not item.is_invalid and not item.is_out_of_stock and not item.has_exceeded_stock):
            item.subtotal = price * item.quantity
            cart_total += item.subtotal
        else :
             item.subtotal = 0

    shipping_charge = 0

    grand_total = cart_total + shipping_charge

    context = {
        "cart_items": cart_items,

        "cart_total": cart_total,
        "shipping_charge": shipping_charge,
        "grand_total": grand_total,

        "has_invalid_items": has_invalid_items,
        "has_out_of_stock_items": has_out_of_stock_items,
        "has_exceeded_stock_items": has_exceeded_stock_items,
    }

    return render(
        request,
        "cart.html",
        context
    )


@login_required
@transaction.atomic
def add_to_cart(request):
    
    if request.method != "POST":
        return redirect("products:products")

    product_id = request.POST.get("product_id")

    if not product_id:
        messages.error(
            request,
            "Product not found."
        )
        return redirect("products:products")

    product = Product.objects.filter(
        id=product_id
    ).select_related(
        "category"
    ).first()

    if not product:
        messages.error(
            request,
            "Product not found."
        )
        return redirect("products:products")

    if not product.is_active:

        messages.error(
            request,
            "This product is currently unavailable."
        )

        return redirect(
            "products:products_details",
            product.name
        )

    if getattr(product, "is_blocked", False):

        messages.error(
            request,
            "This product is currently unavailable."
        )

        return redirect(
            "products:products_details",
            product.name
        )

    
    if not product.category:

        messages.error(
            request,
            "This product is currently unavailable."
        )

        return redirect(
            "products:products_details",
            product.name
        )

    if  product.category.is_trashed:

        messages.error(
            request,
            "This product category is currently unavailable."
        )

        return redirect(
            "products:products_details",
            product.name
        )

    if getattr(
        product.category,
        "is_blocked",
        False
    ):

        messages.error(
            request,
            "This product category is currently unavailable."
        )

        return redirect(
            "products:products_details",
            product.name
        )

    if product.quantity <= 0:

        messages.error(
            request,
            "This product is out of stock."
        )

        return redirect(
            "products:products_details",
            product.name
        )

    cart_item = Cart.objects.filter(
        user=request.user,
        product=product
    ).first()

    if cart_item:

        if cart_item.quantity >= MAX_CART_QUANTITY:
            messages.warning(
                request,
                f"You can add a maximum of {MAX_CART_QUANTITY} items of this product."
            )
            return redirect("cart:cart")

        if cart_item.quantity >= product.quantity:

            messages.warning(
                request,
                f"Only {product.quantity} item(s) are available."
            )

            return redirect("cart:cart")

        cart_item.quantity += 1

        cart_item.save(
            update_fields=["quantity"]
        )

        messages.success(
            request,
            "Product quantity increased."
        )

    else:

        Cart.objects.create(
            user=request.user,
            product=product,
            quantity=1
        )

        wishlist_item = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).first()

        if wishlist_item:
            wishlist_item.delete()

        messages.success(
            request,
            "Product added to cart."
        )

    return redirect("cart:cart")


@login_required
@transaction.atomic
def increment_cart(request):
    
    if request.method != "POST":
        return redirect("cart:cart")

    cart_id = request.POST.get("cart_id")

    if not cart_id:

        messages.error(
            request,
            "Cart item not found."
        )

        return redirect("cart:cart")

    cart_item = Cart.objects.filter(
        id=cart_id,
        user=request.user
    ).select_related(
        "product",
        "product__category"
    ).first()

    if not cart_item:

        messages.error(
            request,
            "Cart item not found."
        )

        return redirect("cart:cart")

    product = cart_item.product

    if not product:

        messages.error(
            request,
            "Product is no longer available."
        )

        return redirect("cart:cart")


    if (
        not product.is_active
        or getattr(product, "is_blocked", False)
    ):

        messages.error(
            request,
            "This product is no longer available."
        )

        return redirect("cart:cart")

    if not product.category:

        messages.error(
            request,
            "This product is no longer available."
        )

        return redirect("cart:cart")

    if (
         product.category.is_trashed
        or getattr(
            product.category,
            "is_blocked",
            False
        )
    ):

        messages.error(
            request,
            "This product category is no longer available."
        )

        return redirect("cart:cart")


    if product.quantity <= 0:

        messages.error(
            request,
            "This product is out of stock."
        )

        return redirect("cart:cart")

    if cart_item.quantity >= MAX_CART_QUANTITY:
        messages.warning(
            request,
             f"You can add a maximum of {MAX_CART_QUANTITY} items of this product."
             )
        return redirect("cart:cart")

    if cart_item.quantity >= product.quantity:

        messages.warning(
            request,
            f"Maximum available quantity is {product.quantity}."
        )

        return redirect("cart:cart")

    cart_item.quantity += 1

    cart_item.save(
        update_fields=["quantity"]
    )

    messages.success(
        request,
        "Quantity increased."
    )

    return redirect("cart:cart")


@login_required
@transaction.atomic
def decrement_cart(request):

    if request.method != "POST":
        return redirect("cart:cart")

    cart_id = request.POST.get("cart_id")

    if not cart_id:

        messages.error(
            request,
            "Cart item not found."
        )

        return redirect("cart:cart")

    cart_item = Cart.objects.filter(
        id=cart_id,
        user=request.user
    ).first()

    if not cart_item:

        messages.error(
            request,
            "Cart item not found."
        )

        return redirect("cart:cart")

    if cart_item.quantity > 1:

        cart_item.quantity -= 1

        cart_item.save(
            update_fields=["quantity"]
        )

        messages.success(
            request,
            "Quantity decreased."
        )

    else:

        cart_item.delete()

        messages.success(
            request,
            "Product removed from cart."
        )

    return redirect("cart:cart")


@login_required
def remove_from_cart(request):

    if request.method == "POST":

        item_id = request.POST.get("item_id")

        if not item_id:
            messages.error(
                request,
                "Cart item not found."
            )
            return redirect("cart:cart")

        cart_item = Cart.objects.filter(
            id=item_id,
            user=request.user
        ).first()

        if cart_item:
            cart_item.delete()

            messages.success(
                request,
                "Product removed from cart."
            )
        else:
            messages.error(
                request,
                "Cart item not found."
            )

    return redirect("cart:cart")

@login_required
def add_to_wishlist(request):

    if request.method != "POST":
        return redirect("products:products_list")

    product_id = request.POST.get("product_id")

    if not product_id:
        messages.error(request, "Invalid product.")
        return redirect("products:products_list")

    product = Product.objects.filter(
        id=product_id
    ).first()

    if not product:
        messages.error(request, "Product not found.")
        return redirect("products:products_list")

    
    already_in_cart = Cart.objects.filter(
        user=request.user,
        product=product
    ).exists()

    if already_in_cart:
        messages.info(
            request,
            "This product is already in your cart."
        )
        return redirect("cart:wishlist_view")

    # Don't add duplicate wishlist item
    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    messages.success(
        request,
        "Product added to wishlist."
    )

    return redirect("cart:wishlist_view")


@login_required
def wishlist_view(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related(
        "product",
        "product__category"
    )

    # Remove products that are already in cart.
    cart_product_ids = Cart.objects.filter(
        user=request.user
    ).values_list(
        "product_id",
        flat=True
    )

    wishlist_items = wishlist_items.exclude(
        product_id__in=cart_product_ids
    )

    return render(
        request,
        "wishlist.html",
        {
            "wishlist_items": wishlist_items
        }
    )


@login_required
def remove_from_wishlist(request):

    if request.method != "POST":
        return redirect("cart:wishlist_view")

    product_id = request.POST.get("product_id")

    if product_id:

        Wishlist.objects.filter(
            user=request.user,
            product_id=product_id
        ).delete()

        messages.success(
            request,
            "Product removed from wishlist."
        )

    return redirect("cart:wishlist_view")