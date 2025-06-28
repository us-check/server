import os
import json
import requests
import secrets
from urllib.parse import urlencode
from google.cloud import firestore
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings
from typing import Optional, Dict, Any

class FirestoreService:
    """Firestore 데이터베이스 서비스"""
    
    def __init__(self):
        self.db = firestore.Client(project=settings.FIRESTORE_PROJECT_ID)
        self.users_collection = 'users'
    
    def create_user(self, user_data: Dict[str, Any]) -> str:
        """사용자 생성"""
        doc_ref = self.db.collection(self.users_collection).document()
        user_data['created_at'] = firestore.SERVER_TIMESTAMP
        user_data['updated_at'] = firestore.SERVER_TIMESTAMP
        doc_ref.set(user_data)
        return doc_ref.id
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자 조회"""
        doc_ref = self.db.collection(self.users_collection).document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return {'id': doc.id, **doc.to_dict()}
        return None
    
    def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """Google ID로 사용자 조회"""
        users_ref = self.db.collection(self.users_collection)
        query = users_ref.where('google_id', '==', google_id).limit(1)
        docs = query.stream()
        
        for doc in docs:
            return {'id': doc.id, **doc.to_dict()}
        return None
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """사용자 정보 업데이트"""
        try:
            doc_ref = self.db.collection(self.users_collection).document(user_id)
            update_data['updated_at'] = firestore.SERVER_TIMESTAMP
            doc_ref.update(update_data)
            return True
        except Exception:
            return False

class GoogleOAuthService:
    """Google OAuth 서비스"""
    
    def __init__(self):
        self.client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
        self.client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
        # Firestore 초기화를 지연시켜 설정 오류 방지
        self._firestore_service = None
    
    @property
    def firestore_service(self):
        if self._firestore_service is None:
            self._firestore_service = FirestoreService()
        return self._firestore_service
    
    def get_authorization_url(self) -> str:
        """Google OAuth 인증 URL 생성"""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        
        # 안전한 state 생성
        state = secrets.token_urlsafe(32)
        
        # Google OAuth 2.0 표준 파라미터
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'select_account',
            'state': state,
            'include_granted_scopes': 'true'
        }
        
        # 올바른 URL 인코딩 사용
        query_string = urlencode(params)
        full_url = f"{base_url}?{query_string}"
        
        # 디버깅용 로그
        print(f"Generated OAuth URL: {full_url}")
        print(f"Client ID: {self.client_id[:20]}..." if self.client_id else "Client ID not set")
        print(f"Redirect URI: {self.redirect_uri}")
        
        return full_url
    
    def exchange_code_for_tokens(self, code: str) -> Optional[Dict[str, Any]]:
        """인증 코드를 토큰으로 교환"""
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            return response.json()
        return None
    
    def verify_id_token(self, id_token_str: str) -> Optional[Dict[str, Any]]:
        """ID 토큰 검증"""
        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_str, 
                google_requests.Request(), 
                self.client_id
            )
            return idinfo
        except ValueError:
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Google API에서 사용자 정보 가져오기"""
        url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    
    def authenticate_user(self, code: str) -> Optional[Dict[str, Any]]:
        """OAuth 코드로 사용자 인증 및 Firestore에 저장/업데이트"""
        # 1. 코드를 토큰으로 교환
        tokens = self.exchange_code_for_tokens(code)
        if not tokens:
            return None
        
        # 2. ID 토큰 검증
        user_info = self.verify_id_token(tokens.get('id_token'))
        if not user_info:
            return None
        
        # 3. 추가 사용자 정보 가져오기
        access_token = tokens.get('access_token')
        extended_info = self.get_user_info(access_token)
        
        # 4. Firestore에서 기존 사용자 확인
        google_id = user_info.get('sub')
        existing_user = self.firestore_service.get_user_by_google_id(google_id)
        
        user_data = {
            'google_id': google_id,
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'access_token': access_token,
            'refresh_token': tokens.get('refresh_token'),
            'is_verified': user_info.get('email_verified', False),
            'locale': extended_info.get('locale') if extended_info else None,
        }
        
        if existing_user:
            # 기존 사용자 업데이트
            self.firestore_service.update_user(existing_user['id'], user_data)
            user_data['id'] = existing_user['id']
        else:
            # 새 사용자 생성
            user_id = self.firestore_service.create_user(user_data)
            user_data['id'] = user_id
        
        return user_data