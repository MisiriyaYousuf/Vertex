from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.utils import timezone
from .models import Category
from django.core.paginator import Paginator
from users.models import UserProfile
from .forms import CategoryForm
from django.db import transaction
from products.models import (Product,ProductImage,ProductVariant,ProductVariantImage,)
from .forms import ProductForm,ProductVariantForm
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@never_cache
@login_required
def dashboard(request):
    if not request.user.is_superuser:
        return redirect("users:home")

    #products = Product.objects.all()  
    user_count = User.objects.filter(is_superuser=False).count()
    category_count = Category.objects.filter(is_trashed=False).count()

    return render(request, 'dashboard.html', {
        'user_count': user_count,
        'category_count': category_count,
        })

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
def add_product(request):

    if request.method == "POST":

        form = ProductForm(request.POST)

        custom_errors = []

        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]


        # =====================================================
        # PRODUCT IMAGES
        # =====================================================

        product_images = request.FILES.getlist(
            "product_images"
        )

        if len(product_images) < 3:

            custom_errors.append(
                "Please upload at least 3 product images."
            )


        for image in product_images:

            if image.size > 5 * 1024 * 1024:

                custom_errors.append(
                    f"{image.name} is larger than 5 MB."
                )

            if image.content_type not in allowed_types:

                custom_errors.append(
                    f"{image.name}: only JPG, PNG and WEBP images are allowed."
                )


        # =====================================================
        # VARIANT INDEXES
        # =====================================================

        variant_indexes = request.POST.getlist(
            "variant_index"
        )

        variant_indexes = [
            index.strip()
            for index in variant_indexes
            if index.strip()
        ]


        if len(variant_indexes) < 2:

            custom_errors.append(
                "Please add at least 2 watch variants."
            )


        validated_variants = []


        # =====================================================
        # VALIDATE VARIANTS
        # =====================================================

        for position, index in enumerate(
            variant_indexes,
            start=1
        ):

            color = request.POST.get(
                f"variant_color_{index}",
                ""
            ).strip()

            size = request.POST.get(
                f"variant_size_{index}",
                ""
            ).strip()

            sku = request.POST.get(
                f"variant_sku_{index}",
                ""
            ).strip()

            quantity = request.POST.get(
                f"variant_quantity_{index}",
                ""
            ).strip()


            # IMPORTANT
            variant_images = request.FILES.getlist(
                f"variant_images_{index}"
            )


            variant_data = {
                "color": color,
                "size": size,
                "sku": sku,
                "quantity": quantity,
                "is_active": True,
            }


            variant_form = ProductVariantForm(
                variant_data
            )


            if not variant_form.is_valid():

                for field, errors in (
                    variant_form.errors.items()
                ):

                    for error in errors:

                        custom_errors.append(
                            f"Variant {position}: {error}"
                        )


            # At least one variant image

            if len(variant_images) < 1:

                custom_errors.append(
                    f"Variant {position} must have at least one image."
                )


            # Validate variant images

            for image in variant_images:

                if image.size > 5 * 1024 * 1024:

                    custom_errors.append(
                        f"Variant {position}: "
                        f"{image.name} is larger than 5 MB."
                    )


                if image.content_type not in allowed_types:

                    custom_errors.append(
                        f"Variant {position}: "
                        f"{image.name} must be JPG, PNG or WEBP."
                    )


            validated_variants.append(
                {
                    "index": index,
                    "form": variant_form,
                    "images": variant_images,
                }
            )


        # =====================================================
        # FORM ERRORS
        # =====================================================

        for error in custom_errors:

            form.add_error(
                None,
                error
            )


        if not form.is_valid() or custom_errors:

            return render(
                request,
                "add_product.html",
                {
                    "form": form
                }
            )


        # =====================================================
        # SAVE EVERYTHING
        # =====================================================

        try:

            with transaction.atomic():

                # ------------------------------
                # PRODUCT
                # ------------------------------

                product = form.save()


                # ------------------------------
                # PRODUCT IMAGES
                # ------------------------------

                saved_product_images = []


                for position, image in enumerate(
                    product_images
                ):

                    product_image = (
                        ProductImage.objects.create(
                            product=product,
                            image=image,
                            position=position
                        )
                    )


                    saved_product_images.append(
                        product_image
                    )


                # First image = main image

                if saved_product_images:

                    product.main_image = (
                        saved_product_images[0]
                    )

                    product.save(
                        update_fields=[
                            "main_image"
                        ]
                    )


                # ------------------------------
                # VARIANTS
                # ------------------------------

                for variant_data in validated_variants:

                    variant_form = (
                        variant_data["form"]
                    )


                    variant = (
                        ProductVariant.objects.create(
                            product=product,

                            color=variant_form.cleaned_data[
                                "color"
                            ],

                            size=variant_form.cleaned_data[
                                "size"
                            ],

                            sku=variant_form.cleaned_data[
                                "sku"
                            ],

                            quantity=variant_form.cleaned_data[
                                "quantity"
                            ],

                            is_active=True,
                        )
                    )


                    # ------------------------------
                    # VARIANT IMAGES
                    # ------------------------------

                    for image_position, image in enumerate(
                        variant_data["images"]
                    ):

                        ProductVariantImage.objects.create(
                            variant=variant,
                            image=image,
                            position=image_position
                        )


            messages.success(
                request,
                "Watch product added successfully."
            )


            return redirect(
                "customadmin:list_product"
            )


        except Exception as error:

            form.add_error(
                None,
                f"Unable to add product: {error}"
            )


            return render(
                request,
                "add_product.html",
                {
                    "form": form
                }
            )


    # =====================================================
    # GET
    # =====================================================

    form = ProductForm()


    return render(
        request,
        "add_product.html",
        {
            "form": form
        }
    )

