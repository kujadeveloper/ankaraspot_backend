from django.core.management.base import BaseCommand
from specs.models import SpecsModel
from django.db.models import Count

class Command(BaseCommand):
    # Aynı mağazada aynı isimdeki kategori özelliklerini tespit eder ve tekrarları siler

    def handle(self, *args, **options):
        duplicates = SpecsModel.objects.values('name', 'shop')\
            .annotate(name_count=Count('id'))\
            .filter(name_count__gt=1)

        deleted_count = 0
        
        for duplicate in duplicates:
            specs = SpecsModel.objects.filter(
                name=duplicate['name'],
                shop=duplicate['shop']
            ).order_by('id')
            
            first_spec = specs.first()
            specs_to_delete = specs.exclude(id=first_spec.id)
            
            count = specs_to_delete.count()
            specs_to_delete.delete()
            deleted_count += count
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'"{duplicate["name"]}" isimli özellikten {count} adet tekrar silindi (Mağaza ID: {duplicate["shop"]})'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Toplam {deleted_count} adet tekrarlı özellik silindi'
            )
        )