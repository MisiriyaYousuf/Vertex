from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.cache import never_cache
from cart.models import Cart
from users.models import Address
from .forms import CheckoutForm
from .models import Order, OrderItem
from decimal import Decimal
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import  redirect, render
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


@never_cache
@login_required
def checkout(request):

    cart_items = Cart.objects.filter(
        user=request.user
    ).select_related(
        "product"
    )

    if not cart_items.exists():

        messages.error(
            request,
            "Your cart is empty."
        )

        return redirect(
            "cart:cart_view"
        )

    addresses = Address.objects.filter(
        user=request.user
    ).order_by(
        "-is_default",
        "-created_at"
    )

    if not addresses.exists():

        messages.error(
            request,
            "Please add a delivery address first."
        )

        return redirect(
            "users:add_address"
        )
    has_invalid_items = False

    for item in cart_items:

        if not item.product:

            has_invalid_items = True
            break

        if not item.product.is_active:

            has_invalid_items = True
            break

        if item.product.is_deleted:

            has_invalid_items = True
            break

        if item.product.quantity <= 0:

            has_invalid_items = True
            break

        if item.quantity > item.product.quantity:

            has_invalid_items = True
            break

    if has_invalid_items:

        messages.error(
            request,
            "Some products in your cart are unavailable or have insufficient stock."
        )

        return redirect(
            "cart:cart_view"
        )
    
    subtotal = Decimal("0.00")
    discount = Decimal("0.00")

    for item in cart_items:

        product = item.product

        if product.discount_price:

            price = product.discount_price

            item_discount = (
                product.sale_price - product.discount_price
            ) * item.quantity

        else:

            price = product.sale_price
            item_discount = Decimal("0.00")

        item_total = price * item.quantity

        subtotal += item_total
        discount += item_discount

    tax = Decimal("0.00")
    shipping_charge = Decimal("0.00")
    grand_total = (
        subtotal
        - discount
        + tax
        + shipping_charge
    )

    if request.method == "POST":

        form = CheckoutForm(
            request.user,
            request.POST
        )

        if form.is_valid():

            selected_address = form.cleaned_data[
                "address"
            ]

            payment_method = form.cleaned_data[
                "payment_method"
            ]

            with transaction.atomic():

                # Re-check stock inside transaction
                for item in cart_items:

                    product = item.product

                    if item.quantity > product.quantity:

                        messages.error(
                            request,
                            f"Only {product.quantity} item(s) of "
                            f"{product.name} are available."
                        )

                        return redirect(
                            "cart:cart_view"
                        )

                

                order = Order.objects.create(

                    user=request.user,

                    address=selected_address,

                    payment_method=payment_method,

                    status="Pending",

                    subtotal=subtotal,

                    discount=discount,

                    tax=tax,

                    shipping_charge=shipping_charge,

                    total_amount=grand_total
                )


                for item in cart_items:

                    product = item.product

                    if product.discount_price:

                        price = product.discount_price

                        item_discount = (
                            product.sale_price
                            - product.discount_price
                        ) * item.quantity

                    else:

                        price = product.sale_price
                        item_discount = Decimal("0.00")

                    item_total = (
                        price * item.quantity
                    )

                    OrderItem.objects.create(

                        order=order,

                        product=product,

                        product_name=product.name,

                        price=price,

                        quantity=item.quantity,

                        discount=item_discount,

                        item_total=item_total
                    )

                   

                    product.quantity -= item.quantity

                    product.save(
                        update_fields=["quantity"]
                    )

              

                cart_items.delete()

            request.session["last_order_id"] = order.id
            return redirect("orders:order_success")
        
    else:

        form = CheckoutForm(
            request.user,
            initial={
                "address": addresses.filter(
                    is_default=True
                ).first()
            }
        )

    context = {

        "form": form,

        "addresses": addresses,

        "cart_items": cart_items,

        "subtotal": subtotal,

        "discount": discount,

        "tax": tax,

        "shipping_charge": shipping_charge,

        "grand_total": grand_total,
    }

    return render(
        request,
        "checkout.html",
        context
    )

