from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
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
        return redirect("home")

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect("users:signin")

        user = authenticate(
            request,
            username=user.username,   
            password=password
        )

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome {user.first_name}!")
            return redirect("home")

        messages.error(request, "Invalid email or password.")

    return render(request, "signin.html")

@never_cache
def signup(request):
    if request.user.is_authenticated:
        return redirect("home")

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
                "city": form.cleaned_data["city"],
                "country": form.cleaned_data["country"],
                "address": form.cleaned_data["address"],
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

    if not signup_data:
        messages.error(request, "Session expired.")
        return redirect("users:signup")

    otp = models.OTP.objects.filter(
        email=signup_data["email"],
        is_used=False,
        is_verified=False,
    ).first()

    if request.method == "POST":

        form = forms.OTPVerificationForm(request.POST)

        if form.is_valid():

            if otp is None:
                messages.error(request, "No active OTP found.")
                return redirect("users:signup")

            entered = form.cleaned_data["otp"]

            if otp.is_used:
                messages.error(request, "OTP has already been used.")

            elif otp.is_verified:
                messages.error(request, "OTP has already been verified.")

            elif timezone.now() > otp.expires_at:

                otp.is_used = True
                otp.save(update_fields=["is_used"])

                messages.error(request, "OTP expired. Please register again.")
                return redirect("users:signup")

            elif otp.attempts >= otp.max_attempts:

                otp.is_used = True
                otp.save(update_fields=["is_used"])

                messages.error(request, "Maximum verification attempts exceeded.")

            else:

                otp.attempts += 1

                if check_password(entered, otp.otp_hash):

                    otp.is_verified = True
                    otp.is_used = True
                    otp.save(update_fields=["attempts", "is_verified", "is_used"])

                    username = f"{signup_data['first_name'].lower()}_{uuid.uuid4().hex[:8]}"

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
                        phone=signup_data["phone"],
                        city=signup_data["city"],
                        country=signup_data["country"],
                        address=signup_data["address"],
                    )

                    request.session.pop("signup_data", None)

                    messages.success(request, "Account created successfully.")
                    return redirect("users:signin")

                otp.save(update_fields=["attempts"])

                remaining = otp.max_attempts - otp.attempts

                if remaining <= 0:
                    otp.is_used = True
                    otp.save(update_fields=["is_used"])
                    messages.error(request, "Maximum verification attempts exceeded.")
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
            "email": signup_data["email"],
            "expires_at": otp.expires_at if otp else None,
        },
    )

@never_cache
def resend_otp(request):

    signup_data = request.session.get("signup_data")

    if not signup_data:
        messages.error(request, "Session expired.")
        return redirect("users:signup")

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

                    Best Regards
                    Team Vertex
                    """,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    messages.success(request, "A new OTP has been sent to your email.")
    return redirect("users:verify_otp")

@never_cache
def home(request):
    return render(request, "home.html")



