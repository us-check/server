"""
Firestore 기반 API 뷰
Django ORM 대신 Firestore를 직접 사용하는 API 엔드포인트
"""
import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .firestore_services import FirestoreTourismService
from qr_service.services import QRCodeService

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class FirestoreQueryView(View):
    """Firestore 기반 자연어 쿼리 처리"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = FirestoreTourismService()
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_query = data.get('query', '').strip()
            
            if not user_query:
                return JsonResponse({
                    'success': False,
                    'message': '검색어를 입력해주세요.'
                }, status=400)
            
            # Firestore에서 추천 결과 가져오기
            result = self.tourism_service.get_recommendations_by_query(user_query)
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '잘못된 JSON 형식입니다.'
            }, status=400)
        except Exception as e:
            logger.error(f'Firestore 쿼리 처리 오류: {e}')
            return JsonResponse({
                'success': False,
                'message': f'서버 오류: {str(e)}'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FirestoreFinalizeView(View):
    """Firestore 기반 사용자 선택 저장 및 QR 코드 생성"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = FirestoreTourismService()
        self.qr_service = QRCodeService()
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_query = data.get('query', '')
            selected_spots = data.get('selected_spots', [])
            session_id = data.get('session_id')
            
            if not selected_spots:
                return JsonResponse({
                    'success': False,
                    'message': '선택된 관광지가 없습니다.'
                }, status=400)
            
            # 사용자 선택 저장
            save_result = self.tourism_service.save_user_selection(
                user_query, selected_spots, session_id
            )
            
            if not save_result.get('success'):
                return JsonResponse(save_result, status=500)
            
            # 선택된 관광지 정보 가져오기
            selected_spot_details = []
            for spot_id in selected_spots:
                spot = self.tourism_service.get_spot_by_id(spot_id)
                if spot:
                    selected_spot_details.append(spot)
            
            # QR 코드 생성
            qr_data = {
                'query': user_query,
                'spots': selected_spot_details,
                'selection_id': save_result.get('selection_id'),
                'timestamp': str(data.get('timestamp', ''))
            }
            
            qr_result = self.qr_service.generate_qr_code(
                json.dumps(qr_data, ensure_ascii=False),
                f"uiseong_selection_{save_result.get('selection_id')}"
            )
            
            return JsonResponse({
                'success': True,
                'message': '선택이 완료되었습니다.',
                'selection_id': save_result.get('selection_id'),
                'selected_spots': selected_spot_details,
                'qr_code': qr_result
            })
            
        except Exception as e:
            logger.error(f'Firestore 선택 완료 처리 오류: {e}')
            return JsonResponse({
                'success': False,
                'message': f'서버 오류: {str(e)}'
            }, status=500)

class FirestoreSpotsView(View):
    """Firestore 기반 관광지 목록 조회"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = FirestoreTourismService()
    
    def get(self, request):
        try:
            # 쿼리 파라미터
            category = request.GET.get('category')
            keyword = request.GET.get('keyword')
            popular = request.GET.get('popular', 'false').lower() == 'true'
            with_images = request.GET.get('with_images', 'false').lower() == 'true'
            limit = int(request.GET.get('limit', 20))
            
            if popular:
                # 인기 관광지
                spots = self.tourism_service.get_popular_spots(limit)
            elif with_images:
                # 이미지가 있는 관광지
                spots = self.tourism_service.get_spots_with_images(limit)
            elif category:
                # 카테고리별 관광지
                spots = self.tourism_service.get_spots_by_category(category)[:limit]
            elif keyword:
                # 키워드 검색
                spots = self.tourism_service.search_spots_by_keyword(keyword)[:limit]
            else:
                # 전체 관광지
                spots = self.tourism_service.get_all_spots()[:limit]
            
            return JsonResponse({
                'success': True,
                'spots': spots,
                'count': len(spots)
            })
            
        except Exception as e:
            logger.error(f'Firestore 관광지 목록 조회 오류: {e}')
            return JsonResponse({
                'success': False,
                'message': f'서버 오류: {str(e)}'
            }, status=500)

class FirestoreHistoryView(View):
    """Firestore 기반 사용자 히스토리 조회"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = FirestoreTourismService()
    
    def get(self, request):
        try:
            session_id = request.GET.get('session_id')
            limit = int(request.GET.get('limit', 10))
            
            history = self.tourism_service.get_user_history(session_id, limit)
            
            return JsonResponse({
                'success': True,
                'history': history,
                'count': len(history)
            })
            
        except Exception as e:
            logger.error(f'Firestore 히스토리 조회 오류: {e}')
            return JsonResponse({
                'success': False,
                'message': f'서버 오류: {str(e)}'
            }, status=500)

class FirestoreStatsView(View):
    """Firestore 기반 통계 정보"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = FirestoreTourismService()
    
    def get(self, request):
        try:
            stats = self.tourism_service.get_statistics()
            
            return JsonResponse({
                'success': True,
                'statistics': stats
            })
            
        except Exception as e:
            logger.error(f'Firestore 통계 조회 오류: {e}')
            return JsonResponse({
                'success': False,
                'message': f'서버 오류: {str(e)}'
            }, status=500)

class FirestoreHealthView(View):
    """Firestore 기반 서비스 상태 체크"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = FirestoreTourismService()
    
    def get(self, request):
        try:
            # Firestore 연결 테스트
            total_spots = len(self.tourism_service.get_all_spots())
            
            return JsonResponse({
                'success': True,
                'message': 'Firestore 기반 서비스가 정상적으로 작동 중입니다.',
                'database': 'Firestore',
                'total_spots': total_spots,
                'collection': self.tourism_service.collection_name
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Firestore 서비스 오류: {str(e)}',
                'database': 'Firestore'
            }, status=500)
