from django.apps import AppConfig

class BalancesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'balances'

    def ready(self):
        import balances.signals  # Signal'leri kaydet
