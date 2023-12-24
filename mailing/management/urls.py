from django.urls import path, include, re_path
from .views import *
from rest_framework import routers
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

schema_view = get_schema_view(
    openapi.Info(
        title='SFmailng API',
        default_version='1.0.0',
        description='API documentation of App'
    ),
    public=True
)



router = routers.DefaultRouter()
router.register('client', ClientViewSet)
router.register('message', MessageViewSet)
router.register('mailing', MailingViewSet)



urlpatterns = [
    path('', index, name='main'),  # Main
    path('add-users/', add_users, name='add_users'),  # Adds clients to the directory for testing
    path('del-users/', del_users, name='del_users'),  # Deletes all users
    path('api/v1/', include(router.urls)),  # API
    path('api/v1/auth-rest/', include('rest_framework.urls')),  # Authorization by rest
    path('api/v1/statistic-messages/', StatisticMessagesAPIView.as_view(), name='mestat'),  # Message statistics
    path('api/v1/statistic-messages/<int:status>/', StatisticMessagesAPIView.as_view()),  # Message statistics by status
    path('api/v1/messages-in-mailing/<int:mailing_id>/', MessagesInMailingAPIView.as_view()),  # View messages in the newsletter
    path('api/v1/auth/', include('djoser.urls')),  # Route for user registration
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-schema'),  # OpenAPI
    path('logout/', logout_user, name='logout'),  # Logging out of the account
]
