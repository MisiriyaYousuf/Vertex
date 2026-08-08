from django.db import models
from customadmin.models import Category


class Product(models.Model):

    name = models.CharField(max_length=255)
    description = models.TextField()
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    quantity = models.PositiveIntegerField()
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ProductImage(models.Model):

    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="images")
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} Image"
