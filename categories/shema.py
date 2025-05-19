from drf_yasg import openapi

shema = {
    'CategoriesAuthView': {
            'update_match': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'match': openapi.Schema(
                                type=openapi.TYPE_INTEGER
                            ),
                            'category_id': openapi.Schema(
                                type=openapi.TYPE_INTEGER
                            )
                        }
                    ),
    }
}