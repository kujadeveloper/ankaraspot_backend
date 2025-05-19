from django_elasticsearch_dsl import Document, fields
from utils.elastic_analyzers import turkish_analyzer
from .models import BrandModel
from django_elasticsearch_dsl.registries import registry

text_analyzer = turkish_analyzer()

@registry.register_document
class BrandsDocument(Document):
    name = fields.TextField(
        analyzer=text_analyzer,
        attr='name',
        fields={
            'raw': fields.TextField(analyzer='keyword', multi=True),
            'suggest': fields.CompletionField(),
        }
    )

    shop = fields.ObjectField(
        attr='shop',
        properties={
            'id': fields.IntegerField(attr='id'),
            'name': fields.TextField(attr='name', analyzer=text_analyzer),
            'image': fields.ObjectField(attr='images', properties={
                'id': fields.IntegerField(attr='id'),
                'thumb_file_url': fields.TextField(attr='thumb_file_url'),
            })
        }
    )

    class Index:
        name = 'brands_index'
    class Django:
        model = BrandModel
        fields = ['id','is_main', 'is_deleted', 'created_at', 'updated_at']
