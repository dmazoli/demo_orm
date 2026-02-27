from django.urls import path

from .views import optimized_sales_report_stream_csv, unoptimized_sales_report_csv

urlpatterns = [
    path('reports/unoptimized', unoptimized_sales_report_csv, name='report-unoptimized-csv'),
    path('reports/optimized', optimized_sales_report_stream_csv, name='report-optimized-csv'),
]
