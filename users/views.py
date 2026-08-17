from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import timedelta
import secrets
import uuid
from . import forms
from . import models
from .models import UserProfile
from products.models import Product

def generate_otp(email):

    models.OTP.objects.filter(
        email=email,
        is_used=False,
        is_verified=False
    ).update(is_used=True)

    otp_code = "".join(str(secrets.randbelow(10)) for _ in range(6))

    otp = models.OTP.objects.create(
        email=email,
        otp_hash=make_password(otp_code),
        expires_at=timezone.now() + timedelta(minutes=1),
    )

    return otp, otp_code


@never_cache
def signin(request):

    if request.user.is_authenticated:

        if request.user.is_superuser:
            return redirect("customadmin:dashboard")

        return redirect("users:home")

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect("users:signin")

        
        if user.is_superuser:

            user = authenticate(
                request,
                username=user.username,
                password=password
            )

            if user is not None:
                login(request, user)
                return redirect("customadmin:dashboard")

            messages.error(request, "Invalid email or password.")
            return redirect("users:signin")

        
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found.")
            return redirect("users:signin")

        if profile.blocked or not user.is_active:
            messages.error(
                request,
                "Your account has been blocked. Please contact the administrator."
            )
            return redirect("users:signin")

        user = authenticate(
            request,
            username=user.username,
            password=password
        )

        if user is not None:

            login(request, user)

            messages.success(
                request,
                f"Welcome {user.first_name}!"
            )

            return redirect("users:home")

        messages.error(request, "Invalid email or password.")
        return redirect("users:signin")

    return render(request, "signin.html")

