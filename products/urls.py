from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
path('list/',views.products,name='products'),
path('details/<int:product_id>/', views.products_details, name='product_details'),
]