import csv
from datetime import datetime
from decimal import Decimal

from django.http import HttpResponse, StreamingHttpResponse
from django.utils.timezone import is_aware
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import BaseRenderer

from .models import Sale, SaleItem


class CSVRenderer(BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'
    charset = 'utf-8'
    render_style = 'binary'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b''
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode(self.charset)
        return str(data).encode(self.charset)


def _serialize_csv_value(value):
    if isinstance(value, datetime):
        if is_aware(value):
            return value.isoformat()
        return value.replace(tzinfo=None).isoformat()
    if isinstance(value, Decimal):
        return f'{value:.2f}'
    return value


@api_view(['GET'])
@renderer_classes([CSVRenderer])
def unoptimized_sales_report_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="unoptimized_sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            'sale_id',
            'sale_date',
            'reseller_username',
            'product_sku',
            'product_name',
            'item_category',
            'quantity',
            'unit_price',
            'line_total',
        ]
    )

    sales = Sale.objects.all().order_by('id')
    for sale in sales:
        reseller_username = sale.reseller.user.username

        for item in sale.items.all():
            row = [
                sale.id,
                sale.sold_at,
                reseller_username,
                item.product.sku,
                item.product.name,
                item.category.name,
                item.quantity,
                item.unit_price,
                item.line_total,
            ]
            writer.writerow([_serialize_csv_value(value) for value in row])

    return response


class Echo:
    def write(self, value):
        return value


@api_view(['GET'])
@renderer_classes([CSVRenderer])
def optimized_sales_report_stream_csv(request):
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)

    queryset = (
        SaleItem.objects.select_related(
            'sale',
            'sale__reseller',
            'sale__reseller__user',
            'product',
            'category',
        )
        .prefetch_related('product__categories')
        .values_list(
            'sale_id',
            'sale__sold_at',
            'sale__reseller__user__username',
            'product__sku',
            'product__name',
            'category__name',
            'quantity',
            'unit_price',
            'line_total',
        )
        .order_by('sale_id', 'id')
    )

    header = [
        'sale_id',
        'sale_date',
        'reseller_username',
        'product_sku',
        'product_name',
        'item_category',
        'quantity',
        'unit_price',
        'line_total',
    ]

    def row_generator():
        yield writer.writerow(header)
        for row in queryset.iterator(chunk_size=5000):
            yield writer.writerow([_serialize_csv_value(value) for value in row])

    response = StreamingHttpResponse(row_generator(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="optimized_sales_report.csv"'
    return response
