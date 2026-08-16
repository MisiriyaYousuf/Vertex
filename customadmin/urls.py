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
]
