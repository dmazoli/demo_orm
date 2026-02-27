import random
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from sales.models import Category, Product, Reseller, Sale, SaleItem


class Command(BaseCommand):
    help = 'Seed database with high-volume sales data for ORM performance demo.'

    def add_arguments(self, parser):
        parser.add_argument('--user-count', type=int, default=1000)
        parser.add_argument('--category-count', type=int, default=80)
        parser.add_argument('--product-count', type=int, default=10000)
        parser.add_argument('--sale-count', type=int, default=100000)
        parser.add_argument('--min-items-per-sale', type=int, default=2)
        parser.add_argument('--max-items-per-sale', type=int, default=4)
        parser.add_argument('--chunk-size', type=int, default=5000)
        parser.add_argument('--seed', type=int, default=42)
        parser.add_argument('--reset', action='store_true')

    def handle(self, *args, **options):
        random.seed(options['seed'])

        user_count = options['user_count']
        category_count = options['category_count']
        product_count = options['product_count']
        sale_count = options['sale_count']
        min_items_per_sale = options['min_items_per_sale']
        max_items_per_sale = options['max_items_per_sale']
        chunk_size = options['chunk_size']
        reset = options['reset']

        if min_items_per_sale > max_items_per_sale:
            raise ValueError('min-items-per-sale cannot be greater than max-items-per-sale')

        self.stdout.write(self.style.NOTICE('Starting seed process...'))

        if reset:
            self._reset_data()

        users = self._create_users(user_count, chunk_size)
        resellers = self._create_resellers(users, chunk_size)
        categories = self._create_categories(category_count, chunk_size)
        products = self._create_products(product_count, chunk_size)
        product_category_map = self._link_products_to_categories(products, categories, chunk_size)

        self._create_sales_and_items(
            resellers=resellers,
            products=products,
            categories=categories,
            product_category_map=product_category_map,
            sale_count=sale_count,
            min_items_per_sale=min_items_per_sale,
            max_items_per_sale=max_items_per_sale,
            chunk_size=chunk_size,
        )

        self.stdout.write(self.style.SUCCESS('Seed process finished successfully.'))

    def _reset_data(self):
        self.stdout.write(self.style.WARNING('Reset flag enabled. Clearing existing data...'))
        User = get_user_model()

        with transaction.atomic():
            SaleItem.objects.all().delete()
            Sale.objects.all().delete()
            Product.categories.through.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            Reseller.objects.all().delete()
            User.objects.filter(username__startswith='seed_user_').delete()

    def _create_users(self, user_count, chunk_size):
        User = get_user_model()
        existing = User.objects.filter(username__startswith='seed_user_').count()
        if existing >= user_count:
            self.stdout.write(self.style.NOTICE('Users already present. Reusing existing seed users.'))
            return list(
                User.objects.filter(username__startswith='seed_user_').order_by('id')[:user_count]
            )

        self.stdout.write(f'Creating users: {user_count}')
        new_users = []
        for index in range(user_count):
            username = f'seed_user_{index:05d}'
            new_users.append(
                User(
                    username=username,
                    email=f'{username}@example.com',
                    first_name='Seed',
                    last_name=f'User{index:05d}',
                )
            )

        for start in range(0, len(new_users), chunk_size):
            User.objects.bulk_create(new_users[start:start + chunk_size], ignore_conflicts=True)

        return list(User.objects.filter(username__startswith='seed_user_').order_by('id')[:user_count])

    def _create_resellers(self, users, chunk_size):
        existing_count = Reseller.objects.count()
        if existing_count >= len(users):
            self.stdout.write(self.style.NOTICE('Resellers already present. Reusing existing records.'))
            return list(Reseller.objects.select_related('user').order_by('id')[: len(users)])

        self.stdout.write(f'Creating resellers: {len(users)}')
        regions = ['North', 'South', 'East', 'West', 'Central']
        reseller_batch = []

        for index, user in enumerate(users):
            reseller_batch.append(
                Reseller(
                    user=user,
                    company_name=f'Reseller Company {index:05d}',
                    region=random.choice(regions),
                )
            )

        for start in range(0, len(reseller_batch), chunk_size):
            Reseller.objects.bulk_create(reseller_batch[start:start + chunk_size], ignore_conflicts=True)

        return list(Reseller.objects.select_related('user').order_by('id')[: len(users)])

    def _create_categories(self, category_count, chunk_size):
        existing_count = Category.objects.count()
        if existing_count >= category_count:
            self.stdout.write(self.style.NOTICE('Categories already present. Reusing existing records.'))
            return list(Category.objects.order_by('id')[:category_count])

        self.stdout.write(f'Creating categories: {category_count}')
        category_batch = [Category(name=f'Category {index:03d}') for index in range(category_count)]

        for start in range(0, len(category_batch), chunk_size):
            Category.objects.bulk_create(category_batch[start:start + chunk_size], ignore_conflicts=True)

        return list(Category.objects.order_by('id')[:category_count])

    def _create_products(self, product_count, chunk_size):
        existing_count = Product.objects.count()
        if existing_count >= product_count:
            self.stdout.write(self.style.NOTICE('Products already present. Reusing existing records.'))
            return list(Product.objects.order_by('id')[:product_count])

        self.stdout.write(f'Creating products: {product_count}')
        product_batch = []
        for index in range(product_count):
            base_price = Decimal(random.uniform(10, 1000)).quantize(Decimal('0.01'))
            product_batch.append(
                Product(
                    sku=f'SKU-{index:06d}',
                    name=f'Product {index:06d}',
                    description=f'Description for product {index:06d}',
                    base_price=base_price,
                    stock_quantity=random.randint(5, 1000),
                )
            )

        for start in range(0, len(product_batch), chunk_size):
            Product.objects.bulk_create(product_batch[start:start + chunk_size], ignore_conflicts=True)

        return list(Product.objects.order_by('id')[:product_count])

    def _link_products_to_categories(self, products, categories, chunk_size):
        through_model = Product.categories.through
        existing_links = through_model.objects.count()
        if existing_links > 0:
            self.stdout.write(self.style.NOTICE('Product-category links already present. Reusing mapping.'))
            mapping = {}
            for product_id, category_id in through_model.objects.values_list('product_id', 'category_id'):
                mapping.setdefault(product_id, []).append(category_id)
            return mapping

        self.stdout.write('Creating product-category links...')
        category_ids = [category.id for category in categories]
        relation_batch = []
        mapping = {}

        for product in products:
            selected = random.sample(category_ids, k=random.randint(1, min(3, len(category_ids))))
            mapping[product.id] = selected
            for category_id in selected:
                relation_batch.append(
                    through_model(product_id=product.id, category_id=category_id)
                )

        for start in range(0, len(relation_batch), chunk_size):
            through_model.objects.bulk_create(relation_batch[start:start + chunk_size], ignore_conflicts=True)

        return mapping

    def _create_sales_and_items(
        self,
        *,
        resellers,
        products,
        categories,
        product_category_map,
        sale_count,
        min_items_per_sale,
        max_items_per_sale,
        chunk_size,
    ):
        existing_sales = Sale.objects.count()
        if existing_sales >= sale_count:
            self.stdout.write(self.style.NOTICE('Sales already present. Skipping sale/item generation.'))
            return

        self.stdout.write(f'Creating sales: {sale_count}')
        reseller_ids = [reseller.id for reseller in resellers]
        category_ids = [category.id for category in categories]
        product_payload = [(product.id, product.base_price) for product in products]

        now = timezone.now()
        total_created = 0
        while total_created < sale_count:
            remaining = sale_count - total_created
            current_chunk = min(chunk_size, remaining)

            sale_batch = []
            for _ in range(current_chunk):
                sale_batch.append(
                    Sale(
                        reseller_id=random.choice(reseller_ids),
                        sold_at=now - timedelta(days=random.randint(0, 365), minutes=random.randint(0, 1439)),
                    )
                )

            with transaction.atomic():
                previous_max_sale_id = (
                    Sale.objects.order_by('-id').values_list('id', flat=True).first() or 0
                )

                Sale.objects.bulk_create(sale_batch, batch_size=chunk_size)

                created_sale_ids = list(
                    Sale.objects.filter(id__gt=previous_max_sale_id)
                    .order_by('id')
                    .values_list('id', flat=True)[:current_chunk]
                )

                if len(created_sale_ids) != current_chunk:
                    raise RuntimeError(
                        f'Expected {current_chunk} new sales, got {len(created_sale_ids)}. '
                        'Abort to avoid creating orphan sale items.'
                    )

                item_batch = []
                for sale_id in created_sale_ids:
                    item_count = random.randint(min_items_per_sale, max_items_per_sale)
                    for _ in range(item_count):
                        product_id, base_price = random.choice(product_payload)
                        candidate_categories = product_category_map.get(product_id) or category_ids
                        selected_category = random.choice(candidate_categories)

                        quantity = random.randint(1, 8)
                        multiplier = Decimal(str(random.uniform(0.85, 1.20))).quantize(
                            Decimal('0.0001'), rounding=ROUND_HALF_UP
                        )
                        unit_price = (base_price * multiplier).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        line_total = (unit_price * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                        item_batch.append(
                            SaleItem(
                                sale_id=sale_id,
                                product_id=product_id,
                                category_id=selected_category,
                                quantity=quantity,
                                unit_price=unit_price,
                                line_total=line_total,
                            )
                        )

                SaleItem.objects.bulk_create(item_batch, batch_size=chunk_size)

            total_created += current_chunk
            self.stdout.write(f'  Progress: {total_created}/{sale_count} sales created')
