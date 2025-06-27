from django.urls import path
from . import views
from .firestore_views import (
    FirestoreQueryView, FirestoreFinalizeView, FirestoreSpotsView,
    FirestoreHistoryView, FirestoreStatsView, FirestoreHealthView
)

app_name = 'api'

urlpatterns = [
    # 기존 Django ORM 기반 API
    path('query/', views.process_query, name='process_query'),
    path('finalize/', views.finalize_selection, name='finalize_selection'),
    path('history/', views.get_user_history, name='get_user_history'),
    path('spots/', views.get_all_spots, name='get_all_spots'),
    path('sync/', views.sync_firestore, name='sync_firestore'),
    path('health/', views.health_check, name='health_check'),
    path('test/', views.test_query, name='test_query'),
    path('simple/', views.simple_query, name='simple_query'),
    
    # Firestore 기반 API (새로운 엔드포인트)
    path('fs/query/', FirestoreQueryView.as_view(), name='firestore_query'),
    path('fs/finalize/', FirestoreFinalizeView.as_view(), name='firestore_finalize'),
    path('fs/spots/', FirestoreSpotsView.as_view(), name='firestore_spots'),
    path('fs/history/', FirestoreHistoryView.as_view(), name='firestore_history'),
    path('fs/stats/', FirestoreStatsView.as_view(), name='firestore_stats'),
    path('fs/health/', FirestoreHealthView.as_view(), name='firestore_health'),
]
