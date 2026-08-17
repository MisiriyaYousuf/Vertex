import re
from django import forms
from .models import Category
from decimal import Decimal
from products .models import Product, ProductImage,ProductVariant
from django import forms


class CategoryForm(forms.ModelForm):

    name = forms.CharField(max_length=100,required=True,widget=forms.TextInput(attrs={"class": "form-control","placeholder": "Enter category name",
                "maxlength": "100","autocomplete": "off",}))

    class Meta:
        model = Category
        fields = ["name"]

    def clean_name(self):

        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Category name cannot be empty.")

        if not re.fullmatch(r"[A-Za-z ]+", name):
            raise forms.ValidationError("Category name can contain only letters and spaces.")

        if "  " in name:
            raise forms.ValidationError("Category name cannot contain multiple consecutive spaces.")

        existing = Category.objects.filter(name__iexact=name,is_trashed=False)

        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise forms.ValidationError("This category already exists.")

        return name

class ProductForm(forms.ModelForm):
    
    class Meta:
        model = Product
        fields = [
            'category',
            'name',
            'description',
            'sale_price',
            'discount_price',
            'quantity',
            'main_image',
            'coupon_code',
            'is_active',
            'featured',
        ]

        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),

            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name',
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter product description',
            }),

            'sale_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter sale price',
                'step': '0.01',
                'min': '0.01',
            }),

            'discount_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter discount price',
                'step': '0.01',
                'min': '0.01',
            }),

            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quantity',
                'min': '0',
            }),

            'main_image': forms.Select(attrs={
                'class': 'form-control',
            }),

            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),

            'featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        
        if self.instance and self.instance.pk:
            self.fields['main_image'].queryset = ProductImage.objects.filter(
                product=self.instance
            )
        else:
            
            self.fields['main_image'].queryset = ProductImage.objects.none()

    def clean_name(self):
        name = self.cleaned_data.get('name')

        if not name:
            raise forms.ValidationError(
                "Product name is required."
            )

        name = name.strip()

        if len(name) < 2:
            raise forms.ValidationError(
                "Product name must contain at least 2 characters."
            )

       
        queryset = Product.objects.filter(
            name__iexact=name,
            is_deleted=False
        )

        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(
                "A product with this name already exists."
            )

        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')

        if not description:
            raise forms.ValidationError(
                "Product description is required."
            )

        description = description.strip()

        if len(description) < 10:
            raise forms.ValidationError(
                "Description must contain at least 10 characters."
            )

        return description

    def clean_sale_price(self):
        sale_price = self.cleaned_data.get('sale_price')

        if sale_price is None:
            raise forms.ValidationError(
                "Sale price is required."
            )

        if sale_price <= Decimal('0'):
            raise forms.ValidationError(
                "Sale price must be greater than zero."
            )

        return sale_price

    def clean_discount_price(self):
        discount_price = self.cleaned_data.get('discount_price')

        if discount_price is None:
            return discount_price

        if discount_price <= Decimal('0'):
            raise forms.ValidationError(
                "Discount price must be greater than zero."
            )

        return discount_price

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')

        if quantity is None:
            raise forms.ValidationError(
                "Quantity is required."
            )

        if quantity < 0:
            raise forms.ValidationError(
                "Quantity cannot be negative."
            )

        return quantity

    def clean(self):
        cleaned_data = super().clean()

        sale_price = cleaned_data.get('sale_price')
        discount_price = cleaned_data.get('discount_price')

        if (
            sale_price is not None
            and discount_price is not None
            and discount_price >= sale_price
        ):
            self.add_error(
                'discount_price',
                'Discount price must be less than the sale price.'
            )

       
        main_image = cleaned_data.get('main_image')

        if main_image and self.instance.pk:
            if main_image.product_id != self.instance.pk:
                self.add_error(
                    'main_image',
                    'Selected image does not belong to this product.'
                )

        return cleaned_data

class ProductImageForm(forms.ModelForm):

    class Meta:
        model = ProductImage
        fields = ['image']

        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')

        if not image:
            raise forms.ValidationError(
                "Please select an image."
            )

        # Maximum size: 5 MB
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "Image size must not exceed 5 MB."
            )

        allowed_types = [
            'image/jpeg',
            'image/png',
            'image/webp',
        ]

        if image.content_type not in allowed_types:
            raise forms.ValidationError(
                "Only JPG, PNG and WEBP images are allowed."
            )

        return image

class ProductVariantForm(forms.ModelForm):

    class Meta:
        model = ProductVariant

        fields = [
            'color',
            'size',
            'sku',
            'quantity',
            'images',
            'is_active',
        ]

        widgets = {
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Black, Silver, Rose Gold',
            }),

            'size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 40mm, 42mm, 44mm',
            }),

            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. WATCH-BLK-40',
            }),

            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Enter stock quantity',
            }),

            'images': forms.SelectMultiple(attrs={
                'class': 'form-control',
            }),

            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)

        super().__init__(*args, **kwargs)

        self.product = product

        if product:
            self.fields['images'].queryset = ProductImage.objects.filter(
                product=product
            )

        elif self.instance and self.instance.pk:
            self.fields['images'].queryset = ProductImage.objects.filter(
                product=self.instance.product
            )

        else:
            self.fields['images'].queryset = ProductImage.objects.none()

    def clean_color(self):
        color = self.cleaned_data.get('color')

        if color:
            color = color.strip()

        return color

    def clean_size(self):
        size = self.cleaned_data.get('size')

        if size:
            size = size.strip()

        return size

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')

        if not sku:
            return None

        sku = sku.strip().upper()

        if len(sku) < 3:
            raise forms.ValidationError(
                "Product code must contain at least 3 characters."
            )

        queryset = ProductVariant.objects.filter(
            sku__iexact=sku
        )

        if self.instance.pk:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise forms.ValidationError(
                "This product code already exists."
            )

        return sku

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')

        if quantity is None:
            raise forms.ValidationError(
                "Quantity is required."
            )

        if quantity < 0:
            raise forms.ValidationError(
                "Quantity cannot be negative."
            )

        return quantity

    def clean(self):
        cleaned_data = super().clean()

        color = cleaned_data.get('color')
        size = cleaned_data.get('size')
        images = cleaned_data.get('images')

        if not color and not size:
            raise forms.ValidationError(
                "Enter at least a color or case size for the watch variant."
            )

        if images:
            product = self.product
            if not product and self.instance.pk:
                product = self.instance.product
            if product:
                invalid_images = images.exclude(product=product)
                if invalid_images.exists():
                    raise forms.ValidationError("All variant images must belong to the same product.")
        return cleaned_data