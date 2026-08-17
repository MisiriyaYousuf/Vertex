from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from .forms import ProductForm
from django.http import HttpResponseNotAllowed, JsonResponse
from django.utils import timezone
from django.db import transaction
from products.models import Product, ProductImage, ProductVariant
from .models import Category
from users.models import UserProfile
from .forms import CategoryForm
import json


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

@login_required
@never_cache
def list_product(request):
    query = request.GET.get('q', '').strip()

    products = Product.objects.filter(
        is_deleted=False
    )

    if query:
        products = products.filter(name__icontains=query)

    return render(
        request,
        'list_product.html',
        {'products': products}
    )


@login_required
@never_cache
def delete_product(request, product_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    product = get_object_or_404(
        Product,
        id=product_id,
        is_deleted=False
    )

    product.is_deleted = True
    product.save(update_fields=['is_deleted'])

    messages.success(
        request,
        f'Product "{product.name}" was successfully deleted.'
    )

    return redirect('customadmin:list_product')

@login_required
@never_cache
def add_product(request):

    if request.method == 'POST':

        form = ProductForm(request.POST)

        if form.is_valid():

            main_image_file = request.FILES.get('main_image')

            variant_images_files = request.FILES.getlist(
                'variant_images_upload'
            )

            try:
                with transaction.atomic():

                    product = form.save(commit=False)
                    product.is_deleted = False

                    product.save()

                    if main_image_file:

                        main_image = ProductImage.objects.create(
                            product=product,
                            image=main_image_file
                        )

                        product.main_image = main_image

                        product.save(
                            update_fields=['main_image']
                        )

                    if variant_images_files:
                        product_variant = ProductVariant.objects.create(
                            product=product,
                            quantity=product.quantity
                        )

                        for image_file in variant_images_files:

                            variant_image = ProductImage.objects.create(
                                product=product,
                                image=image_file
                            )

                            product_variant.images.add(
                                variant_image
                            )

                    messages.success(
                        request,
                        f'Product "{product.name}" was added successfully!'
                    )

                    return redirect(
                        'customadmin:list_product'
                    )

            except Exception as e:

                messages.error(
                    request,
                    f'Unable to add product: {str(e)}'
                )

        else:
            messages.error(
                request,
                'Please correct the errors below.'

            )

    else:
        form = ProductForm()

    categories = Category.objects.filter(
        is_trashed=False
    ).order_by('name')

    return render(
        request,
        'edit_product.html',
        {
            'form': form,
            'categories': categories,
        }
    )

@login_required
@never_cache
def view_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_deleted=False
    )

    product_variants = ProductVariant.objects.filter(
        product=product
    )

    return render(
        request,
        'view_product.html',
        {
            'product': product,
            'variants': product_variants,
        }
    )


@login_required
@never_cache
@csrf_exempt
def edit_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_deleted=False
    )

    categories = Category.objects.filter(
        is_trashed=False
    ).order_by('name')

    if request.method == 'POST':

        # AJAX image deletion
        if request.headers.get(
            'X-Requested-With'
        ) == 'XMLHttpRequest':

            try:
                data = json.loads(request.body)

                image_type = data.get('type')
                image_id = data.get('id')

                if image_type == 'main':

                    if product.main_image:
                        product.main_image.delete()
                        product.main_image = None
                        product.save(
                            update_fields=['main_image']
                        )

                elif image_type == 'variant':

                    variant_image = get_object_or_404(
                        ProductImage,
                        id=image_id
                    )

                    variant_image.delete()

                return JsonResponse({
                    'success': True
                })

            except Exception as e:

                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })

        # Normal form submission
        category = get_object_or_404(
            Category,
            id=request.POST.get('category'),
            is_trashed=False
        )

        product.category = category
        product.name = request.POST.get('name')
        product.sale_price = request.POST.get('sale_price')
        product.discount_price = (
            request.POST.get('discount_price') or None
        )
        product.quantity = request.POST.get('quantity')
        product.description = request.POST.get('description')
        product.coupon_code = request.POST.get('coupon')

        # Replace main image
        main_image_file = request.FILES.get('main_image')

        if main_image_file:

            if product.main_image:
                product.main_image.delete()

            main_image = ProductImage.objects.create(
                image=main_image_file,
                is_variant=False
            )

            product.main_image = main_image

        product.save()

        # Add new variant images
        variant_images_files = request.FILES.getlist(
            'variant_images_upload'
        )

        if variant_images_files:

            product_variant, created = (
                ProductVariant.objects.get_or_create(
                    product=product
                )
            )

            for image_file in variant_images_files:

                variant_image = ProductImage.objects.create(
                    image=image_file,
                    is_variant=True
                )

                product_variant.variant_images.add(
                    variant_image
                )

        messages.success(
            request,
            f'Product "{product.name}" was updated successfully!'
        )

        return redirect('customadmin:list_product')

    return render(
        request,'edit_product.html',{
            'categories': categories,
            'product': product
        }
    )

@never_cache
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("users:signin")