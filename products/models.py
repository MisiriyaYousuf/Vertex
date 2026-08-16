from django.db import models
from customadmin.models import Category

class Product(models.Model):

    GENDER_CHOICES = [
        ('men', 'Men'),
        ('women', 'Women'),
        ('unisex', 'Unisex'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name='products')
    gender = models.CharField(max_length=10,choices=GENDER_CHOICES,default='unisex')
    sale_price = models.DecimalField(max_digits=10,decimal_places=2)
    discount_price = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    quantity = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} Image"


class ProductVariant(models.Model):
    STRAP_CHOICES = [
        ('leather', 'Leather'),
        ('steel', 'Stainless Steel'),
        ('silicone', 'Silicone'),
        ('fabric', 'Fabric')
    ]

    SIZE_CHOICES = [
        ('38', '38 mm'),
        ('40', '40 mm'),
        ('42', '42 mm'),
        ('44', '44 mm'),
        ('46', '46 mm'),
    ]

    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='variants')
    color = models.CharField(max_length=50)
    strap_type = models.CharField(max_length=20,choices=STRAP_CHOICES)
    size = models.CharField(max_length=10,choices=SIZE_CHOICES,blank=True,null=True)
    variant_price = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return (f"{self.product.name} - " f"{self.color} - " f"{self.strap_type}")

