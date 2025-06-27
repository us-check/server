"""
통합 API 서비스 - 메인 엔드포인트 처리
"""
import logging
import uuid
from typing import Dict, List
from django.contrib.auth.models import User
from django.utils import timezone
from tourism.services import TourismDataService
from tourism.models import UserTourismSelection, TourismSpot
from gemini_ai.services import GeminiAIService
from qr_service.services import QRCodeService

logger = logging.getLogger(__name__)

class TourismRecommendationService:
    """관광지 추천 통합 서비스"""
    
    def __init__(self):
        self.tourism_service = TourismDataService()
        self.gemini_service = GeminiAIService()
        self.qr_service = QRCodeService()
    
    def process_user_query(self, user_query: str, user: User = None, session_id: str = None) -> Dict:
        """사용자 쿼리 처리 - 메인 엔드포인트"""
        try:
            # 1. Gemini AI로 쿼리 분석 및 관광지 추천
            recommendation_result = self.gemini_service.recommend_tourism_spots(
                user_query=user_query,
                max_results=20  # 파친코 게임용으로 충분한 개수
            )
            
            if not recommendation_result['success']:
                return recommendation_result
            
            # 2. 사용자 선택 기록 생성
            selection_record = UserTourismSelection.objects.create(
                user=user,
                session_id=session_id or str(uuid.uuid4()),
                original_query=user_query,
                processed_query=recommendation_result['analysis'].get('processed_query', user_query),
                ai_analysis=recommendation_result['analysis']
            )
            
            # 3. 추천된 관광지들을 선택 기록에 연결
            recommended_spot_ids = [spot['id'] for spot in recommendation_result['recommended_spots']]
            recommended_spots = TourismSpot.objects.filter(id__in=recommended_spot_ids)
            selection_record.selected_spots.set(recommended_spots)
            
            # 4. 응답 데이터 구성
            response_data = {
                'success': True,
                'selection_id': selection_record.id,
                'query': user_query,
                'analysis': recommendation_result['analysis'],
                'recommended_spots': recommendation_result['recommended_spots'],
                'total_count': len(recommendation_result['recommended_spots']),
                'session_id': selection_record.session_id,
                'timestamp': selection_record.created_at.isoformat()
            }
            
            logger.info(f"Query processed successfully: {user_query} -> {len(recommendation_result['recommended_spots'])} spots")
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing user query: {e}")
            return {
                'success': False,
                'message': str(e),
                'query': user_query
            }
    
    def finalize_user_selection(self, selection_id: int, selected_spot_ids: List[int], 
                              user: User = None) -> Dict:
        """사용자의 최종 관광지 선택 처리"""
        try:
            # 1. 선택 기록 조회
            try:
                selection_record = UserTourismSelection.objects.get(id=selection_id)
            except UserTourismSelection.DoesNotExist:
                return {'success': False, 'message': 'Selection record not found'}
            
            # 2. 최종 선택된 관광지 업데이트
            selected_spots = TourismSpot.objects.filter(id__in=selected_spot_ids)
            selection_record.selected_spots.set(selected_spots)
            selection_record.updated_at = timezone.now()
            selection_record.save()
            
            # 3. QR 코드 생성
            qr_data = {
                'selection_id': selection_record.id,
                'spots': [spot.to_dict() for spot in selected_spots],
                'timestamp': timezone.now().isoformat(),
                'user_info': {
                    'user_id': user.id if user else None,
                    'username': user.username if user else None,
                    'session_id': selection_record.session_id
                },
                'original_query': selection_record.original_query
            }
            
            qr_result = self.qr_service.generate_qr_for_tourism_selection(qr_data)
            
            if qr_result['success']:
                # QR 코드 정보를 선택 기록에 업데이트
                selection_record.qr_code_url = qr_result['qr_url']
                selection_record.save()
            
            # 4. AI 기반 여행 설명 생성
            travel_description = self.gemini_service.generate_tourism_description(list(selected_spots))
            
            # 5. 응답 데이터 구성
            response_data = {
                'success': True,
                'selection_id': selection_record.id,
                'selected_spots': [spot.to_dict() for spot in selected_spots],
                'qr_code_url': qr_result.get('qr_url', '') if qr_result['success'] else '',
                'qr_access_url': qr_result.get('access_url', '') if qr_result['success'] else '',
                'travel_description': travel_description,
                'session_id': selection_record.session_id,
                'created_at': selection_record.created_at.isoformat(),
                'updated_at': selection_record.updated_at.isoformat()
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
        """사용자의 선택 기록 조회"""
        try:
            queryset = UserTourismSelection.objects.all()
            
            if user:
                queryset = queryset.filter(user=user)
            elif session_id:
                queryset = queryset.filter(session_id=session_id)
            
            selections = queryset.order_by('-created_at')[:limit]
            
            result_data = []
            for selection in selections:
                selected_spots = selection.selected_spots.all()
                result_data.append({
                    'selection_id': selection.id,
                    'original_query': selection.original_query,
                    'selected_spots': [spot.to_dict() for spot in selected_spots],
                    'qr_code_url': selection.qr_code_url,
                    'session_id': selection.session_id,
                    'created_at': selection.created_at.isoformat(),
                    'ai_analysis': selection.ai_analysis
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
                'message': str(e)
            }
    
    def get_all_tourism_spots(self) -> Dict:
        """모든 관광지 데이터 조회 (관리용)"""
        try:
            spots = self.tourism_service.get_all_tourism_spots()
            
            result_data = [spot.to_dict() for spot in spots]
            
            return {
                'success': True,
                'tourism_spots': result_data,
                'total_count': len(result_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting all tourism spots: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def sync_firestore_data(self) -> Dict:
        """Firestore 데이터 동기화"""
        try:
            sync_result = self.tourism_service.firestore_service.sync_tourism_data()
            
            logger.info(f"Firestore sync completed: {sync_result}")
            
            return sync_result
            
        except Exception as e:
            logger.error(f"Error syncing Firestore data: {e}")
            return {
                'success': False,
                'message': str(e)
            }