@never_cache
def signup(request):
    if request.user.is_authenticated:
        return redirect("users:home")

    if request.method == "POST":
        form = forms.SignupForm(request.POST)

        if form.is_valid():

            # Store signup data in session
            request.session["signup_data"] = {
                "first_name": form.cleaned_data["first_name"],
                "last_name": form.cleaned_data["last_name"],
                "email": form.cleaned_data["email"],
                "password": form.cleaned_data["password1"],
                "phone": form.cleaned_data["phone"],
            }

            otp, otp_code = generate_otp(form.cleaned_data["email"])

            # Send OTP email
            send_mail(
                subject="Your OTP Verification Code",
                message=f"""
                        Hi {form.cleaned_data['first_name']},

                        Your signup OTP is: {otp_code}

                        It is valid for 1 minute.

                        --- HAPPY SHOPPING ---

                        Best Regards,
                        Team Vertex
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[form.cleaned_data["email"]],
                fail_silently=False,
            )

            messages.success(request, "OTP sent to your email.")
            return redirect("users:verify_otp")

    else:
        form = forms.SignupForm()

    return render(request, "signup.html", {"form": form})

@never_cache
def verify_view(request):

    signup_data = request.session.get("signup_data")
    reset_data = request.session.get("password_reset_data")
    if signup_data:
        verification_type = "signup"
        email = signup_data["email"]

    elif reset_data:
        verification_type = "password_reset"
        email = reset_data["email"]

    else:
        messages.error(request, "Session expired. Please try again.")
        return redirect("users:signin")

    
    otp = models.OTP.objects.filter(
        email=email,
        is_used=False,
        is_verified=False
    ).order_by("-created_at").first()

    if request.method == "POST":

        form = forms.OTPVerificationForm(request.POST)

        if form.is_valid():

            if otp is None:
                messages.error(
                    request,
                    "No active OTP found. Please request a new OTP."
                )
                return redirect("users:forgot_password"
                                if verification_type == "password_reset"
                                else "users:signup")

            entered = form.cleaned_data["otp"]

            
            if otp.is_used:

                messages.error(
                    request,
                    "OTP has already been used."
                )

            
            elif otp.is_verified:

                messages.error(
                    request,
                    "OTP has already been verified."
                )

            elif timezone.now() > otp.expires_at:

                otp.is_used = True
                otp.save(update_fields=["is_used"])

                messages.error(
                    request,
                    "OTP expired. Please request a new OTP."
                )

            
            elif otp.attempts >= otp.max_attempts:

                otp.is_used = True
                otp.save(update_fields=["is_used"])

                messages.error(
                    request,
                    "Maximum verification attempts exceeded. Please request a new OTP."
                )

            else:

                otp.attempts += 1

                if check_password(entered, otp.otp_hash):

                    otp.is_verified = True
                    otp.is_used = True

                    otp.save(
                        update_fields=[
                            "attempts",
                            "is_verified",
                            "is_used"
                        ]
                    )

                    if verification_type == "signup":

                        username = (
                            f"{signup_data['first_name'].lower()}_"
                            f"{uuid.uuid4().hex[:8]}"
                        )

                        user = User.objects.create_user(
                            username=username,
                            first_name=signup_data["first_name"],
                            last_name=signup_data["last_name"],
                            email=signup_data["email"],
                            password=signup_data["password"],
                            is_active=True,
                        )

                        models.UserProfile.objects.create(
                            user=user,
                            phone=signup_data["phone"]
                        )

                        request.session.pop("signup_data", None)

                        messages.success(
                            request,
                            "Account created successfully."
                        )

                        return redirect("users:signin")
                    
                    elif verification_type == "password_reset":

                        request.session["password_reset_verified"] = True

                        messages.success(
                            request,
                            "Email verified successfully. You can now reset your password."
                        )

                        return redirect("users:reset_password")

                else:

                    otp.save(update_fields=["attempts"])

                    remaining = otp.max_attempts - otp.attempts

                    if remaining <= 0:

                        otp.is_used = True
                        otp.save(update_fields=["is_used"])

                        messages.error(
                            request,
                            "Maximum verification attempts exceeded. Please request a new OTP."
                        )

                    else:

                        messages.error(
                            request,
                            f"Invalid OTP. {remaining} attempt(s) remaining."
                        )

    else:
        form = forms.OTPVerificationForm()

    return render(
        request,
        "verify_otp.html",
        {
            "form": form,
            "email": email,
            "expires_at": otp.expires_at if otp else None,
            "verification_type": verification_type,
        }
    )

@never_cache
def resend_otp(request):

    signup_data = request.session.get("signup_data")
    reset_data = request.session.get("password_reset_data")


    if signup_data:

        verification_type = "signup"

        email = signup_data["email"]
        first_name = signup_data["first_name"]

        otp, otp_code = generate_otp(email)

        send_mail(
            subject="Your OTP Verification Code",

            message=f"""
                    Hi {first_name},

                    Your new signup OTP is: {otp_code}

                    This OTP is valid for 1 minute.

                    --- HAPPY SHOPPING ---

                    Best Regards,
                    Team Vertex
                                """,

            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )


    elif reset_data:

        verification_type = "password_reset"

        email = reset_data["email"]

        user = User.objects.filter(
            id=reset_data["user_id"]
        ).first()

        if not user:

            messages.error(
                request,
                "User account not found."
            )

            request.session.pop(
                "password_reset_data",
                None
            )

            return redirect(
                "users:forgot_password"
            )

        otp, otp_code = generate_otp(email)

        send_mail(
            subject="Password Reset OTP",

            message=f"""
                        Hi {user.first_name},

                        Your new password reset OTP is: {otp_code}

                        This OTP is valid for 1 minute.

                        If you did not request a password reset, please ignore this email.

                        --- HAPPY SHOPPING ---

                        Best Regards,
                        Team Vertex
                                    """,

            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )


    else:

        messages.error(
            request,
            "Session expired. Please try again."
        )

        return redirect(
            "users:signin"
        )


    messages.success(
        request,
        "A new OTP has been sent to your email."
    )

    return redirect(
        "users:verify_otp"
    )

@never_cache
def forgot_password(request):

    if request.user.is_authenticated:
        return redirect("users:home")

    if request.method == "POST":

        email = request.POST.get("email", "").strip().lower()

        if not email:
            messages.error(
                request,
                "Please enter your email address."
            )
            return redirect("users:forgot_password")

        user = User.objects.filter(
            email__iexact=email
        ).first()

        if not user:
            messages.error(
                request,
                "No account found with this email address."
            )
            return redirect("users:forgot_password")

        
        request.session.pop("password_reset_verified", None)

        
        request.session["password_reset_data"] = {
            "email": email,
            "user_id": user.id,
        }

        
        otp, otp_code = generate_otp(email)

        
        send_mail(
            subject="Password Reset OTP",
            message=f"""
                        Hi {user.first_name},

                        Your password reset OTP is: {otp_code}

                        This OTP is valid for 1 minute.

                        If you did not request a password reset, please ignore this email.

                        --- HAPPY SHOPPING ---

                        Best Regards,
                        Team Vertex
                                    """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(
            request,
            "OTP has been sent to your email."
        )

        
        return redirect("users:verify_otp")

    return render(
        request,
        "forgot_password.html"
    )

@never_cache
def reset_password(request):

    reset_data = request.session.get("password_reset_data")
    reset_verified = request.session.get("password_reset_verified")

    if not reset_data or not reset_verified:

        messages.error(request,"Please verify your OTP first.")
        return redirect("users:forgot_password")

    if request.method == "POST":
        form = forms.ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password"]
            user = User.objects.filter(id=reset_data["user_id"]).first()
            if not user:
                messages.error(request,"User account not found.")
                request.session.pop("password_reset_data",None)
                request.session.pop("password_reset_verified",None)
                return redirect("users:signin")
            user.set_password(new_password)
            user.save(update_fields=["password"])
            request.session.pop("password_reset_data",None)
            request.session.pop("password_reset_verified",None)
            messages.success(request,"Password reset successfully. Please sign in.")
            return redirect("users:signin")
    else:
        form = forms.ResetPasswordForm()
    return render(request,"reset_password.html",{ "form": form })

@never_cache
@login_required
def home(request):
    if request.user.is_superuser:
        return redirect("customadmin:dashboard")

    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        logout(request)
        return redirect("users:signin")

    if profile.blocked or not request.user.is_active:
        logout(request)
        messages.error(
            request,
            "Your account has been blocked. Please contact the administrator."
        )
        return redirect("users:signin")

    # Get active, non-deleted products
    products = Product.objects.filter(
        is_deleted=False,
        is_active=True
    ).select_related(
        "category",
        "main_image"
    ).order_by("-id")

    return render(request, "home.html", {
        "products": products
    })

@never_cache
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("users:signin")