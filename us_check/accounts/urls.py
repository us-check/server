from django.urls import path
from api import oauth_views  # api 앱의 oauth_views 가져오기

urlpatterns = [
    path('google/', oauth_views.GoogleAuthRedirectView.as_view(), name='google_auth'),
    path('google/callback/', oauth_views.GoogleCallbackView.as_view(), name='google_callback'),
    path('google/url/', oauth_views.GoogleAuthURLView.as_view(), name='google_auth_url'),
    path('auth/status/', oauth_views.AuthStatusView.as_view(), name='auth_status'),
    path('profile/', oauth_views.UserProfileView.as_view(), name='user_profile'),
    path('logout/', oauth_views.LogoutView.as_view(), name='logout'),
]