@never_cache
@login_required
def order_success(request):

    order_id = request.session.get("last_order_id")

    if not order_id:
        return redirect("orders:order_list")

    order = (
        Order.objects
        .prefetch_related("items")
        .filter(
            id=order_id,
            user=request.user
        )
        .first()
    )

    if not order:
        return redirect("orders:order_list")

    return render(
        request,
        "order_success.html",
        {
            "order": order
        }
    )

@login_required
@never_cache
def order_detail(request):

    if request.method != "POST":
        return redirect("orders:order_list")

    order_id = request.POST.get("order_id")

    if not order_id:
        messages.error(
            request,
            "Order not found."
        )
        return redirect("orders:order_list")

    order = (
        Order.objects
        .prefetch_related("items")
        .select_related("address")
        .filter(
            id=order_id,
            user=request.user
        )
        .first()
    )

    if not order:
        messages.error(
            request,
            "Order not found."
        )
        return redirect("orders:order_list")

    return render(
        request,
        "order_detail.html",
        {
            "order": order
        }
    )

@login_required
@never_cache
def order_list(request):

    orders = (
        Order.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    search = request.GET.get(
        "search",
        ""
    ).strip()

    if search:

        orders = orders.filter(
            Q(id__icontains=search)
        )

    return render(
        request,
        "order_list.html",
        {
            "orders": orders,
            "search": search,
        }
    )

@login_required
@transaction.atomic
def cancel_order(request):

    if request.method != "POST":

        return redirect(
            "orders:order_list"
        )

    order_id = request.POST.get("order_id")

    if not order_id:

        messages.error(
            request,
            "Order not found."
        )

        return redirect(
            "orders:order_list"
        )

    order = (
        Order.objects
        .select_for_update()
        .filter(
            id=order_id,
            user=request.user
        )
        .first()
    )

    if not order:

        messages.error(
            request,
            "Order not found."
        )

        return redirect(
            "orders:order_list"
        )

    if order.status in [
        "Delivered",
        "Cancelled"
    ]:

        messages.error(
            request,
            "This order cannot be cancelled."
        )

        return redirect(
            "orders:order_list"
        )

    reason = request.POST.get(
        "cancellation_reason",
        ""
    ).strip()

    for item in order.items.select_for_update():

        if not item.is_cancelled:

            item.product.quantity += item.quantity

            item.product.save(
                update_fields=["quantity"]
            )

            item.is_cancelled = True

            item.cancellation_reason = reason

            item.save(
                update_fields=[
                    "is_cancelled",
                    "cancellation_reason"
                ]
            )

    order.status = "Cancelled"

    order.cancellation_reason = reason

    order.save(
        update_fields=[
            "status",
            "cancellation_reason",
            "updated_at"
        ]
    )

    messages.success(
        request,
        "Order cancelled successfully."
    )

    return redirect(
        "orders:order_list"
    )

@login_required
@transaction.atomic
def cancel_order_item(request):

    if request.method != "POST":

        return redirect(
            "orders:order_list"
        )

    order_id = request.POST.get(
        "order_id"
    )

    item_id = request.POST.get(
        "item_id"
    )

    if not order_id or not item_id:

        messages.error(
            request,
            "Order or product not found."
        )

        return redirect(
            "orders:order_list"
        )

    order = (
        Order.objects
        .select_for_update()
        .filter(
            id=order_id,
            user=request.user
        )
        .first()
    )

    if not order:

        messages.error(
            request,
            "Order not found."
        )

        return redirect(
            "orders:order_list"
        )

    item = (
        OrderItem.objects
        .select_for_update()
        .filter(
            id=item_id,
            order=order
        )
        .first()
    )

    if not item:

        messages.error(
            request,
            "Product not found."
        )

        return redirect(
            "orders:order_list"
        )

    if order.status in [
        "Delivered",
        "Cancelled"
    ]:

        messages.error(
            request,
            "This product cannot be cancelled."
        )

        return redirect(
            "orders:order_list"
        )

    if item.is_cancelled:

        messages.error(
            request,
            "This product is already cancelled."
        )

        return redirect(
            "orders:order_list"
        )

    reason = request.POST.get(
        "cancellation_reason",
        ""
    ).strip()

    item.product.quantity += item.quantity

    item.product.save(
        update_fields=["quantity"]
    )

    item.is_cancelled = True

    item.cancellation_reason = reason

    item.save(
        update_fields=[
            "is_cancelled",
            "cancellation_reason"
        ]
    )

    remaining_items = order.items.filter(
        is_cancelled=False
    ).exists()

    if not remaining_items:

        order.status = "Cancelled"

        order.cancellation_reason = reason

        order.save(
            update_fields=[
                "status",
                "cancellation_reason",
                "updated_at"
            ]
        )

    messages.success(
        request,
        "Product cancelled successfully."
    )

    return redirect(
        "orders:order_list"
    )

@login_required
@transaction.atomic
def return_order(request):

    if request.method != "POST":

        return redirect(
            "orders:order_list"
        )

    order_id = request.POST.get(
        "order_id"
    )

    if not order_id:

        messages.error(
            request,
            "Order not found."
        )

        return redirect(
            "orders:order_list"
        )

    order = (
        Order.objects
        .select_for_update()
        .filter(
            id=order_id,
            user=request.user
        )
        .first()
    )

    if not order:

        messages.error(
            request,
            "Order not found."
        )

        return redirect(
            "orders:order_list"
        )

    if order.status != "Delivered":

        messages.error(
            request,
            "Only delivered orders can be returned."
        )

        return redirect(
            "orders:order_list"
        )

    reason = request.POST.get(
        "return_reason",
        ""
    ).strip()

    if not reason:

        messages.error(
            request,
            "Return reason is required."
        )

        return redirect(
            "orders:order_list"
        )

    for item in order.items.select_for_update():

        if not item.is_cancelled and not item.is_returned:

            item.product.quantity += item.quantity

            item.product.save(
                update_fields=["quantity"]
            )

            item.is_returned = True

            item.return_reason = reason

            item.save(
                update_fields=[
                    "is_returned",
                    "return_reason"
                ]
            )

    order.status = "Cancelled"

    order.return_reason = reason

    order.save(
        update_fields=[
            "status",
            "return_reason",
            "updated_at"
        ]
    )

    messages.success(
        request,
        "Order returned successfully."
    )

    return redirect(
        "orders:order_list"
    )

@login_required
def download_invoice(request):

    if request.method != "POST":

        return redirect(
            "orders:order_list"
        )

    order_id = request.POST.get(
        "order_id"
    )

    if not order_id:

        messages.error(
            request,
            "Order not found."
        )

        return redirect(
            "orders:order_list"
        )

    order = (
        Order.objects
        .prefetch_related("items")
        .filter(
            id=order_id,
            user=request.user
        )
        .first()
    )

    if not order:

        messages.error(
            request,
            "Order not found."
        )

        return redirect(
            "orders:order_list"
        )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; '
        f'filename="invoice_order_{order.id}.pdf"'
    )

    pdf = canvas.Canvas(
        response,
        pagesize=A4
    )

    width, height = A4

    y = height - 50

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.drawString(
        50,
        y,
        "INVOICE"
    )

    y -= 35

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        50,
        y,
        f"Order ID: {order.id}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Order Date: "
        f"{order.created_at.strftime('%d %b %Y')}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Payment: "
        f"{order.get_payment_method_display()}"
    )

    y -= 40

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        50,
        y,
        "Products"
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        10
    )

    for item in order.items.all():

        if item.is_cancelled:
            continue

        if item.is_returned:
            continue

        text = (
            f"{item.product_name} | "
            f"Qty: {item.quantity} | "
            f"₹{item.item_total}"
        )

        pdf.drawString(
            50,
            y,
            text
        )

        y -= 20

        if y < 80:

            pdf.showPage()

            y = height - 50

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Subtotal: ₹{order.subtotal}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Discount: ₹{order.discount}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Tax: ₹{order.tax}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Shipping: ₹{order.shipping_charge}"
    )

    y -= 30

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        50,
        y,
        f"Grand Total: ₹{order.total_amount}"
    )

    pdf.save()

    return response