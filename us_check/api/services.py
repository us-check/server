"""
통합 API 서비스 - 완전히 Firestore 기반으로 리팩토링
Django 모델 제거, 순수 Firestore 서비스
"""
import logging
import uuid
from typing import Dict, List, Optional
from django.contrib.auth.models import User
from django.utils import timezone
from tourism.services import FirestoreTourismService
from gemini_ai.services import GeminiAIService
from qr_service.services import QRCodeService

logger = logging.getLogger(__name__)

class TourismRecommendationService:
    """관광지 추천 통합 서비스 - Firestore 기반"""
    
    def __init__(self):
        self.tourism_service = FirestoreTourismService()
        self.gemini_service = GeminiAIService()
        self.qr_service = QRCodeService()
        
    def process_user_query(self, user_query: str, user: User = None, session_id: str = None) -> Dict:
        """사용자 쿼리 처리 - 메인 엔드포인트"""
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            logger.info(f"Processing user query: {user_query[:100]}...")
            
            # 1. Gemini AI로 쿼리 분석 및 관광지 추천
            all_spots = self.tourism_service.get_all_spots()
            recommendation_result = self.gemini_service.recommend_tourism_spots(
                user_query, all_spots
            )
            
            if not recommendation_result.get('success', False):
                return {
                    'success': False,
                    'message': recommendation_result.get('message', 'AI 추천 실패')
                }
            
            # 2. 사용자 선택 기록 Firestore에 저장
            selection_data = {
                'user_id': user.id if user else None,
                'username': user.username if user else None,
                'session_id': session_id,
                'original_query': user_query,
                'processed_query': user_query,
                'ai_analysis': recommendation_result['analysis'],
                'recommended_spots': recommendation_result['recommended_spots'],
                'created_at': timezone.now().isoformat(),
                'updated_at': timezone.now().isoformat(),
                'status': 'pending'
            }
            
            selection_id = self.tourism_service.create_user_selection(selection_data)
            
            # 3. 응답 데이터 구성
            response_data = {
                'success': True,
                'selection_id': selection_id,
                'query': user_query,
                'analysis': recommendation_result['analysis'],
                'recommended_spots': recommendation_result['recommended_spots'],
                'session_id': session_id,
                'user_info': {
                    'user_id': user.id if user else None,
                    'username': user.username if user else None
                }
            }
            
            logger.info(f"Query processed successfully: {len(recommendation_result['recommended_spots'])} spots recommended")
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing user query: {e}")
            return {
                'success': False,
                'message': f'쿼리 처리 중 오류가 발생했습니다: {str(e)}',
                'session_id': session_id
            }
    
    def finalize_user_selection(self, selection_id: str, selected_spot_ids: List[str], 
                              user: User = None) -> Dict:
        """사용자의 최종 관광지 선택 처리 - Firestore 기반"""
        try:
            # 1. 선택 기록 조회
            selection_record = self.tourism_service.get_user_selection(selection_id)
            if not selection_record:
                return {'success': False, 'message': 'Selection record not found'}
            
            # 2. 선택된 관광지 정보 조회
            selected_spots = []
            for spot_id in selected_spot_ids:
                spot = self.tourism_service.get_spot_by_id(spot_id)
                if spot:
                    selected_spots.append(spot)
            
            if not selected_spots:
                return {'success': False, 'message': 'No valid spots selected'}
            
            # 3. QR 코드 생성
            qr_data = {
                'selection_id': selection_id,
                'spots': selected_spots,
                'timestamp': timezone.now().isoformat(),
                'user_info': {
                    'user_id': user.id if user else None,
                    'username': user.username if user else None,
                    'session_id': selection_record.get('session_id', '')
                },
                'original_query': selection_record.get('original_query', '')
            }
            
            qr_result = self.qr_service.generate_qr_for_tourism_selection(qr_data)
            
            # 4. 선택 기록 업데이트
            update_data = {
                'selected_spots': selected_spots,
                'selected_spot_ids': selected_spot_ids,
                'qr_code_url': qr_result.get('qr_url', '') if qr_result.get('success') else '',
                'qr_access_url': qr_result.get('access_url', '') if qr_result.get('success') else '',
                'updated_at': timezone.now().isoformat(),
                'status': 'completed'
            }
            
            self.tourism_service.update_user_selection(selection_id, update_data)
            
            # 5. AI 기반 여행 설명 생성
            travel_description = self.gemini_service.generate_tourism_description(selected_spots)
            
            # 6. 응답 데이터 구성
            response_data = {
                'success': True,
                'selection_id': selection_id,
                'selected_spots': selected_spots,
                'qr_code_url': qr_result.get('qr_url', '') if qr_result.get('success') else '',
                'qr_access_url': qr_result.get('access_url', '') if qr_result.get('success') else '',
                'travel_description': travel_description,
                'session_id': selection_record.get('session_id', ''),
                'created_at': selection_record.get('created_at', ''),
                'updated_at': update_data['updated_at']
            }
            
            logger.info(f"User selection finalized: {selection_id} -> {len(selected_spot_ids)} spots")
            return response_data
            
        except Exception as e:
            logger.error(f"Error finalizing user selection: {e}")
            return {
                'success': False,
                'message': str(e),
                'selection_id': selection_id
            }
    
    def get_user_selections(self, user: User = None, session_id: str = None, 
                           limit: int = 10) -> Dict:
        """사용자의 선택 기록 조회 - Firestore 기반"""
        try:
            # Firestore에서 사용자 선택 기록 조회
            selections = self.tourism_service.get_user_selections(
                user_id=user.id if user else None,
                session_id=session_id,
                limit=limit
            )
            
            result_data = []
            for selection in selections:
                result_data.append({
                    'selection_id': selection.get('id', ''),
                    'original_query': selection.get('original_query', ''),
                    'selected_spots': selection.get('selected_spots', []),
                    'qr_code_url': selection.get('qr_code_url', ''),
                    'session_id': selection.get('session_id', ''),
                    'created_at': selection.get('created_at', ''),
                    'updated_at': selection.get('updated_at', ''),
                    'status': selection.get('status', 'unknown')
                })
            
            return {
                'success': True,
                'selections': result_data,
                'total_count': len(result_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting user selections: {e}")
            return {
                'success': False,
                'message': str(e),
                'selections': []
            }
    
    def get_all_tourism_spots(self) -> Dict:
        """모든 관광지 데이터 조회 (관리용) - Firestore 기반"""
        try:
            spots = self.tourism_service.get_all_spots()
            
            return {
                'success': True,
                'spots': spots,
                'total_count': len(spots)
            }
            
        except Exception as e:
            logger.error(f"Error getting all tourism spots: {e}")
            return {
                'success': False,
                'message': str(e),
                'spots': []
            }
    
    def sync_firestore_data(self) -> Dict:
        """Firestore 데이터 동기화"""
        try:
            result = self.tourism_service.sync_all_data()
            return result
            
        except Exception as e:
            logger.error(f"Error syncing Firestore data: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def search_spots_by_keywords(self, keywords: List[str]) -> Dict:
        """키워드로 관광지 검색 - Firestore 기반"""
        try:
            spots = self.tourism_service.search_spots_by_keywords(keywords)
            
            return {
                'success': True,
                'spots': spots,
                'total_count': len(spots),
                'keywords': keywords
            }
            
        except Exception as e:
            logger.error(f"Error searching spots by keywords: {e}")
            return {
                'success': False,
                'message': str(e),
                'spots': []
            }
