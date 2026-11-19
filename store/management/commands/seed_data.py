"""Carga los datos de prueba de la tienda (alias de `seed`).

Uso:
    python manage.py seed_data            # solo si la tienda está vacía
    python manage.py seed_data --reset    # borra y vuelve a crear todo
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Carga datos de prueba: usuarios, productos, pedidos e ítems.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Borra los datos de store antes de crearlos.')

    def handle(self, *args, **options):
        call_command('seed', reset=options['reset'])
