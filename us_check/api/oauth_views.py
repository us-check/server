import os
import json
import sys
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

# GoogleOAuthService import 수정
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'accounts'))
from services import GoogleOAuthService

class GoogleAuthRedirectView(View):
    """Google OAuth로 직접 리다이렉트"""
    
    def get(self, request):
        try:
            oauth_service = GoogleOAuthService()
            auth_url = oauth_service.get_authorization_url()
            
            # 브라우저를 Google OAuth로 직접 리다이렉트
            return redirect(auth_url)
        except Exception as e:
            return JsonResponse({
                'error': f'Failed to redirect to Google OAuth: {str(e)}',
                'suggestion': 'Check your Google OAuth configuration'
            }, status=500)

class GoogleAuthURLView(View):
    """Google OAuth URL 생성 API (JSON 응답)"""
    
    def get(self, request):
        try:
            oauth_service = GoogleOAuthService()
            auth_url = oauth_service.get_authorization_url()
            
            return JsonResponse({
                'auth_url': auth_url,
                'success': True
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'success': False
            }, status=500)

class GoogleOAuthDebugView(View):
    """Google OAuth 설정 디버깅"""
    
    def get(self, request):
        try:
            # 환경변수와 Django settings 모두 확인
            env_client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
            env_redirect_uri = os.getenv('GOOGLE_OAUTH2_REDIRECT_URI', 'http://localhost:8000/api/oauth/google/callback/')
            
            settings_client_id = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None)
            settings_redirect_uri = getattr(settings, 'GOOGLE_OAUTH2_REDIRECT_URI', None)
            
            # 설정 검증
            if not env_client_id and not settings_client_id:
                return JsonResponse({'error': 'GOOGLE_OAUTH2_CLIENT_ID not configured in env or settings'}, status=400)
            
            # 사용할 값 결정 (settings 우선)
            client_id = settings_client_id or env_client_id
            redirect_uri = settings_redirect_uri or env_redirect_uri
            
            # Google 표준 형식으로 URL 생성 (수동)
            if client_id:
                import requests
                
                params = [
                    ('scope', 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid'),
                    ('access_type', 'offline'),
                    ('include_granted_scopes', 'true'),
                    ('response_type', 'code'),
                    ('state', 'debug_state_123'),
                    ('redirect_uri', redirect_uri),
                    ('client_id', client_id)
                ]
                
                query_parts = []
                for key, value in params:
                    encoded_value = requests.utils.quote(str(value), safe='')
                    query_parts.append(f"{key}={encoded_value}")
                
                query_string = '&'.join(query_parts)
                manual_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
            else:
                manual_auth_url = "No client_id found"
            
            # 서비스를 통한 URL 생성도 테스트
            try:
                oauth_service = GoogleOAuthService()
                service_auth_url = oauth_service.get_authorization_url()
            except Exception as e:
                service_auth_url = f"Service error: {str(e)}"
            
            return JsonResponse({
                'success': True,
                'config': {
                    'env_client_id': env_client_id[:20] + '...' if env_client_id else 'Not found',
                    'settings_client_id': settings_client_id[:20] + '...' if settings_client_id else 'Not found',
                    'using_client_id': client_id[:20] + '...' if client_id else 'Not found',
                    'redirect_uri': redirect_uri,
                    'env_file_exists': os.path.exists('.env')
                },
                'urls': {
                    'manual_generated': manual_auth_url,
                    'service_generated': service_auth_url
                },
                'instructions': 'Copy either auth_url and paste it in your browser to test OAuth flow'
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Debug error: {str(e)}',
                'type': type(e).__name__
            }, status=500)

class GoogleCallbackView(View):
    """Google OAuth 콜백 처리"""
    
    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        state = request.GET.get('state')
        
        if error:
            return JsonResponse({'error': error}, status=400)
        
        if not code:
            return JsonResponse({'error': 'No authorization code provided'}, status=400)
        
        # 임시로 성공 응답 (실제 토큰 교환은 나중에 구현)
        return JsonResponse({
            'success': True,
            'message': 'OAuth callback received successfully',
            'code': code[:20] + '...',  # 보안상 일부만 표시
            'state': state,
            'next_step': 'Token exchange implementation needed'
        })

class AuthStatusView(View):
    """인증 상태 확인 API"""
    
    def get(self, request):
        user_id = request.session.get('user_id')
        authenticated = request.session.get('authenticated', False)
        
        if authenticated and user_id:
            try:
                oauth_service = GoogleOAuthService()
                user_data = oauth_service.firestore_service.get_user(user_id)
                
                if user_data:
                    return JsonResponse({
                        'authenticated': True,
                        'user': {
                            'id': user_data['id'],
                            'email': user_data['email'],
                            'name': user_data['name'],
                            'picture': user_data['picture']
                        }
                    })
            except Exception as e:
                return JsonResponse({
                    'authenticated': False,
                    'error': f'Failed to get user data: {str(e)}'
                })
        
        return JsonResponse({'authenticated': False})

@method_decorator(csrf_exempt, name='dispatch')
class UserProfileView(View):
    """사용자 프로필 조회/업데이트"""
    
    def get(self, request):
        """현재 사용자 프로필 조회"""
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        try:
            oauth_service = GoogleOAuthService()
            user_data = oauth_service.firestore_service.get_user(user_id)
            if not user_data:
                return JsonResponse({'error': 'User not found'}, status=404)
            
            # 민감한 정보 제거
            safe_user_data = {
                'id': user_data['id'],
                'email': user_data['email'],
                'name': user_data['name'],
                'picture': user_data['picture'],
                'is_verified': user_data.get('is_verified', False),
                'locale': user_data.get('locale')
            }
            
            return JsonResponse({'user': safe_user_data})
        except Exception as e:
            return JsonResponse({'error': f'Profile fetch failed: {str(e)}'}, status=500)
    
    def patch(self, request):
        """사용자 프로필 업데이트"""
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        try:
            data = json.loads(request.body)
            # 업데이트 가능한 필드만 허용
            allowed_fields = ['name', 'locale']
            update_data = {k: v for k, v in data.items() if k in allowed_fields}
            
            if not update_data:
                return JsonResponse({'error': 'No valid fields to update'}, status=400)
            
            oauth_service = GoogleOAuthService()
            success = oauth_service.firestore_service.update_user(user_id, update_data)
            if success:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': 'Update failed'}, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Update failed: {str(e)}'}, status=500)

class LogoutView(View):
    """로그아웃"""
    
    def post(self, request):
        """세션 삭제하여 로그아웃"""
        request.session.flush()
        return JsonResponse({'success': True, 'message': 'Logged out successfully'})