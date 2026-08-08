from django.urls import path
from . import views

app_name = 'customadmin' 
urlpatterns = [
    path('',views.dashboard,name='dashboard'),
    path("logout/", views.logout_view, name="logout"),
    path("users/",views.user_management,name="user_management"),
    path("users/block/<int:profile_id>/",views.block_user,name="block_user"),
    path("users/unblock/<int:profile_id>/",views.unblock_user,name="unblock_user"),
]
