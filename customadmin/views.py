from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from products.models import Product
from .models import Category
from django.http import HttpResponse,HttpResponseNotAllowed
from django.utils import timezone
from users.models import UserProfile
from . forms import CategoryForm


@never_cache
@login_required
def dashboard(request):
    if not request.user.is_superuser:
        return redirect("users:home")

    products = Product.objects.all()  
    user_count = User.objects.filter(is_superuser=False).count()
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
def block_user(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    profile_id = request.POST.get("profile_id")
    profile = UserProfile.objects.filter(id=profile_id,user__is_superuser=False).first()
    user = profile.user
    profile.blocked = True
    profile.save(update_fields=["blocked"])
    user.is_active = False
    user.save(update_fields=["is_active"])
    messages.success(request,f"{user.username} has been blocked successfully.")
    return redirect("customadmin:user_management")

@never_cache
@login_required
def unblock_user(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    profile_id = request.POST.get("profile_id")
    profile = UserProfile.objects.filter(id=profile_id,user__is_superuser=False).first()
    user = profile.user
    profile.blocked = False
    profile.save(update_fields=["blocked"])
    user.is_active = True
    user.save(update_fields=["is_active"])
    messages.success(request,f"{user.username} has been unblocked successfully.")
    return redirect("customadmin:user_management")

@never_cache
@login_required
def category_management(request):
    categories = Category.objects.filter(is_trashed=False).order_by("name")
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Category added successfully.")
            return redirect("customadmin:category_management")
    else:
        form = CategoryForm()
    return render(request,"category_manage.html",{ "categories": categories, "form": form, })

def edit_category(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    category_id = request.POST.get("category_id")
    category = Category.objects.filter(id=category_id,is_trashed=False).first()
    form = CategoryForm(request.POST,instance=category)
    if form.is_valid():
        form.save()
        messages.success(request,"Category updated successfully.")
        return redirect("customadmin:category_management")
    return render(request,"category_edit.html",{"form": form,"category": category,})

@never_cache
@login_required
def delete_category(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    category_id = request.POST.get("category_id")
    category = Category.objects.filter(id=category_id,is_trashed=False).first()
    category.is_trashed = True
    category.trashed_at = timezone.now()
    category.save(update_fields=["is_trashed","trashed_at"])
    messages.success(request,f'"{category.name}" deleted successfully.')
    return redirect("customadmin:category_management")

@never_cache
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("users:signin")