from drf_yasg import openapi

shema = {
    'UsersPublicView': {
        'confirm_key': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'confirm_key': openapi.Schema(
                    type=openapi.TYPE_STRING
                )
            }
        ),
        'forgot_pass': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING
                )
            }
        ),
        'subscribe': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING
                )
            }
        ),
        'reset_pass': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'token': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'repassword': openapi.Schema(
                    type=openapi.TYPE_STRING
                )
            }
        ),
    },
    'UsersView': {
        'create_descriptions': 'Create a user',
        'update_descriptions': 'Update user',
        'delete_descriptions': 'Delete user',
        'list_descriptions': 'List users',
        'create_anonym_descriptions': 'Create a anonym user',
        'create_sshkey': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'ssh_key': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'name': openapi.Schema(
                    type=openapi.TYPE_STRING
                )
            }
        ),
        'create': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'username': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'phone': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'repassword': openapi.Schema(
                    type=openapi.TYPE_STRING
                )
            }
        ),
        'update': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                ),
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING
                ),
                'phone': openapi.Schema(
                    type=openapi.TYPE_STRING
                )
            }
        ),
        'delete': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(
                    type=openapi.TYPE_INTEGER
                )
            }
        ),
        'lists': [openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
                  openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
                  openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')]
    },

}
