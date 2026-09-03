from django.urls import path

from . import views


app_name = "orders"

urlpatterns = [

    path(
        "checkout/",
        views.checkout,
        name="checkout"
    ),

    path(
        "success/",
        views.order_success,
        name="order_success"
    ),

    path(
        "orders/",
        views.order_list,
        name="order_list"
    ),

    path(
        "detail/",
        views.order_detail,
        name="order_detail"
    ),

    path(
        "cancel/",
        views.cancel_order,
        name="cancel_order"
    ),

    path(
        "cancel-item/",
        views.cancel_order_item,
        name="cancel_order_item"
    ),

    path(
        "return/",
        views.return_order,
        name="return_order"
    ),

    path(
        "invoice/",
        views.download_invoice,
        name="download_invoice"
    ),
]