@never_cache
@login_required
def list_product(request):

    product_list = (
        Product.objects
        .select_related(
            "category",
            "main_image"
        )
        .order_by(
            "-created_at"
        )
    )

    paginator = Paginator(
        product_list,
        6
    )

    page_number = request.GET.get(
        "page"
    )

    products = paginator.get_page(
        page_number
    )

    return render(
        request,
        "list_product.html",
        {
            "products": products
        }
    )


@never_cache
@login_required
def view_product(request):

    product_id = request.GET.get("id")


    # No ID supplied

    if not product_id:

        return render(
            request,
            "view_product.html",
            {
                "product": None,
                "error_message": "Product ID is missing."
            }
        )


    # Get product

    product = (
        Product.objects
        .filter(id=product_id)
        .select_related("category")
        .first()
    )


    # Product doesn't exist

    if product is None:

        return render(
            request,
            "view_product.html",
            {
                "product": None,
                "error_message": "Product not found."
            }
        )


    # =====================================================
    # PRODUCT IMAGES
    # =====================================================

    product_images = (
        ProductImage.objects
        .filter(product=product)
        .order_by("position", "id")
    )


    # =====================================================
    # VARIANTS + VARIANT IMAGES
    # =====================================================

    variants = (
        ProductVariant.objects
        .filter(product=product)
        .prefetch_related("images")
        .order_by("id")
    )


    context = {

        "product": product,

        "product_images": product_images,

        "variants": variants,

    }


    return render(
        request,
        "view_product.html",
        context
    )

