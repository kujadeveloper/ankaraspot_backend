from django.core.management.base import BaseCommand
from sitesettings.models import *

class Command(BaseCommand):
    help = 'Seeds the database'

    def handle(self, *args, **kwargs):
        SitesettingsModels.objects.create(aws_access_key='TcM3SXau7kWNhHuX', aws_secret='6KdAAp8ys52jLumazm7x243qkuRc7i8u', aws_url='https://image.fiyator.com')
        self.stdout.write(self.style.SUCCESS('Database seeded!'))
