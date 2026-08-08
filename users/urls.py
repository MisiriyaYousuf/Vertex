from django.urls import path
from . import views

app_name = "users"

urlpatterns = [

    path("", views.signin, name="signin"),

    path("signup/", views.signup, name="signup"),

    path("verify-otp/", views.verify_view, name="verify_otp"),

    path("resend-otp/", views.resend_otp, name="resend_otp"),

    path("home/", views.home, name="home"),

    path("logout/", views.logout_view, name="logout"),
]
