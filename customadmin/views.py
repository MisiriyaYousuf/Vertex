from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from products.models import Product,Category
from django.http import HttpResponse,HttpResponseNotAllowed
from users.models import UserProfile


@never_cache
@login_required
def dashboard(request):
    if not request.user.is_superuser:
        return redirect("users:home")

    products = Product.objects.all()  
    if not request.user.is_superuser:  
        return redirect('home')
    user_count = User.objects.count()
    product_count = Product.objects.filter(is_deleted=False).count()
    category_count = Category.objects.filter(is_trashed=False).count()

    return render(request, 'dashboard.html', {
        'user_count': user_count,
        'product_count': product_count,
        'category_count': category_count,
        'products': products})

@never_cache
@login_required
def user_management(request):

    
    if  request.user.is_superuser:
    
        profiles = UserProfile.objects.filter(user__is_superuser=False).select_related("user")
        return render( request,"user_manage.html",{"profiles": profiles,})


@never_cache
@login_required
def block_user(request, profile_id):

    if  request.user.is_superuser:

        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

    profile = UserProfile.objects.filter(id=profile_id,user__is_superuser=False).first()
    if profile is None:
        return HttpResponse('User not exist')
    user = profile.user
    profile.blocked = True
    profile.save(update_fields=["blocked"])
    user.is_active = False
    user.save(update_fields=["is_active"])
    messages.success(
        request,
        f"{user.username} has been blocked successfully."
    )
    return redirect("customadmin:user_management")


@never_cache
@login_required
def unblock_user(request, profile_id):

    
    if request.user.is_superuser:
    
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

    profile = UserProfile.objects.filter(
        id=profile_id,
        user__is_superuser=False
    ).first()

    if profile is None:
        return HttpResponse('User not exist')
    user = profile.user
    profile.blocked = False
    profile.save(update_fields=["blocked"])

    user.is_active = True
    user.save(update_fields=["is_active"])

    messages.success(
        request,
        f"{user.username} has been unblocked successfully."
    )
    return redirect("customadmin:user_management")

@never_cache
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("users:signin")