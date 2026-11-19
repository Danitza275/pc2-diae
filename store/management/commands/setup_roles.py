"""Crea los roles del proyecto y los asigna a los usuarios.

Uso:
    python manage.py setup_roles
"""
from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea los grupos Administrador y Cliente y asigna los usuarios.'

    def handle(self, *args, **options):
        admin, creado = Group.objects.get_or_create(name='Administrador')
        cliente, _ = Group.objects.get_or_create(name='Cliente')

        # El Administrador tiene todos los permisos de la app store
        permisos = Permission.objects.filter(content_type__app_label='store')
        admin.permissions.set(permisos)
        self.stdout.write(f'Grupo "Administrador" con {permisos.count()} permisos de store.')

        # El Cliente solo puede ver
        ver = permisos.filter(codename__startswith='view_')
        cliente.permissions.set(ver)
        self.stdout.write(f'Grupo "Cliente" con {ver.count()} permisos de solo lectura.')

        # Asignación de usuarios
        for usuario in User.objects.all():
            if usuario.is_staff or usuario.is_superuser:
                usuario.groups.add(admin)
                usuario.groups.remove(cliente)
            else:
                usuario.groups.add(cliente)
                usuario.groups.remove(admin)

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {User.objects.filter(groups=admin).count()} administrador(es), '
            f'{User.objects.filter(groups=cliente).count()} cliente(s).'))
