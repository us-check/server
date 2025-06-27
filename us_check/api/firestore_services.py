"""
Firestore 기반 관광지 추천 서비스
Django ORM 대신 Firestore를 직접 사용하는 서비스
"""
import logging
from typing import List, Dict, Optional
from tourism.services import FirestoreService
from gemini_ai.services import GeminiAIService

logger = logging.getLogger(__name__)

class FirestoreTourismService:
    """Firestore 기반 관광지 서비스"""
    
    def __init__(self):
        self.firestore_service = FirestoreService()
        self.gemini_service = GeminiAIService()
        self.collection_name = 'tourism_spots'
    
    def get_all_spots(self) -> List[Dict]:
        """모든 관광지 데이터 조회"""
        return self.firestore_service.get_all_documents(self.collection_name)
    
    def get_spots_by_category(self, category: str) -> List[Dict]:
        """카테고리별 관광지 조회"""
        return self.firestore_service.query_documents(
            self.collection_name, 'category', '==', category
        )
    
    def search_spots_by_keyword(self, keyword: str) -> List[Dict]:
        """키워드로 관광지 검색 (제목 기반)"""
        spots = self.get_all_spots()
        
        # 클라이언트 측 필터링 (Firestore의 제한된 텍스트 검색 보완)
        filtered_spots = []
        keyword_lower = keyword.lower()
        
        for spot in spots:
            title = spot.get('title', '').lower()
            addr1 = spot.get('addr1', '').lower()
            overview = spot.get('overview', '').lower()
            category = spot.get('category', '').lower()
            
            if (keyword_lower in title or 
                keyword_lower in addr1 or 
                keyword_lower in overview or 
                keyword_lower in category):
                filtered_spots.append(spot)
        
        return filtered_spots
    
    def get_recommendations_by_query(self, user_query: str, limit: int = 10) -> Dict:
        """자연어 쿼리 기반 관광지 추천"""
        try:
            # 1. Gemini AI로 쿼리 분석
            analysis_result = self.gemini_service.analyze_tourism_query(user_query)
            
            if not analysis_result.get('success'):
                return {
                    'success': False,
                    'message': '쿼리 분석 실패',
                    'recommendations': []
                }
            
            analysis = analysis_result.get('analysis', {})
            logger.info(f'쿼리 분석 결과: {analysis}')
            
            # 2. 모든 관광지 데이터 가져오기
            all_spots = self.get_all_spots()
            
            # 3. 분석 결과에 따라 필터링 및 추천
            recommendations = self.filter_and_rank_spots(all_spots, analysis, limit)
            
            return {
                'success': True,
                'query': user_query,
                'analysis': analysis,
                'recommendations': recommendations,
                'total_count': len(recommendations)
            }
            
        except Exception as e:
            logger.error(f'추천 생성 오류: {e}')
            return {
                'success': False,
                'message': str(e),
                'recommendations': []
            }
    
    def filter_and_rank_spots(self, spots: List[Dict], analysis: Dict, limit: int) -> List[Dict]:
        """분석 결과에 따라 관광지 필터링 및 랭킹"""
        filtered_spots = []
        
        # 추출된 키워드들
        keywords = analysis.get('keywords', [])
        categories = analysis.get('categories', [])
        locations = analysis.get('locations', [])
        
        for spot in spots:
            score = 0
            
            # 카테고리 매칭
            spot_category = spot.get('category', '')
            if categories:
                for category in categories:
                    if category.lower() in spot_category.lower():
                        score += 3
            
            # 키워드 매칭
            title = spot.get('title', '').lower()
            overview = spot.get('overview', '').lower()
            addr1 = spot.get('addr1', '').lower()
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in title:
                    score += 2
                elif keyword_lower in overview:
                    score += 1
                elif keyword_lower in addr1:
                    score += 1
            
            # 위치 매칭
            for location in locations:
                location_lower = location.lower()
                if location_lower in addr1:
                    score += 2
            
            # 기본적으로 모든 관광지에 최소 점수 부여
            if score == 0:
                score = 0.1
            
            spot_with_score = spot.copy()
            spot_with_score['relevance_score'] = score
            filtered_spots.append(spot_with_score)
        
        # 점수에 따라 정렬
        filtered_spots.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # 상위 N개 반환
        return filtered_spots[:limit]
    
    def get_spot_by_id(self, spot_id: str) -> Optional[Dict]:
        """ID로 특정 관광지 조회"""
        try:
            doc_ref = self.firestore_service.db.collection(self.collection_name).document(spot_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            else:
                return None
                
        except Exception as e:
            logger.error(f'관광지 조회 오류: {e}')
            return None
    
    def save_user_selection(self, user_query: str, selected_spots: List[str], session_id: str = None) -> Dict:
        """사용자 선택 저장 (Firestore)"""
        try:
            from datetime import datetime
            
            selection_data = {
                'user_query': user_query,
                'selected_spot_ids': selected_spots,
                'selected_at': datetime.now(),
                'session_id': session_id,
                'source': 'firestore_api'
            }
            
            result = self.firestore_service.add_document('user_selections', selection_data)
            
            if result.get('success'):
                return {
                    'success': True,
                    'selection_id': result.get('doc_id'),
                    'message': '선택 내역이 저장되었습니다.'
                }
            else:
                return {
                    'success': False,
                    'message': result.get('message', '저장에 실패했습니다.')
                }
                
        except Exception as e:
            logger.error(f'사용자 선택 저장 오류: {e}')
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_user_history(self, session_id: str = None, limit: int = 10) -> List[Dict]:
        """사용자 히스토리 조회"""
        try:
            if session_id:
                # 특정 세션의 히스토리
                selections = self.firestore_service.query_documents(
                    'user_selections', 'session_id', '==', session_id
                )
            else:
                # 전체 히스토리 (최근순)
                selections = self.firestore_service.get_all_documents('user_selections')
            
            # 최신순 정렬 (클라이언트 측)
            selections.sort(key=lambda x: x.get('selected_at', ''), reverse=True)
            
            return selections[:limit]
            
        except Exception as e:
            logger.error(f'사용자 히스토리 조회 오류: {e}')
            return []
    
    def get_popular_spots(self, limit: int = 10) -> List[Dict]:
        """인기 관광지 조회 (조회수 기준)"""
        spots = self.get_all_spots()
        
        # readcount 기준으로 정렬
        spots.sort(key=lambda x: int(x.get('readcount', 0)), reverse=True)
        
        return spots[:limit]
    
    def get_spots_with_images(self, limit: int = 20) -> List[Dict]:
        """이미지가 있는 관광지 조회"""
        spots = self.get_all_spots()
        
        # 이미지가 있는 관광지만 필터링
        spots_with_images = [
            spot for spot in spots 
            if spot.get('firstimage') and spot.get('firstimage').strip()
        ]
        
        return spots_with_images[:limit]
    
    def get_statistics(self) -> Dict:
        """관광지 데이터 통계"""
        spots = self.get_all_spots()
        
        # 카테고리별 개수
        category_counts = {}
        for spot in spots:
            category = spot.get('category', '기타')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 이미지 유무별 개수
        with_images = len([s for s in spots if s.get('firstimage')])
        without_images = len(spots) - with_images
        
        return {
            'total_spots': len(spots),
            'category_distribution': category_counts,
            'images': {
                'with_images': with_images,
                'without_images': without_images
            },
            'collection_name': self.collection_name
        }
