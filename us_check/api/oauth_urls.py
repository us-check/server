from django.urls import path
from . import oauth_views

urlpatterns = [
    path('google/', oauth_views.GoogleAuthRedirectView.as_view(), name='google_auth_redirect'),
    path('google/url/', oauth_views.GoogleAuthURLView.as_view(), name='google_auth_url'),
    
    # OAuth 콜백
    path('google/callback/', oauth_views.GoogleCallbackView.as_view(), name='google_callback'),
    
    # 디버깅
    path('debug/', oauth_views.GoogleOAuthDebugView.as_view(), name='oauth_debug'),
    
    # 인증 상태 관리
    path('auth/status/', oauth_views.AuthStatusView.as_view(), name='auth_status'),
    path('profile/', oauth_views.UserProfileView.as_view(), name='user_profile'),
    path('logout/', oauth_views.LogoutView.as_view(), name='logout'),
]