@never_cache
@login_required
def edit_product(request):

    product_id = request.GET.get("id")

    if not product_id:
        messages.error(
            request,
            "Product ID is required."
        )

        return redirect(
            "customadmin:list_product"
        )

    product = (
        Product.objects
        .filter(id=product_id)
        .select_related(
            "category",
            "main_image"
        )
        .prefetch_related(
            "images",
            "variants__images"
        )
        .first()
    )

    if product is None:

        messages.error(
            request,
            "Product not found."
        )

        return redirect(
            "customadmin:list_product"
        )


    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            instance=product
        )

        form_is_valid = form.is_valid()

        custom_errors = []


        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]


        # ====================================================
        # NEW PRODUCT IMAGES
        # ====================================================

        new_product_images = request.FILES.getlist(
            "product_images"
        )


        for image in new_product_images:

            if image.size > 5 * 1024 * 1024:

                custom_errors.append(
                    f"{image.name} is larger than 5 MB."
                )


            if image.content_type not in allowed_types:

                custom_errors.append(
                    f"{image.name}: only JPG, PNG and WEBP images are allowed."
                )


        # ====================================================
        # VARIANTS
        # ====================================================

        variant_indexes = request.POST.getlist(
            "variant_index"
        )


        variant_indexes = [
            index
            for index in variant_indexes
            if index.strip()
        ]


        if len(variant_indexes) < 2:

            custom_errors.append(
                "Please keep at least 2 watch variants."
            )


        validated_variants = []


        for position, index in enumerate(
            variant_indexes,
            start=1
        ):

            color = request.POST.get(
                f"variant_color_{index}",
                ""
            ).strip()


            size = request.POST.get(
                f"variant_size_{index}",
                ""
            ).strip()


            sku = request.POST.get(
                f"variant_sku_{index}",
                ""
            ).strip()


            quantity = request.POST.get(
                f"variant_quantity_{index}",
                ""
            ).strip()


            variant_id = request.POST.get(
                f"variant_id_{index}",
                ""
            )


            # ------------------------------------------------
            # IMPORTANT:
            # Existing variant image field names
            # ------------------------------------------------

            variant_images = request.FILES.getlist(
                f"variant_images_{index}"
            )


            # ------------------------------------------------
            # BACKWARD COMPATIBILITY
            # Existing template uses:
            # variant_images_existing_ID
            # ------------------------------------------------

            if not variant_images and index.startswith("existing_"):

                existing_variant_id = index.replace(
                    "existing_",
                    "",
                    1
                )

                variant_images = request.FILES.getlist(
                    f"variant_images_existing_{existing_variant_id}"
                )


            variant_data = {

                "color": color,

                "size": size,

                "sku": sku,

                "quantity": quantity,

                "is_active": True,

            }


            variant_form = ProductVariantForm(
                variant_data
            )


            if not variant_form.is_valid():

                for field, errors in (
                    variant_form.errors.items()
                ):

                    for error in errors:

                        custom_errors.append(
                            f"Variant {position}: {error}"
                        )


            # ------------------------------------------------
            # Validate images
            # ------------------------------------------------

            for image in variant_images:

                if image.size > 5 * 1024 * 1024:

                    custom_errors.append(
                        f"Variant {position}: "
                        f"{image.name} is larger than 5 MB."
                    )


                if image.content_type not in allowed_types:

                    custom_errors.append(
                        f"Variant {position}: "
                        f"{image.name} must be JPG, PNG or WEBP."
                    )


            validated_variants.append({

                "index": index,

                "variant_id": variant_id,

                "form": variant_form,

                "images": variant_images,

            })


        # ====================================================
        # ADD CUSTOM ERRORS
        # ====================================================

        for error in custom_errors:

            form.add_error(
                None,
                error
            )


        # ====================================================
        # INVALID FORM
        # ====================================================

        if form.errors or not form_is_valid:

            return render(
                request,
                "edit_product.html",
                {
                    "form": form,
                    "product": product,
                    "variants": product.variants.all(),
                    "product_images": product.images.all(),
                }
            )


        # ====================================================
        # SAVE EVERYTHING
        # ====================================================

        try:

            with transaction.atomic():

                # ==========================================
                # UPDATE PRODUCT
                # ==========================================

                product = form.save()


                # ==========================================
                # ADD NEW PRODUCT IMAGES
                # ==========================================

                current_image_count = (
                    product.images.count()
                )


                for position, image in enumerate(
                    new_product_images,
                    start=current_image_count
                ):

                    ProductImage.objects.create(

                        product=product,

                        image=image,

                        position=position,

                    )


                # ==========================================
                # VARIANTS
                # ==========================================

                submitted_variant_ids = []


                for variant_data in validated_variants:

                    variant_form = (
                        variant_data["form"]
                    )


                    variant_id = (
                        variant_data["variant_id"]
                    )


                    # --------------------------------------
                    # EXISTING VARIANT
                    # --------------------------------------

                    if variant_id:

                        variant = (
                            ProductVariant.objects
                            .filter(
                                id=variant_id,
                                product=product
                            )
                            .first()
                        )


                        if variant:

                            submitted_variant_ids.append(
                                variant.id
                            )


                            variant.color = (
                                variant_form.cleaned_data[
                                    "color"
                                ]
                            )


                            variant.size = (
                                variant_form.cleaned_data[
                                    "size"
                                ]
                            )


                            variant.sku = (
                                variant_form.cleaned_data[
                                    "sku"
                                ]
                            )


                            variant.quantity = (
                                variant_form.cleaned_data[
                                    "quantity"
                                ]
                            )


                            variant.save()


                        else:

                            variant = (
                                ProductVariant.objects.create(

                                    product=product,

                                    color=(
                                        variant_form.cleaned_data[
                                            "color"
                                        ]
                                    ),

                                    size=(
                                        variant_form.cleaned_data[
                                            "size"
                                        ]
                                    ),

                                    sku=(
                                        variant_form.cleaned_data[
                                            "sku"
                                        ]
                                    ),

                                    quantity=(
                                        variant_form.cleaned_data[
                                            "quantity"
                                        ]
                                    ),

                                    is_active=True,

                                )
                            )


                            submitted_variant_ids.append(
                                variant.id
                            )


                    # --------------------------------------
                    # NEW VARIANT
                    # --------------------------------------

                    else:

                        variant = (
                            ProductVariant.objects.create(

                                product=product,

                                color=(
                                    variant_form.cleaned_data[
                                        "color"
                                    ]
                                ),

                                size=(
                                    variant_form.cleaned_data[
                                        "size"
                                    ]
                                ),

                                sku=(
                                    variant_form.cleaned_data[
                                        "sku"
                                    ]
                                ),

                                quantity=(
                                    variant_form.cleaned_data[
                                        "quantity"
                                    ]
                                ),

                                is_active=True,

                            )
                        )


                        submitted_variant_ids.append(
                            variant.id
                        )


                    # ======================================
                    # ADD VARIANT IMAGES
                    # ======================================

                    existing_image_count = (
                        variant.images.count()
                    )


                    for image_position, image in enumerate(
                        variant_data["images"],
                        start=existing_image_count
                    ):

                        ProductVariantImage.objects.create(

                            variant=variant,

                            image=image,

                            position=image_position,

                        )


                # ==========================================
                # DELETE REMOVED VARIANTS
                # ==========================================

                product.variants.exclude(
                    id__in=submitted_variant_ids
                ).delete()


                # ==========================================
                # ENSURE MAIN IMAGE EXISTS
                # ==========================================

                if (
                    product.main_image is None
                    and product.images.exists()
                ):

                    product.main_image = (
                        product.images.order_by(
                            "position",
                            "id"
                        ).first()
                    )


                    product.save(
                        update_fields=[
                            "main_image"
                        ]
                    )


            messages.success(
                request,
                "Product updated successfully."
            )


            return redirect(
                "customadmin:list_product"
            )


        except Exception as error:

            form.add_error(
                None,
                f"Unable to update product: {error}"
            )


    # ========================================================
    # GET
    # ========================================================

    else:

        form = ProductForm(
            instance=product
        )


    return render(
        request,
        "edit_product.html",
        {
            "form": form,

            "product": product,

            "variants": product.variants.all(),

            "product_images": product.images.all(),
        }
    )


