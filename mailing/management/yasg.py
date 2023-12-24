from drf_yasg import openapi
from drf_yasg.views import get_schema_view

schema_view = get_schema_view(
    openapi.Info(
        title='Mailing API',
        default_version='1.0.0',
        description='API documentation of App'
    ),
    public=True
)
