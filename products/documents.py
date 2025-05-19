# products/documents.py
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl import Document, fields

from utils.elastic_analyzers import turkish_analyzer
from .models import ProductModel

text_analyzer = turkish_analyzer()

# Define Elasticsearch document for ProductModel
@registry.register_document
class ProductDocument(Document):
    name = fields.TextField(
        analyzer=text_analyzer,
        attr='name',
        fields={
            'raw': fields.TextField(analyzer=text_analyzer),
            'suggest': fields.CompletionField(),
        }
    )

    image = fields.ObjectField(
        attr='image',
        properties={
            'id': fields.IntegerField(attr='id'),
            'thumb_file_url': fields.TextField(attr='thumb_file_url', analyzer=text_analyzer),
        }
    )

    shop = fields.ObjectField(
        attr='shop',
        properties={
            'id': fields.IntegerField(attr='id'),
            'name': fields.TextField(attr='name', analyzer=text_analyzer),
            'shop_title': fields.TextField(attr='shop_title', analyzer=text_analyzer),
            'cargo_barem': fields.FloatField(attr='cargo_barem'),
            'is_active': fields.BooleanField(attr='is_active'),
            'images': fields.ObjectField(attr='images', properties={
                'id': fields.IntegerField(attr='id'),
                'thumb_file_url': fields.TextField(attr='thumb_file_url'),
            })
        }
    )

    match = fields.ObjectField(
        attr='match',
        properties={
            'id': fields.IntegerField(attr='id'),
            'name': fields.TextField(attr='name', analyzer=text_analyzer),
            'price': fields.FloatField(attr='price'),
            'link': fields.TextField(attr='link'),
            'image': fields.ObjectField(
                    attr='image',
                    properties={
                        'id': fields.IntegerField(attr='id'),
                        'thumb_file_url': fields.TextField(attr='thumb_file_url', analyzer=text_analyzer),
                    }
            ),
            'is_deleted': fields.BooleanField(attr='is_deleted'),
            'shop': fields.ObjectField(attr='shop', properties={
                'id': fields.IntegerField(attr='id'),
                'name': fields.TextField(attr='name'),
                'images': fields.ObjectField(attr='images', properties={
                    'id': fields.IntegerField(attr='id'),
                    'thumb_file_url': fields.TextField(attr='thumb_file_url'),
                })
            }),
            'sub_merchant_shop': fields.ObjectField(attr='sub_merchant_shop',
                                                    properties={
                                                        'id': fields.IntegerField(attr='id'),
                                                        'name': fields.TextField(attr='name', analyzer=text_analyzer),
                                                    })
        }
    )

    sub_merchant_shop = fields.ObjectField(
        attr='sub_merchant_shop',
        properties={
            'id': fields.IntegerField(attr='id'),
            'name': fields.TextField(attr='name', analyzer=text_analyzer),
        }
    )

    brand = fields.ObjectField(
        attr='brand',
        properties={
            'id': fields.IntegerField(attr='id'),
            'name': fields.TextField(attr='name', analyzer=text_analyzer),
        }
    )

    category = fields.ObjectField(
        attr='category',
        properties={
            'id': fields.IntegerField(attr='id'),
            'name': fields.TextField(attr='name', analyzer=text_analyzer),
            'slug': fields.TextField(attr='slug'),
            'is_adult': fields.BooleanField(attr='is_adult'),
            'bread_crumb': fields.ObjectField(attr='bread_crumb', multi=True),
        }
    )

    price = fields.FloatField(attr='price')

    spec_values = fields.ObjectField(
        attr='spec_values',
        multi=True,
        properties={
            'id': fields.IntegerField(attr='id'),
            'value': fields.TextField(attr='value', analyzer=text_analyzer),
            'is_deleted': fields.BooleanField(attr='is_deleted'),
        }
    )

    title = fields.TextField(attr='name')
    shop_id = fields.IntegerField(attr='shop.id')

    # New fields for match counts and scores
    total_match_count = fields.IntegerField(attr='total_match_count')
    total_shop_count = fields.IntegerField(attr='total_shop_count')
    match_score = fields.IntegerField(attr='match_score')
    shop_score = fields.IntegerField(attr='shop_score')
    final_score = fields.IntegerField(attr='final_score')

    class Index:
        name = 'products_index'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'refresh_interval': '30s',
        }

    class Django:
        model = ProductModel
        queryset = ProductModel.objects.select_related('shop').filter(
            is_deleted=False, shop__is_active=True, shop__is_deleted=False
        )
        queryset_pagination = 1500
        fields = [
            'id',
            'stock',
            'slug',
            'status',
            'barcode',
            'model_code',
            'link',
            'is_match',
            'is_deleted',
            'created_at',
            'updated_at',
        ]