# ============================================================
# DELETE PRODUCT IMAGE
# ============================================================

@never_cache
@login_required
def delete_product_image(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request."
            },
            status=400
        )


    image_id = request.POST.get(
        "image_id"
    )


    if not image_id:

        return JsonResponse(
            {
                "success": False,
                "message": "Image ID is required."
            },
            status=400
        )


    image = (
        ProductImage.objects
        .filter(id=image_id)
        .select_related(
            "product"
        )
        .first()
    )


    if image is None:

        return JsonResponse(
            {
                "success": False,
                "message": "Product image not found."
            },
            status=404
        )


    try:

        product = image.product


        # -----------------------------------------------
        # Check whether this is the main image
        # -----------------------------------------------

        is_main_image = (
            product.main_image_id == image.id
        )


        image.delete()


        # -----------------------------------------------
        # If deleted image was main image,
        # assign another image as main image.
        # -----------------------------------------------

        if is_main_image:

            next_image = (
                product.images
                .order_by(
                    "position",
                    "id"
                )
                .first()
            )


            product.main_image = next_image


            product.save(
                update_fields=[
                    "main_image"
                ]
            )


        return JsonResponse(
            {
                "success": True,

                "message": "Product image deleted successfully.",

                "product_id": product.id,
            }
        )


    except Exception as error:

        return JsonResponse(
            {
                "success": False,
                "message": (
                    f"Unable to delete image: {error}"
                )
            },
            status=500
        )


# ============================================================
# DELETE VARIANT IMAGE
# ============================================================

@never_cache
@login_required
def delete_variant_image(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request."
            },
            status=400
        )


    image_id = request.POST.get(
        "image_id"
    )


    if not image_id:

        return JsonResponse(
            {
                "success": False,
                "message": "Image ID is required."
            },
            status=400
        )


    image = (
        ProductVariantImage.objects
        .filter(id=image_id)
        .select_related(
            "variant",
            "variant__product"
        )
        .first()
    )


    if image is None:

        return JsonResponse(
            {
                "success": False,
                "message": "Variant image not found."
            },
            status=404
        )


    try:

        variant = image.variant

        product = variant.product


        image.delete()


        return JsonResponse(
            {
                "success": True,

                "message": "Variant image deleted successfully.",

                "variant_id": variant.id,

                "product_id": product.id,
            }
        )


    except Exception as error:

        return JsonResponse(
            {
                "success": False,
                "message": (
                    f"Unable to delete variant image: {error}"
                )
            },
            status=500
        )


# ============================================================
# DELETE PRODUCT
# ============================================================

@never_cache
@login_required
def delete_product(request):

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request."
        )

        return redirect(
            "customadmin:list_product"
        )


    product_id = request.GET.get(
        "id"
    )


    if not product_id:

        messages.error(
            request,
            "Product ID is required."
        )

        return redirect(
            "customadmin:list_product"
        )


    product = (
        Product.objects
        .filter(id=product_id)
        .first()
    )


    if product is None:

        messages.error(
            request,
            "Product not found."
        )

        return redirect(
            "customadmin:list_product"
        )


    try:

        product_name = product.name

        product.delete()


        messages.success(
            request,
            f"{product_name} deleted successfully."
        )


    except Exception as error:

        messages.error(
            request,
            f"Unable to delete product: {error}"
        )


    return redirect(
        "customadmin:list_product"
    )

@never_cache
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("users:signin")