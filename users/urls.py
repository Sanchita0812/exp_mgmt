from django.urls import path
from users.views import GoogleLoginUrlView, GoogleCallbackView, OAuthTestFrontView

urlpatterns = [
    path('google/login/', GoogleLoginUrlView.as_view(), name='google-login'),
    path('google/callback/', GoogleCallbackView.as_view(), name='google-callback'),
    path('test-oauth/', OAuthTestFrontView.as_view(), name='test-oauth'),
]
