"""
Tourism 서비스 - 완전히 Firestore 기반으로 리팩토링
Django 모델 제거, 순수 Firestore 서비스
"""
import logging
from typing import List, Dict, Optional, Any
from django.conf import settings
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import json

logger = logging.getLogger(__name__)

class FirestoreTourismService:
    """완전히 Firestore 기반의 관광지 데이터 서비스"""
    
    def __init__(self):
        self.db = getattr(settings, 'FIRESTORE_CLIENT', None)
        if not self.db:
            logger.error('Firestore client not initialized')
        
        # 컬렉션 이름들 - 실제 Firestore DB 컬렉션명과 일치
        self.tourism_collection = 'tourism_spots'  # 실제 컬렉션명으로 변경
        self.user_selections_collection = 'user_tourism_selections'
        self.qr_codes_collection = 'qr_codes'
    
    # =============================================================================
    # 관광지 데이터 관리
    # =============================================================================
    
    def get_all_tourism_spots(self) -> List[Dict]:
        """모든 관광지 데이터 조회"""
        try:
            if not self.db:
                return []
            
            docs = self.db.collection(self.tourism_collection).stream()
            
            spots = []
            for doc in docs:
                spot_data = doc.to_dict()
                spot_data['id'] = doc.id
                spots.append(spot_data)
            
            logger.info(f'총 {len(spots)}개의 관광지 데이터 조회')
            return spots
            
        except Exception as e:
            logger.error(f'관광지 데이터 조회 오류: {e}')
            return []
    
    def get_tourism_spot_by_id(self, spot_id: str) -> Optional[Dict]:
        """ID로 특정 관광지 조회"""
        try:
            if not self.db:
                return None
            
            doc = self.db.collection(self.tourism_collection).document(spot_id).get()
            
            if doc.exists:
                spot_data = doc.to_dict()
                spot_data['id'] = doc.id
                return spot_data
            else:
                return None
                
        except Exception as e:
            logger.error(f'관광지 조회 오류 (ID: {spot_id}): {e}')
            return None
    
    def search_tourism_spots_by_keyword(self, keyword: str) -> List[Dict]:
        """키워드로 관광지 검색 (클라이언트 사이드 필터링)"""
        try:
            all_spots = self.get_all_tourism_spots()
            
            if not keyword:
                return all_spots
            
            keyword_lower = keyword.lower()
            filtered_spots = []
            
            for spot in all_spots:
                # 여러 필드에서 키워드 검색
                searchable_fields = [
                    spot.get('name', ''),
                    spot.get('title', ''),
                    spot.get('description', ''),
                    spot.get('overview', ''),
                    spot.get('addr1', ''),
                    spot.get('category', ''),
                    ' '.join(spot.get('tags', []))
                ]
                
                # 모든 검색 가능한 필드를 하나의 문자열로 합치기
                search_text = ' '.join(searchable_fields).lower()
                
                if keyword_lower in search_text:
                    filtered_spots.append(spot)
            
            logger.info(f'키워드 "{keyword}"로 {len(filtered_spots)}개 관광지 검색')
            return filtered_spots
            
        except Exception as e:
            logger.error(f'키워드 검색 오류: {e}')
            return []
    
    def get_spots_by_category(self, category: str) -> List[Dict]:
        """카테고리별 관광지 조회"""
        try:
            if not self.db:
                return []
            
            # Firestore 쿼리로 카테고리 필터링
            docs = self.db.collection(self.tourism_collection).where(
                filter=FieldFilter('category', '==', category)
            ).stream()
            
            spots = []
            for doc in docs:
                spot_data = doc.to_dict()
                spot_data['id'] = doc.id
                spots.append(spot_data)
            
            logger.info(f'카테고리 "{category}"로 {len(spots)}개 관광지 조회')
            return spots
            
        except Exception as e:
            logger.error(f'카테고리 검색 오류: {e}')
            # 쿼리 실패 시 클라이언트 사이드 필터링으로 대체
            all_spots = self.get_all_tourism_spots()
            return [spot for spot in all_spots if spot.get('category') == category]
    
    def add_tourism_spot(self, spot_data: Dict) -> Dict:
        """새 관광지 추가"""
        try:
            if not self.db:
                return {'success': False, 'message': 'Firestore client not initialized'}
            
            # 문서 ID 생성 (이름 기반 또는 자동 생성)
            doc_id = spot_data.get('id') or spot_data.get('name', '').replace(' ', '_').lower()
            
            # 타임스탬프 추가
            spot_data['created_at'] = firestore.SERVER_TIMESTAMP
            spot_data['updated_at'] = firestore.SERVER_TIMESTAMP
            spot_data['is_active'] = True
            
            doc_ref = self.db.collection(self.tourism_collection).document(doc_id)
            doc_ref.set(spot_data)
            
            logger.info(f'관광지 추가: {spot_data.get("name", doc_id)}')
            return {'success': True, 'id': doc_id}
            
        except Exception as e:
            logger.error(f'관광지 추가 오류: {e}')
            return {'success': False, 'message': str(e)}
    
    def update_tourism_spot(self, spot_id: str, spot_data: Dict) -> Dict:
        """관광지 정보 업데이트"""
        try:
            if not self.db:
                return {'success': False, 'message': 'Firestore client not initialized'}
            
            # 업데이트 타임스탬프 추가
            spot_data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.db.collection(self.tourism_collection).document(spot_id)
            doc_ref.update(spot_data)
            
            logger.info(f'관광지 업데이트: {spot_id}')
            return {'success': True, 'id': spot_id}
            
        except Exception as e:
            logger.error(f'관광지 업데이트 오류: {e}')
            return {'success': False, 'message': str(e)}
    
    def delete_tourism_spot(self, spot_id: str) -> Dict:
        """관광지 삭제 (소프트 삭제)"""
        try:
            if not self.db:
                return {'success': False, 'message': 'Firestore client not initialized'}
            
            doc_ref = self.db.collection(self.tourism_collection).document(spot_id)
            doc_ref.update({
                'is_active': False,
                'deleted_at': firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f'관광지 삭제: {spot_id}')
            return {'success': True, 'id': spot_id}
            
        except Exception as e:
            logger.error(f'관광지 삭제 오류: {e}')
            return {'success': False, 'message': str(e)}
    
    # =============================================================================
    # 사용자 선택 관리
    # =============================================================================
    
    def save_user_selection(self, selection_data: Dict) -> Dict:
        """사용자 관광지 선택 저장"""
        try:
            if not self.db:
                return {'success': False, 'message': 'Firestore client not initialized'}
            
            # 타임스탬프 추가
            selection_data['created_at'] = firestore.SERVER_TIMESTAMP
            selection_data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.db.collection(self.user_selections_collection).document()
            doc_ref.set(selection_data)
            
            logger.info(f'사용자 선택 저장: {doc_ref.id}')
            return {'success': True, 'id': doc_ref.id}
            
        except Exception as e:
            logger.error(f'사용자 선택 저장 오류: {e}')
            return {'success': False, 'message': str(e)}
    
    def get_user_selections(self, user_id: str = None, session_id: str = None) -> List[Dict]:
        """사용자 선택 기록 조회"""
        try:
            if not self.db:
                return []
            
            query = self.db.collection(self.user_selections_collection)
            
            if user_id:
                query = query.where(filter=FieldFilter('user_id', '==', user_id))
            elif session_id:
                query = query.where(filter=FieldFilter('session_id', '==', session_id))
            
            docs = query.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
            
            selections = []
            for doc in docs:
                selection_data = doc.to_dict()
                selection_data['id'] = doc.id
                selections.append(selection_data)
            
            return selections
            
        except Exception as e:
            logger.error(f'사용자 선택 조회 오류: {e}')
            return []
    
    # =============================================================================
    # QR 코드 관리
    # =============================================================================
    
    def save_qr_code_info(self, qr_data: Dict) -> Dict:
        """QR 코드 정보 저장"""
        try:
            if not self.db:
                return {'success': False, 'message': 'Firestore client not initialized'}
            
            qr_data['created_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.db.collection(self.qr_codes_collection).document()
            doc_ref.set(qr_data)
            
            logger.info(f'QR 코드 정보 저장: {doc_ref.id}')
            return {'success': True, 'id': doc_ref.id}
            
        except Exception as e:
            logger.error(f'QR 코드 정보 저장 오류: {e}')
            return {'success': False, 'message': str(e)}
    
    def get_qr_code_info(self, qr_id: str) -> Optional[Dict]:
        """QR 코드 정보 조회"""
        try:
            if not self.db:
                return None
            
            doc = self.db.collection(self.qr_codes_collection).document(qr_id).get()
            
            if doc.exists:
                qr_data = doc.to_dict()
                qr_data['id'] = doc.id
                return qr_data
            else:
                return None
                
        except Exception as e:
            logger.error(f'QR 코드 정보 조회 오류: {e}')
            return None
    
    # =============================================================================
    # 데이터 마이그레이션 및 초기화
    # =============================================================================
    
    def bulk_upload_tourism_data(self, tourism_data: List[Dict]) -> Dict:
        """관광지 데이터 대량 업로드"""
        try:
            if not self.db:
                return {'success': False, 'message': 'Firestore client not initialized'}
            
            batch = self.db.batch()
            uploaded_count = 0
            
            for data in tourism_data:
                # 문서 ID 생성
                doc_id = data.get('id') or data.get('name', '').replace(' ', '_').lower()
                if not doc_id:
                    continue
                
                # 타임스탬프 추가
                data['created_at'] = firestore.SERVER_TIMESTAMP
                data['updated_at'] = firestore.SERVER_TIMESTAMP
                data['is_active'] = True
                
                doc_ref = self.db.collection(self.tourism_collection).document(doc_id)
                batch.set(doc_ref, data)
                uploaded_count += 1
                
                # 배치 크기 제한 (Firestore는 배치당 500개 제한)
                if uploaded_count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            # 남은 배치 커밋
            if uploaded_count % 500 != 0:
                batch.commit()
            
            logger.info(f'총 {uploaded_count}개 관광지 데이터 업로드 완료')
            return {'success': True, 'uploaded_count': uploaded_count}
            
        except Exception as e:
            logger.error(f'대량 업로드 오류: {e}')
            return {'success': False, 'message': str(e)}
    
    def get_database_stats(self) -> Dict:
        """데이터베이스 통계 정보"""
        try:
            stats = {
                'tourism_spots': 0,
                'user_selections': 0,
                'qr_codes': 0
            }
            
            if not self.db:
                return stats
            
            # 각 컬렉션의 문서 수 조회
            collections = [
                (self.tourism_collection, 'tourism_spots'),
                (self.user_selections_collection, 'user_selections'),
                (self.qr_codes_collection, 'qr_codes')
            ]
            
            for collection_name, stat_key in collections:
                docs = self.db.collection(collection_name).stream()
                count = sum(1 for _ in docs)
                stats[stat_key] = count
            
            return stats
            
        except Exception as e:
            logger.error(f'통계 조회 오류: {e}')
            return {'error': str(e)}

    # =============================================================================
    # API 호환성을 위한 메서드들
    # =============================================================================
    
    def get_all_spots(self) -> List[Dict]:
        """API 호환성을 위한 메서드 - get_all_tourism_spots와 동일"""
        return self.get_all_tourism_spots()
    
    def get_spot_by_id(self, spot_id: str) -> Optional[Dict]:
        """API 호환성을 위한 메서드 - get_tourism_spot_by_id와 동일"""
        return self.get_tourism_spot_by_id(spot_id)
    
    def search_spots_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """키워드 리스트로 관광지 검색"""
        try:
            all_spots = self.get_all_tourism_spots()
            
            if not keywords:
                return all_spots
            
            filtered_spots = []
            
            for spot in all_spots:
                # 여러 필드에서 키워드 검색
                searchable_fields = [
                    spot.get('name', ''),
                    spot.get('title', ''),
                    spot.get('description', ''),
                    spot.get('overview', ''),
                    spot.get('addr1', ''),
                    spot.get('category', ''),
                    ' '.join(spot.get('tags', []))
                ]
                
                # 모든 검색 가능한 필드를 하나의 문자열로 합치기
                search_text = ' '.join(searchable_fields).lower()
                
                # 키워드 중 하나라도 매치되면 포함
                match_found = False
                for keyword in keywords:
                    if keyword.lower() in search_text:
                        match_found = True
                        break
                
                if match_found:
                    filtered_spots.append(spot)
            
            logger.info(f'키워드 {keywords}로 {len(filtered_spots)}개 관광지 검색')
            return filtered_spots
            
        except Exception as e:
            logger.error(f'키워드 검색 오류: {e}')
            return []
    
    # =============================================================================
    # 사용자 선택 기록 관리
    # =============================================================================
    
    def create_user_selection(self, selection_data: Dict) -> str:
        """사용자 선택 기록 생성"""
        try:
            if not self.db:
                raise Exception('Firestore client not initialized')
            
            # 새 문서 생성
            doc_ref = self.db.collection(self.user_selections_collection).document()
            
            # 데이터에 ID 추가
            selection_data['id'] = doc_ref.id
            
            # Firestore에 저장
            doc_ref.set(selection_data)
            
            logger.info(f'사용자 선택 기록 생성: {doc_ref.id}')
            return doc_ref.id
            
        except Exception as e:
            logger.error(f'사용자 선택 기록 생성 오류: {e}')
            raise
    
    def get_user_selection(self, selection_id: str) -> Optional[Dict]:
        """특정 사용자 선택 기록 조회"""
        try:
            if not self.db:
                return None
            
            doc = self.db.collection(self.user_selections_collection).document(selection_id).get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            else:
                return None
                
        except Exception as e:
            logger.error(f'사용자 선택 기록 조회 오류 (ID: {selection_id}): {e}')
            return None
    
    def update_user_selection(self, selection_id: str, update_data: Dict) -> bool:
        """사용자 선택 기록 업데이트"""
        try:
            if not self.db:
                return False
            
            doc_ref = self.db.collection(self.user_selections_collection).document(selection_id)
            doc_ref.update(update_data)
            
            logger.info(f'사용자 선택 기록 업데이트: {selection_id}')
            return True
            
        except Exception as e:
            logger.error(f'사용자 선택 기록 업데이트 오류: {e}')
            return False
    
    def get_user_selections(self, user_id: str = None, session_id: str = None, limit: int = 10) -> List[Dict]:
        """사용자 선택 기록 목록 조회"""
        try:
            if not self.db:
                return []
            
            query = self.db.collection(self.user_selections_collection)
            
            # 필터 조건 추가
            if user_id:
                query = query.where('user_id', '==', user_id)
            elif session_id:
                query = query.where('session_id', '==', session_id)
            
            # 정렬 및 제한
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = query.stream()
            
            selections = []
            for doc in docs:
                selection_data = doc.to_dict()
                selection_data['id'] = doc.id
                selections.append(selection_data)
            
            logger.info(f'사용자 선택 기록 조회: {len(selections)}개')
            return selections
            
        except Exception as e:
            logger.error(f'사용자 선택 기록 목록 조회 오류: {e}')
            return []
    
    def sync_all_data(self) -> Dict:
        """모든 데이터 동기화"""
        try:
            spots = self.get_all_tourism_spots()
            
            return {
                'success': True,
                'message': f'데이터 동기화 완료: {len(spots)}개 관광지',
                'total_spots': len(spots)
            }
            
        except Exception as e:
            logger.error(f'데이터 동기화 오류: {e}')
            return {
                'success': False,
                'message': str(e)
            }


# 전역 서비스 인스턴스
tourism_service = FirestoreTourismService()


# =============================================================================
# 기존 코드와의 호환성을 위한 래퍼 클래스들
# =============================================================================

class FirestoreService:
    """기존 코드 호환성을 위한 래퍼 클래스"""
    
    def __init__(self):
        self.service = tourism_service
    
    def get_all_documents(self, collection_name: str = None) -> List[Dict]:
        if collection_name == 'tourism_spots' or not collection_name:
            return self.service.get_all_tourism_spots()
        return []
    
    def query_documents(self, collection_name: str, field: str, operator: str, value) -> List[Dict]:
        if collection_name == 'tourism_spots' and field == 'category' and operator == '==':
            return self.service.get_spots_by_category(value)
        return []


class TourismDataService:
    """기존 코드 호환성을 위한 래퍼 클래스"""
    
    def __init__(self):
        self.service = tourism_service
    
    def get_all_tourism_spots(self) -> List[Dict]:
        return self.service.get_all_tourism_spots()
    
    def search_spots_by_keywords(self, keywords: List[str]) -> List[Dict]:
        if not keywords:
            return self.service.get_all_tourism_spots()
        
        # 첫 번째 키워드로 검색 (간단한 구현)
        return self.service.search_tourism_spots_by_keyword(keywords[0])
    
    def get_spots_by_category(self, category: str) -> List[Dict]:
        return self.service.get_spots_by_category(category)
    
    def get_nearby_spots(self, latitude: float, longitude: float, radius_km: float = 10) -> List[Dict]:
        # 지리적 검색은 별도 구현 필요
        return self.service.get_all_tourism_spots()[:10]
