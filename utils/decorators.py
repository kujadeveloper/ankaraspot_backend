from rest_framework.response import Response

from functools import wraps


def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return Response({'detail': 'Permission denied'}, status=401)
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def group_required(group_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.groups.filter(name=group_name).exists():
                return Response({'detail': 'Permission denied'}, status=401)
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
