from drf_yasg import openapi

shop_comparison_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'shop_ids': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_INTEGER),
            description='Karşılaştırılacak mağaza ID\'leri'
        ),
    },
    required=['shop_ids']
)

shop_comparison_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'shop_id': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'total_matched_products': openapi.Schema(type=openapi.TYPE_INTEGER),
                'cheaper_products': openapi.Schema(type=openapi.TYPE_INTEGER),
                'expensive_products': openapi.Schema(type=openapi.TYPE_INTEGER),
                'equal_price_products': openapi.Schema(type=openapi.TYPE_INTEGER),
                'avg_price_difference': openapi.Schema(type=openapi.TYPE_NUMBER),
                'analyses': openapi.Schema(
                    type=openapi.TYPE_ARRAY, 
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            }
        )
    }
)

shop_comparison_get_parameters = [
    openapi.Parameter(
        'shop_ids[]',
        openapi.IN_QUERY,
        description="Karşılaştırma sonuçları getirilecek mağaza ID'leri",
        type=openapi.TYPE_ARRAY,
        items=openapi.Items(type=openapi.TYPE_INTEGER),
        required=True
    )
]

shop_comparison_get_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'total_products': openapi.Schema(type=openapi.TYPE_INTEGER),
        'cheaper_products': openapi.Schema(type=openapi.TYPE_INTEGER),
        'expensive_products': openapi.Schema(type=openapi.TYPE_INTEGER),
        'avg_price_difference': openapi.Schema(type=openapi.TYPE_NUMBER),
        'analyses': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_OBJECT)
        )
    }
) 