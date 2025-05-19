from drf_yasg import openapi

shema = {
    'ShopViews': {
        'comment': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'shop_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                ),
                'comment': openapi.Schema(
                    type=openapi.TYPE_STRING
                )
            }
        ),
        'html_map_delete': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'shop_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                ),
                'id': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                )
            }
        ),
        'html_map':openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                ),
                'type': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'tagName': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'className': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'attributes': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'text': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'order': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                )
            }
        )
    },
}
