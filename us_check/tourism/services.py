"""
Tourism 서비스 - Firestore와 관광지 데이터 관리
"""
import logging
from typing import List, Dict, Optional
from django.conf import settings
from django.db import models
from google.cloud import firestore
from .models import TourismSpot

logger = logging.getLogger(__name__)

class FirestoreService:
    """Firestore 데이터베이스 서비스"""
    
    def __init__(self):
        self.db = getattr(settings, 'FIRESTORE_CLIENT', None)
        self.collection_name = 'uiseong_tourism_spots'
    
    def sync_tourism_data(self) -> Dict:
        """Firestore에서 관광지 데이터를 가져와서 Django 모델과 동기화"""
        try:
            if not self.db:
                return {'success': False, 'message': 'Firestore client not initialized'}
            
            # Firestore에서 모든 관광지 데이터 가져오기
            docs = self.db.collection(self.collection_name).stream()
            
            synced_count = 0
            updated_count = 0
            
            for doc in docs:
                data = doc.to_dict()
                firestore_id = doc.id
                
                # Django 모델에 저장 또는 업데이트
                tourism_spot, created = TourismSpot.objects.update_or_create(
                    firestore_id=firestore_id,
                    defaults={
                        'name': data.get('name', ''),
                        'description': data.get('description', ''),
                        'address': data.get('address', ''),
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                        'category': data.get('category', ''),
                        'tags': data.get('tags', []),
                        'contact_info': data.get('contact_info', ''),
                        'website': data.get('website', ''),
                        'opening_hours': data.get('opening_hours', ''),
                        'raw_data': data,
                    }
                )
                
                if created:
                    synced_count += 1
                else:
                    updated_count += 1
            
            logger.info(f"Firestore sync completed: {synced_count} new, {updated_count} updated")
            
            return {
                'success': True,
                'synced_count': synced_count,
                'updated_count': updated_count,
                'total_count': synced_count + updated_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing Firestore data: {e}")
            return {'success': False, 'message': str(e)}
    
    def upload_tourism_data(self, tourism_data: List[Dict]) -> Dict:
        """관광지 데이터를 Firestore에 업로드"""
        try:
            if not self.db:
                return {'success': False, 'message': 'Firestore client not initialized'}
            
            batch = self.db.batch()
            uploaded_count = 0
            
            for data in tourism_data:
                # 문서 ID 생성 (name을 기반으로 하거나 자동 생성)
                doc_id = data.get('id') or data.get('name', '').replace(' ', '_').lower()
                if not doc_id:
                    continue
                
                doc_ref = self.db.collection(self.collection_name).document(doc_id)
                batch.set(doc_ref, data)
                uploaded_count += 1
            
            # 배치 커밋
            batch.commit()
            
            logger.info(f"Uploaded {uploaded_count} tourism spots to Firestore")
            
            return {
                'success': True,
                'uploaded_count': uploaded_count
            }
            
        except Exception as e:
            logger.error(f"Error uploading to Firestore: {e}")
            return {'success': False, 'message': str(e)}
    
    def search_tourism_spots(self, query_params: Dict) -> List[Dict]:
        """Firestore에서 관광지 검색"""
        try:
            if not self.db:
                return []
            
            query = self.db.collection(self.collection_name)
            
            # 카테고리 필터링
            if 'category' in query_params:
                query = query.where('category', '==', query_params['category'])
            
            # 추가 필터링 로직...
            
            results = []
            for doc in query.stream():
                data = doc.to_dict()
                data['firestore_id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Firestore: {e}")
            return []

    def clear_collection(self, collection_name: str = None) -> Dict:
        """Firestore 컬렉션의 모든 문서 삭제"""
        try:
            if not self.db:
                return {'success': False, 'message': 'Firestore client not initialized'}
            
            collection_name = collection_name or self.collection_name
            collection_ref = self.db.collection(collection_name)
            
            # 배치 삭제
            docs = collection_ref.limit(500).stream()
            deleted_count = 0
            
            batch = self.db.batch()
            batch_count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                batch_count += 1
                deleted_count += 1
                
                # 배치가 500개에 도달하면 커밋
                if batch_count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0
            
            # 마지막 배치 커밋
            if batch_count > 0:
                batch.commit()
            
            logger.info(f'Firestore 컬렉션 "{collection_name}" 에서 {deleted_count}개 문서 삭제')
            return {
                'success': True, 
                'message': f'{deleted_count}개 문서 삭제 완료',
                'deleted_count': deleted_count
            }
            
        except Exception as e:
            logger.error(f'Firestore 컬렉션 삭제 오류: {e}')
            return {'success': False, 'message': str(e)}
    
    def add_document(self, collection_name: str, document_data: Dict, doc_id: str = None) -> Dict:
        """Firestore 컬렉션에 문서 추가"""
        try:
            if not self.db:
                return {'success': False, 'message': 'Firestore client not initialized'}
            
            collection_ref = self.db.collection(collection_name)
            
            if doc_id:
                # 지정된 ID로 문서 생성/업데이트
                doc_ref = collection_ref.document(doc_id)
                doc_ref.set(document_data)
                return {'success': True, 'doc_id': doc_id, 'message': 'Document added with custom ID'}
            else:
                # 자동 ID로 문서 생성
                doc_ref = collection_ref.add(document_data)
                return {'success': True, 'doc_id': doc_ref[1].id, 'message': 'Document added with auto ID'}
                
        except Exception as e:
            logger.error(f'Firestore 문서 추가 오류: {e}')
            return {'success': False, 'message': str(e)}
    
    def get_all_documents(self, collection_name: str = None) -> List[Dict]:
        """Firestore 컬렉션의 모든 문서 조회"""
        try:
            if not self.db:
                logger.error('Firestore client not initialized')
                return []
            
            collection_name = collection_name or self.collection_name
            docs = self.db.collection(collection_name).stream()
            
            documents = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['id'] = doc.id
                documents.append(doc_data)
            
            return documents
            
        except Exception as e:
            logger.error(f'Firestore 문서 조회 오류: {e}')
            return []
    
    def query_documents(self, collection_name: str, field: str, operator: str, value) -> List[Dict]:
        """Firestore 컬렉션에서 조건부 쿼리"""
        try:
            if not self.db:
                logger.error('Firestore client not initialized')
                return []
            
            collection_name = collection_name or self.collection_name
            docs = self.db.collection(collection_name).where(field, operator, value).stream()
            
            documents = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['id'] = doc.id
                documents.append(doc_data)
            
            return documents
            
        except Exception as e:
            logger.error(f'Firestore 쿼리 오류: {e}')
            return []


class TourismDataService:
    """관광지 데이터 관리 서비스"""
    
    def __init__(self):
        self.firestore_service = FirestoreService()
    
    def get_all_tourism_spots(self) -> List[TourismSpot]:
        """모든 관광지 데이터 반환"""
        return TourismSpot.objects.filter(is_active=True)
    
    def search_spots_by_keywords(self, keywords: List[str]) -> List[TourismSpot]:
        """키워드로 관광지 검색 (SQLite 호환)"""
        if not keywords:
            return TourismSpot.objects.filter(is_active=True)
        
        # 각 키워드에 대해 OR 조건으로 검색
        query = models.Q()
        
        for keyword in keywords:
            keyword_query = (
                models.Q(name__icontains=keyword) |
                models.Q(description__icontains=keyword) |
                models.Q(category__icontains=keyword) |
                models.Q(address__icontains=keyword)
            )
            query |= keyword_query
        
        # 기본 쿼리 실행
        queryset = TourismSpot.objects.filter(query, is_active=True)
        
        return queryset
    
    def get_spots_by_category(self, category: str) -> List[TourismSpot]:
        """카테고리별 관광지 검색"""
        return TourismSpot.objects.filter(
            category__icontains=category,
            is_active=True
        )
    
    def get_nearby_spots(self, latitude: float, longitude: float, radius_km: float = 10) -> List[TourismSpot]:
        """근처 관광지 검색 (간단한 구현)"""
        # 실제로는 더 정교한 지리적 검색이 필요
        spots = TourismSpot.objects.filter(
            is_active=True,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        # 거리 계산 로직 추가 필요
        return spots[:10]  # 임시로 10개만 반환
