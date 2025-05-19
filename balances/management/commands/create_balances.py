from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from balances.models import Balance

class Command(BaseCommand):
    help = 'Mevcut kullanıcılar için bakiye oluşturur'

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.all()
        created_count = 0

        for user in users:
            _, created = Balance.objects.get_or_create(
                user=user,
                defaults={'amount': 0}
            )
            if created:
                created_count += 1
                self.stdout.write(f'Bakiye oluşturuldu: {user.username}')

        self.stdout.write(
            self.style.SUCCESS(f'Toplam {created_count} kullanıcı için yeni bakiye oluşturuldu')
        ) 