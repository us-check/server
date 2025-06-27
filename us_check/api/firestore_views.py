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
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .services import TourismRecommendationService
from qr_service.services import QRCodeService

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class FirestoreQueryView(View):
    """Firestore 기반 자연어 쿼리 처리"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = TourismRecommendationService()
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_query = data.get('query', '').strip()
            session_id = data.get('session_id')
            
            if not user_query:
                return JsonResponse({
                    'success': False,
                    'message': '검색어를 입력해주세요.'
                }, status=400)
            
            # 사용자 정보 (인증된 경우)
            user = request.user if request.user.is_authenticated else None
            
            # Firestore에서 추천 결과 가져오기
            result = self.tourism_service.process_user_query(
                user_query=user_query,
                user=user,
                session_id=session_id
            )
            
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
class FirestoreSelectionView(View):
    """사용자의 최종 관광지 선택 처리"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = TourismRecommendationService()
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            selection_id = data.get('selection_id')
            selected_spot_ids = data.get('selected_spot_ids', [])
            
            if not selection_id:
                return JsonResponse({
                    'success': False,
                    'message': '선택 ID가 필요합니다.'
                }, status=400)
            
            if not selected_spot_ids:
                return JsonResponse({
                    'success': False,
                    'message': '선택된 관광지가 없습니다.'
                }, status=400)
            
            # 사용자 정보 (인증된 경우)
            user = request.user if request.user.is_authenticated else None
            
            # 최종 선택 처리
            result = self.tourism_service.finalize_user_selection(
                selection_id=selection_id,
                selected_spot_ids=selected_spot_ids,
                user=user
            )
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '잘못된 JSON 형식입니다.'
            }, status=400)
        except Exception as e:
            logger.error(f'선택 처리 오류: {e}')
            return JsonResponse({
                'success': False,
                'message': f'서버 오류: {str(e)}'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FirestoreUserSelectionsView(View):
    """사용자 선택 기록 조회"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = TourismRecommendationService()
    
    def get(self, request):
        try:
            session_id = request.GET.get('session_id')
            limit = int(request.GET.get('limit', 10))
            
            # 사용자 정보 (인증된 경우)
            user = request.user if request.user.is_authenticated else None
            
            # 선택 기록 조회
            result = self.tourism_service.get_user_selections(
                user=user,
                session_id=session_id,
                limit=limit
            )
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f'선택 기록 조회 오류: {e}')
            return JsonResponse({
                'success': False,
                'message': f'서버 오류: {str(e)}'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FirestoreAllSpotsView(View):
    """모든 관광지 데이터 조회 (관리용)"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = TourismRecommendationService()
    
    def get(self, request):
        try:
            result = self.tourism_service.get_all_tourism_spots()
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f'관광지 데이터 조회 오류: {e}')
            return JsonResponse({
                'success': False,
                'message': f'서버 오류: {str(e)}'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FirestoreSearchView(View):
    """키워드로 관광지 검색"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = TourismRecommendationService()
    
    def get(self, request):
        try:
            keywords = request.GET.get('keywords', '').strip()
            if not keywords:
                return JsonResponse({
                    'success': False,
                    'message': '검색 키워드를 입력해주세요.'
                }, status=400)
            
            # 키워드를 리스트로 변환
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            
            result = self.tourism_service.search_spots_by_keywords(keyword_list)
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f'키워드 검색 오류: {e}')
            return JsonResponse({
                'success': False,
                'message': f'서버 오류: {str(e)}'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FirestoreSyncView(View):
    """Firestore 데이터 동기화 (관리용)"""
    
    def __init__(self):
        super().__init__()
        self.tourism_service = TourismRecommendationService()
    
    def post(self, request):
        try:
            result = self.tourism_service.sync_firestore_data()
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f'Firestore 동기화 오류: {e}')
            return JsonResponse({
                'success': False,
                'message': f'서버 오류: {str(e)}'
            }, status=500)

# 함수형 뷰들
@csrf_exempt
def get_spot_detail(request, spot_id):
    """특정 관광지 상세 정보"""
    try:
        tourism_service = TourismRecommendationService()
        
        # Firestore에서 관광지 정보 조회
        spots = tourism_service.get_all_tourism_spots()
        if not spots['success']:
            return JsonResponse({
                'success': False,
                'message': '관광지 데이터를 가져올 수 없습니다.'
            }, status=500)
        
        # 해당 ID의 관광지 찾기
        spot = None
        for s in spots['spots']:
            if str(s.get('id')) == str(spot_id) or s.get('firestore_id') == str(spot_id):
                spot = s
                break
        
        if not spot:
            return JsonResponse({
                'success': False,
                'message': '관광지를 찾을 수 없습니다.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'spot': spot
        })
        
    except Exception as e:
        logger.error(f'관광지 상세 조회 오류: {e}')
        return JsonResponse({
            'success': False,
            'message': f'서버 오류: {str(e)}'
        }, status=500)

@csrf_exempt
def qr_access(request, qr_id):
    """QR 코드로 관광지 정보 접근"""
    try:
        qr_service = QRCodeService()
        
        # QR 코드 정보 조회
        qr_data = qr_service.get_qr_data(qr_id)
        
        if not qr_data:
            return JsonResponse({
                'success': False,
                'message': 'QR 코드 정보를 찾을 수 없습니다.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'qr_data': qr_data
        })
        
    except Exception as e:
        logger.error(f'QR 접근 오류: {e}')
        return JsonResponse({
            'success': False,
            'message': f'서버 오류: {str(e)}'
        }, status=500)

@csrf_exempt
def health_check(request):
    """서비스 상태 확인"""
    try:
        tourism_service = TourismRecommendationService()
        
        # Firestore 연결 상태 확인
        result = tourism_service.sync_firestore_data()
        
        return JsonResponse({
            'success': True,
            'status': 'healthy',
            'firestore_status': result.get('success', False),
            'message': 'API 서비스가 정상 작동 중입니다.'
        })
        
    except Exception as e:
        logger.error(f'헬스체크 오류: {e}')
        return JsonResponse({
            'success': False,
            'status': 'unhealthy',
            'message': f'서비스 오류: {str(e)}'
        }, status=500)
