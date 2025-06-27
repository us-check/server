from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import logging

from .services import TourismRecommendationService

logger = logging.getLogger(__name__)

# 통합 서비스 인스턴스
recommendation_service = TourismRecommendationService()

@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
@csrf_exempt
def process_query(request):
    """
    사용자 자연어 쿼리 처리 엔드포인트
    
    POST Request Body:
    {
        "query": "자연 경관이 좋은 곳 추천해줘",
        "session_id": "optional_session_id",
        "user_id": "optional_user_id"
    }
    
    GET Request:
    /api/query/?query=자연경관이 좋은 곳 추천해줘&session_id=test
    """
    try:
        logger.info("=== process_query 시작 ===")
        
        # POST와 GET 요청 모두 지원
        if request.method == 'POST':
            data = request.data
            user_query = data.get('query', '').strip()
            user_id = data.get('user_id')
            session_id = data.get('session_id')
        else:  # GET 요청
            user_query = request.GET.get('query', '').strip()
            user_id = request.GET.get('user_id')
            session_id = request.GET.get('session_id')
        
        logger.info(f"쿼리: {user_query}")
        
        if not user_query:
            return Response({
                'success': False,
                'message': 'Query is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 사용자 정보 처리
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                logger.info(f"사용자 찾음: {user.username}")
            except User.DoesNotExist:
                logger.warning(f"User not found: {user_id}")
        
        logger.info("서비스 호출 시작")
        
        # 단계별로 서비스 호출 테스트
        try:
            # 1단계: 서비스 인스턴스 확인
            logger.info("recommendation_service 확인 중...")
            service = recommendation_service
            logger.info(f"서비스 타입: {type(service)}")
            
            # 2단계: 실제 호출
            logger.info("process_user_query 호출 중...")
            result = service.process_user_query(
                user_query=user_query,
                user=user,
                session_id=session_id
            )
            logger.info(f"서비스 호출 완료: {result.get('success', 'unknown')}")
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as service_error:
            logger.error(f"서비스 호출 오류: {service_error}")
            import traceback
            logger.error(f"서비스 오류 상세: {traceback.format_exc()}")
            
            # 서비스 오류 시 폴백 응답
            return Response({
                'success': False,
                'message': f'Service error: {str(service_error)}',
                'fallback': True,
                'query': user_query,
                'error_type': 'service_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in process_query: {e}")
        logger.error(f"Traceback: {error_trace}")
        
        return Response({
            'success': False,
            'message': f'Internal server error: {str(e)}',
            'error_detail': error_trace if settings.DEBUG else None,
            'error_type': 'general_error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def finalize_selection(request):
    """
    사용자의 최종 관광지 선택 처리 엔드포인트
    
    Request Body:
    {
        "selection_id": 123,
        "selected_spot_ids": [1, 3, 7, 12],
        "user_id": "optional_user_id"
    }
    """
    try:
        data = request.data
        selection_id = data.get('selection_id')
        selected_spot_ids = data.get('selected_spot_ids', [])
        
        if not selection_id:
            return Response({
                'success': False,
                'message': 'Selection ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not selected_spot_ids:
            return Response({
                'success': False,
                'message': 'Selected spot IDs are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 사용자 정보 처리
        user = None
        user_id = data.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"User not found: {user_id}")
        
        # 선택 완료 처리
        result = recommendation_service.finalize_user_selection(
            selection_id=selection_id,
            selected_spot_ids=selected_spot_ids,
            user=user
        )
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in finalize_selection: {e}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_history(request):
    """
    사용자 선택 기록 조회 엔드포인트
    
    Query Parameters:
    - user_id: 사용자 ID (optional)
    - session_id: 세션 ID (optional)
    - limit: 결과 개수 제한 (default: 10)
    """
    try:
        user_id = request.GET.get('user_id')
        session_id = request.GET.get('session_id')
        limit = int(request.GET.get('limit', 10))
        
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"User not found: {user_id}")
        
        result = recommendation_service.get_user_selections(
            user=user,
            session_id=session_id,
            limit=limit
        )
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in get_user_history: {e}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_spots(request):
    """
    모든 관광지 데이터 조회 엔드포인트 (관리/개발용)
    """
    try:
        result = recommendation_service.get_all_tourism_spots()
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in get_all_spots: {e}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def sync_firestore(request):
    """
    Firestore 데이터 동기화 엔드포인트 (관리용)
    """
    try:
        result = recommendation_service.sync_firestore_data()
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in sync_firestore: {e}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    서버 상태 확인 엔드포인트
    """
    return Response({
        'success': True,
        'message': 'Server is running',
        'timestamp': timezone.now().isoformat()
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def simple_query(request):
    """
    매우 간단한 쿼리 테스트
    """
    query = request.GET.get('query', 'no query')
    
    return Response({
        'success': True,
        'message': 'Simple query works!',
        'received_query': query,
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def test_query(request):
    """
    쿼리 테스트 엔드포인트 (간단한 버전)
    """
    try:
        query = request.GET.get('query', '')
        
        # 데이터베이스에서 관광지 몇 개만 가져오기
        from tourism.models import TourismSpot
        spots = TourismSpot.objects.all()[:5]
        
        result = {
            'success': True,
            'query': query,
            'test_spots': [
                {
                    'id': spot.id,
                    'name': spot.name,
                    'category': spot.category
                } for spot in spots
            ],
            'total_spots_in_db': TourismSpot.objects.count()
        }
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    """
    쿼리 테스트 엔드포인트 (간단한 버전)
    """
    try:
        query = request.GET.get('query', '')
        
        # 데이터베이스에서 관광지 몇 개만 가져오기
        from tourism.models import TourismSpot
        spots = TourismSpot.objects.all()[:5]
        
        result = {
            'success': True,
            'query': query,
            'test_spots': [
                {
                    'id': spot.id,
                    'name': spot.name,
                    'category': spot.category
                } for spot in spots
            ],
            'total_spots_in_db': TourismSpot.objects.count()
        }
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
