from django.db import models
from customadmin.models import Category


class ProductImage(models.Model):
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(
        upload_to='products/images/'
    )

    def __str__(self):
        return self.image.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )

    name = models.CharField(max_length=255)
    description = models.TextField()

    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField()

    main_image = models.ForeignKey(
        ProductImage,
        related_name='main_image_products',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    coupon_code = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    color = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    size = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True
    )

    quantity = models.PositiveIntegerField(default=0)

    images = models.ManyToManyField(
        ProductImage,
        related_name='variants',
        blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        values = []

        if self.color:
            values.append(self.color)

        if self.size:
            values.append(self.size)

        return f"{self.product.name} - {' / '.join(values)}"


