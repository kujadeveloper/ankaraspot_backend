from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from users.models import User

class Command(BaseCommand):
    help = 'Seeds the database'

    def handle(self, *args, **kwargs):
        Group.objects.create(name='admin')
        Group.objects.create(name='user')
        Group.objects.create(name='company')
        self.stdout.write(self.style.SUCCESS('Database seeded!'))
        instance = User.objects.create(email='admin@ankaraspot.com',
                            username='admin',
                            first_name='admin',
                            last_name='user',
                            phone='555555555')
        instance.set_password('ankaraspot123')
        instance.is_active = True
        instance.is_superuser = True
        instance.is_staff = True
        instance.save()

