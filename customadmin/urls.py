from django.urls import path
from . import views

app_name = 'customadmin' 
urlpatterns = [
    path('',views.dashboard,name='dashboard'),
    path("logout/", views.logout_view, name="logout"),
    path("users/",views.user_management,name="user_management"),
    path("users/block/",views.block_user,name="block_user"),
    path("users/unblock/",views.unblock_user,name="unblock_user"),
    path("categories/",views.category_management,name="category_management"),
    path("categories/edit/",views.edit_category,name="edit_category"),
    path("categories/delete/",views.delete_category,name="delete_category"),
    path('list-product/', views.list_product, name='list_product'),
    path('products/add/', views.add_product, name='add_product'),
    path('product/<int:product_id>/', views.view_product, name='view_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
]
