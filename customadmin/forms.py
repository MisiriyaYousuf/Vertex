import re
from django import forms
from .models import Category
from products.models import ( Product,ProductImage,ProductVariant,ProductVariantImage )

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
            "category",
            "name",
            "description",
            "color",
            "size",
            "sale_price",
            "discount_price",
            "quantity",
            "is_active",
            "featured",
        ]

        widgets = {

            "category": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Rolex Submariner",
                    "maxlength": "200",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter watch description",
                    "rows": 4,
                }
            ),

            "color": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Black",
                    "maxlength": "100",
                }
            ),

            "size": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: 42 mm",
                    "maxlength": "100",
                }
            ),

            "sale_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter sale price",
                    "min": "1",
                    "step": "0.01",
                }
            ),

            "discount_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter discount price",
                    "min": "0.01",
                    "step": "0.01",
                }
            ),

            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter quantity",
                    "min": "0",
                    "step": "1",
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "featured": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = Category.objects.filter(
            is_trashed=False
        ).order_by("name")


    def clean_category(self):

        category = self.cleaned_data.get("category")

        if not category:
            raise forms.ValidationError(
                "Please select a category."
            )

        return category

    def clean_name(self):

        name = self.cleaned_data.get("name")

        if not name:
            raise forms.ValidationError(
                "Watch name is required."
            )

        name = name.strip()

        if not name:
            raise forms.ValidationError(
                "Watch name cannot contain only spaces."
            )

        if not re.fullmatch(
            r"[A-Za-z]+(?: [A-Za-z]+)*",
            name
        ):
            raise forms.ValidationError(
                "Watch name can contain only letters and single spaces between words."
            )

        return name

    def clean_color(self):

        color = self.cleaned_data.get("color")

        if not color:
            raise forms.ValidationError(
                "Product color is required."
            )

        color = color.strip()

        if not re.fullmatch(
            r"[A-Za-z]+(?: [A-Za-z]+)*",
            color
        ):
            raise forms.ValidationError(
                "Color can contain only letters and single spaces."
            )

        return color

    def clean_size(self):

        size = self.cleaned_data.get("size")

        if not size:
            raise forms.ValidationError(
                "Product size is required."
            )

        size = size.strip()

        if not re.fullmatch(
            r"\d+(?: mm)?",
            size,
            re.IGNORECASE
        ):
            raise forms.ValidationError(
                "Size must be like 40, 42 or 42 mm."
            )

        return size

    def clean_description(self):

        description = self.cleaned_data.get("description")

        if not description:
            raise forms.ValidationError(
                "Watch description is required."
            )

        description = description.strip()

        if not description:
            raise forms.ValidationError(
                "Description cannot contain only spaces."
            )

        if re.search(r"\s{2,}", description):
            raise forms.ValidationError(
                "Description cannot contain multiple consecutive spaces."
            )

        if not re.fullmatch(
            r"[A-Za-z0-9., -]+",
            description
        ):
            raise forms.ValidationError(
                "Description contains invalid characters."
            )

        return description

    def clean_sale_price(self):

        sale_price = self.cleaned_data.get("sale_price")

        if sale_price is None:
            raise forms.ValidationError(
                "Sale price is required."
            )

        if sale_price <= 0:
            raise forms.ValidationError(
                "Sale price must be greater than zero."
            )

        return sale_price

    def clean_discount_price(self):

        discount_price = self.cleaned_data.get("discount_price")

        if discount_price is None:
            return None

        if discount_price <= 0:
            raise forms.ValidationError(
                "Discount price must be greater than zero."
            )

        return discount_price

    def clean_quantity(self):

        quantity = self.cleaned_data.get("quantity")

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

        sale_price = cleaned_data.get("sale_price")
        discount_price = cleaned_data.get("discount_price")

        if (
            sale_price is not None
            and discount_price is not None
            and discount_price >= sale_price
        ):
            self.add_error(
                "discount_price",
                "Discount price must be less than the sale price."
            )

        return cleaned_data

class ProductVariantForm(forms.ModelForm):

    class Meta:

        model = ProductVariant

        fields = [
            "color",
            "size",
            "sku",
            "quantity",
            "is_active",
        ]

        widgets = {

            "color": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Black",
                }
            ),

            "size": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: 42 mm",
                }
            ),

            "sku": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: RLX-BLK-42",
                    "maxlength": "100",
                }
            ),

            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter quantity",
                    "min": "0",
                    "step": "1",
                }
            ),
        }


    def clean_color(self):

        color = self.cleaned_data.get("color")

        if not color:

            raise forms.ValidationError(
                "Color is required."
            )

        color = color.strip()

        if not color:

            raise forms.ValidationError(
                "Color is required."
            )

        if not re.fullmatch(
            r"[A-Za-z]+(?: [A-Za-z]+)*",
            color
        ):

            raise forms.ValidationError(
                "Color can contain only letters and single spaces."
            )

        return color


    def clean_size(self):

        size = self.cleaned_data.get("size")

        if not size:

            raise forms.ValidationError(
                "Watch size is required."
            )

        size = size.strip()

        if not re.fullmatch(
            r"\d+(?: mm)?",
            size,
            re.IGNORECASE
        ):

            raise forms.ValidationError(
                "Size must be like 40, 42 or 42 mm."
            )

        return size


    def clean_sku(self):

        sku = self.cleaned_data.get("sku")

        if not sku:

            raise forms.ValidationError(
                "SKU is required."
            )

        sku = sku.strip()

        if not re.fullmatch(
            r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*",
            sku
        ):

            raise forms.ValidationError(
                "SKU can contain only letters, numbers and hyphens."
            )

        return sku.upper()


    def clean_quantity(self):

        quantity = self.cleaned_data.get(
            "quantity"
        )

        if quantity is None:

            raise forms.ValidationError(
                "Variant quantity is required."
            )

        if quantity < 0:

            raise forms.ValidationError(
                "Variant quantity cannot be negative."
            )

        return quantity