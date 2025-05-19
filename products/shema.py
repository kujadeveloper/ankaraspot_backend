from drf_yasg import openapi

shema = {
    'ProductsView': {
        'product_event': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                )
            }
        ),
        'favorite': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                )
            }
        ),
        'comment': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                ),
                'comment': openapi.Schema(
                    type=openapi.TYPE_STRING
                )
            }
        ),
        'rate': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                ),
                'rate': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                )
            }
        )
    },
}
