from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Point d'extension pour uniformiser le format des erreurs API si besoin."""
    return exception_handler(exc, context)
