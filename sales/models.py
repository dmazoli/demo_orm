from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Reseller(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reseller_profile',
    )
    company_name = models.CharField(max_length=120)
    region = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['company_name'])]

    def __str__(self) -> str:
        return f'{self.company_name} ({self.user.username})'


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    categories = models.ManyToManyField(Category, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
        ]

    def __str__(self) -> str:
        return f'{self.sku} - {self.name}'


class Sale(models.Model):
    reseller = models.ForeignKey(Reseller, on_delete=models.PROTECT, related_name='sales')
    sold_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['reseller', 'sold_at'])]

    def __str__(self) -> str:
        return f'Sale #{self.pk}'


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['sale']),
            models.Index(fields=['product']),
            models.Index(fields=['category']),
            models.Index(fields=['sale', 'product']),
        ]

    def save(self, *args, **kwargs):
        if self.line_total in (None, Decimal('0')):
            self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'SaleItem #{self.pk} (sale={self.sale_id}, product={self.product_id})'
