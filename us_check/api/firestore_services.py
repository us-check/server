"""
Firestore 기반 관광지 추천 서비스
완전히 Firestore 기반으로 리팩토링된 서비스
"""
import logging
from typing import List, Dict, Optional
from tourism.services import FirestoreTourismService
from gemini_ai.services import GeminiAIService

logger = logging.getLogger(__name__)

class FirestoreTourismRecommendationService:
    """Firestore 기반 관광지 추천 서비스"""
    
    def __init__(self):
        self.tourism_service = FirestoreTourismService()
        self.gemini_service = GeminiAIService()
    
    def get_all_spots(self) -> List[Dict]:
        """모든 관광지 데이터 조회"""
        return self.tourism_service.get_all_tourism_spots()
    
    def get_spots_by_category(self, category: str) -> List[Dict]:
        """카테고리별 관광지 조회"""
        return self.tourism_service.get_spots_by_category(category)
    
    def search_spots_by_keyword(self, keyword: str) -> List[Dict]:
        """키워드로 관광지 검색"""
        return self.tourism_service.search_tourism_spots_by_keyword(keyword)
    
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
            
            # 키워드 매칭 점수
            spot_text = ' '.join([
                spot.get('name', ''),
                spot.get('title', ''),
                spot.get('description', ''),
                spot.get('overview', ''),
                spot.get('addr1', ''),
                spot.get('category', ''),
                ' '.join(spot.get('tags', []))
            ]).lower()
            
            for keyword in keywords:
                if keyword.lower() in spot_text:
                    score += 10
            
            # 카테고리 매칭 점수
            spot_category = spot.get('category', '').lower()
            for category in categories:
                if category.lower() in spot_category:
                    score += 15
            
            # 위치 매칭 점수
            spot_address = spot.get('addr1', '').lower()
            for location in locations:
                if location.lower() in spot_address:
                    score += 20
            
            # 점수가 있는 관광지만 추가
            if score > 0:
                spot['recommendation_score'] = score
                filtered_spots.append(spot)
        
        # 점수순 정렬
        filtered_spots.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)
        
        # 상위 limit개만 반환
        return filtered_spots[:limit]
    
    def save_user_selection(self, user_data: Dict) -> Dict:
        """사용자 선택 저장"""
        return self.tourism_service.save_user_selection(user_data)
    
    def get_user_history(self, user_id: str = None, session_id: str = None) -> List[Dict]:
        """사용자 선택 기록 조회"""
        return self.tourism_service.get_user_selections(user_id, session_id)
    
    def get_database_stats(self) -> Dict:
        """데이터베이스 통계"""
        return self.tourism_service.get_database_stats()


# 전역 서비스 인스턴스 - 기존 코드 호환성
recommendation_service = FirestoreTourismRecommendationService()


# =============================================================================  
# 기존 코드 호환성을 위한 래퍼 클래스
# =============================================================================

class FirestoreTourismService:
    """기존 코드 호환성을 위한 래퍼 클래스"""
    
    def __init__(self):
        self.service = recommendation_service
    
    def get_all_spots(self) -> List[Dict]:
        return self.service.get_all_spots()
    
    def get_spots_by_category(self, category: str) -> List[Dict]:
        return self.service.get_spots_by_category(category)
    
    def search_spots_by_keyword(self, keyword: str) -> List[Dict]:
        return self.service.search_spots_by_keyword(keyword)
    
    def get_recommendations_by_query(self, user_query: str, limit: int = 10) -> Dict:
        return self.service.get_recommendations_by_query(user_query, limit)
    
    def filter_and_rank_spots(self, spots: List[Dict], analysis: Dict, limit: int) -> List[Dict]:
        return self.service.filter_and_rank_spots(spots, analysis, limit)
    
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
