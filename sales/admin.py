from django.contrib import admin

from .models import Category, Product, Reseller, Sale, SaleItem


@admin.register(Reseller)
class ResellerAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'user', 'region', 'created_at')
    search_fields = ('company_name', 'user__username', 'region')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'sku', 'name', 'base_price', 'stock_quantity', 'created_at')
    search_fields = ('sku', 'name')
    list_filter = ('categories',)


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'reseller', 'sold_at', 'created_at')
    list_filter = ('sold_at',)
    search_fields = ('reseller__company_name', 'reseller__user__username')
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale', 'product', 'category', 'quantity', 'unit_price', 'line_total')
    list_filter = ('category',)
    search_fields = ('product__sku', 'product__name')
