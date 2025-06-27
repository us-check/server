from django.urls import path
from . import firestore_views

app_name = 'api'

urlpatterns = [
    # 메인 API 엔드포인트 (Firestore 기반)
    path('query/', firestore_views.FirestoreQueryView.as_view(), name='firestore_query'),
    path('selection/', firestore_views.FirestoreSelectionView.as_view(), name='firestore_selection'),
    path('selections/', firestore_views.FirestoreUserSelectionsView.as_view(), name='firestore_user_selections'),
    
    # 데이터 조회 엔드포인트 (Firestore 기반)
    path('spots/', firestore_views.FirestoreAllSpotsView.as_view(), name='firestore_all_spots'),
    path('search/', firestore_views.FirestoreSearchView.as_view(), name='firestore_search'),
    path('spots/<str:spot_id>/', firestore_views.get_spot_detail, name='get_spot_detail'),
    
    # QR 코드 및 접근
    path('qr/<str:qr_id>/', firestore_views.qr_access, name='qr_access'),
    
    # 시스템 엔드포인트
    path('sync/', firestore_views.FirestoreSyncView.as_view(), name='firestore_sync'),
    path('health/', firestore_views.health_check, name='health_check'),
]
