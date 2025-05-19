from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import ProductModel
from django.db.models import Count, Q
from tqdm import tqdm
import time


class Command(BaseCommand):
    help = 'Tüm ürünlerin skorlarını hesaplar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Her batch\'te işlenecek ürün sayısı'
        )

    def _calculate_scores(self, instance):
        """Bir ürün için skorları hesaplar"""
        try:
            # 1. Kendi eşleşme ve mağaza sayılarını hesapla
            own_match_count = instance.match.filter(
                is_deleted=False  # Sadece silinmemiş eşleşmeleri say
            ).count()
            
            own_shop_count = instance.match.filter(
                is_deleted=False,  # Sadece silinmemiş eşleşmeleri say
                shop__isnull=False
            ).values('shop').distinct().count()
            
            # 2. Alt ürünlerin eşleşme ve mağaza sayılarını hesapla
            if not instance.is_match:  # Ana ürün ise
                sub_matches = instance.match.filter(
                    is_deleted=False  # Sadece silinmemiş eşleşmeleri say
                ).prefetch_related('match')
                
                sub_match_count = 0
                sub_shop_count = 0
                
                for match in sub_matches:
                    sub_match_count += match.match.filter(
                        is_deleted=False  # Sadece silinmemiş eşleşmeleri say
                    ).count()
                    
                    sub_shop_count += match.match.filter(
                        is_deleted=False,  # Sadece silinmemiş eşleşmeleri say
                        shop__isnull=False
                    ).values('shop').distinct().count()
            else:
                sub_match_count = 0
                sub_shop_count = 0
            
            # 3. Toplam sayıları hesapla
            instance.total_match_count = own_match_count + sub_match_count if not instance.is_match else own_match_count
            instance.total_shop_count = own_shop_count + sub_shop_count if not instance.is_match else own_shop_count
            
            # 4. Skorları hesapla
            instance.match_score = 1 if instance.total_match_count == 0 else instance.total_match_count * 2
            instance.shop_score = 0 if instance.total_shop_count == 0 else instance.total_shop_count * 2
            instance.final_score = instance.match_score + instance.shop_score
            
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ürün {instance.id} için skor hesaplama hatası: {str(e)}'))
            # Hata durumunda varsayılan değerleri ata
            instance.total_match_count = 0
            instance.total_shop_count = 0
            instance.match_score = 1
            instance.shop_score = 0
            instance.final_score = 1
            return False

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        
        # Toplam ürün sayısını al
        total_products = ProductModel.objects.count()
        self.stdout.write(f'Toplam {total_products} ürün işlenecek...')
        
        # Ürünleri batch'ler halinde işle
        processed = 0
        start_time = time.time()
        
        with tqdm(total=total_products, desc="Skorlar hesaplanıyor") as pbar:
            while processed < total_products:
                # Batch al
                products = ProductModel.objects.all()[processed:processed + batch_size]
                
                # Her ürün için skorları hesapla ve kaydet
                for product in products:
                    with transaction.atomic():
                        if self._calculate_scores(product):
                            product.save()
                    pbar.update(1)
                
                processed += batch_size
                
                # Her 1000 üründe bir istatistik göster
                if processed % 1000 == 0:
                    elapsed = time.time() - start_time
                    rate = processed / elapsed
                    remaining = (total_products - processed) / rate if rate > 0 else 0
                    self.stdout.write(
                        f'İşlenen: {processed}/{total_products} '
                        f'({rate:.1f} ürün/sn, '
                        f'kalan süre: {remaining/60:.1f} dk)'
                    )
        
        elapsed = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f'Tüm skorlar {elapsed/60:.1f} dakikada hesaplandı. '
            f'({total_products/elapsed:.1f} ürün/sn)'
        )) 