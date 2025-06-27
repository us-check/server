"""
Gemini AI 서비스 - 자연어 처리 및 관광지 추천
"""
import logging
import json
from typing import List, Dict, Optional
from django.conf import settings
import google.generativeai as genai
# Django 모델 제거 - Firestore 기반으로 전환
# from tourism.models import TourismSpot
# from tourism.services import TourismDataService

logger = logging.getLogger(__name__)

class GeminiAIService:
    """Gemini AI를 이용한 자연어 처리 서비스"""
    
    def __init__(self):
        try:
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                
                # System instruction 설정
                system_instruction = """
                당신은 경상북도 의성군 관광지 추천 전문 AI입니다.
                
                주요 역할:
                1. 사용자의 자연어 쿼리를 분석하여 적절한 관광지를 추천
                2. 의성군의 특색과 문화를 반영한 추천 제공
                3. 정확하고 유용한 관광 정보 제공
                
                의성군 주요 특징:
                - 마늘과 양파의 고장으로 유명
                - 조문국 유적지와 역사 문화재 보유
                - 빙계계곡, 사촌역 은행나무 등 자연 관광지
                - 전통과 현대가 조화된 관광 도시
                
                응답 원칙:
                - 항상 JSON 형식으로 구조화된 데이터 제공
                - JSON 입력의 key 순서는 절대 바꾸지 않습니다
                - 음식점, 숙박, 관광지는 각각 최소 5개 이상 추천

                """
                
                self.model = genai.GenerativeModel(
                    'gemini-2.5-flash',
                    system_instruction=system_instruction
                )
                logger.info("Gemini AI initialized successfully with gemini-2.5-flash and system instruction")
            else:
                logger.error("GEMINI_API_KEY not found in settings")
                self.model = None
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self.model = None
        
        # Django 모델 제거 - Firestore 직접 사용
        # self.tourism_service = TourismDataService()
    
    def analyze_user_query(self, user_query: str) -> Dict:
        """사용자 쿼리를 분석하여 관광지 검색 조건 추출"""
        try:
            # Gemini AI 상태 상세 로깅
            logger.info(f"=== Gemini AI 상태 확인 ===")
            logger.info(f"self.model 존재: {self.model is not None}")
            logger.info(f"GEMINI_API_KEY 설정: {bool(getattr(settings, 'GEMINI_API_KEY', None))}")
            
            if not self.model:
                logger.warning("⚠️ Gemini AI not available, using fallback analysis")
                logger.warning("Gemini AI를 사용할 수 없어 폴백 분석을 사용합니다")
                return self._fallback_analysis(user_query)
            
            logger.info("✅ Gemini AI 사용 가능 - 실제 AI 분석 시작")
            
            # 의성군 관광지 정보를 기반으로 한 프롬프트 생성
            prompt = self._create_analysis_prompt(user_query)
            logger.info(f"Generated prompt length: {len(prompt)}")
            
            logger.info("🤖 Gemini AI 호출 중...")
            response = self.model.generate_content(prompt)
            logger.info(f"✅ Gemini AI 응답 받음: {response.text[:100]}...")
            
            # 응답 파싱
            analysis_result = self._parse_analysis_response(response.text)
            
            logger.info(f"Query analysis completed for: {user_query}")
            logger.info(f"Analysis result: {analysis_result}")
            
            return {
                'success': True,
                'original_query': user_query,
                'analysis': analysis_result,
                'processed_query': analysis_result.get('processed_query', user_query),
                'gemini_used': True  # Gemini가 실제로 사용되었음을 표시
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing user query with Gemini: {e}")
            import traceback
            logger.error(f"Gemini 오류 상세: {traceback.format_exc()}")
            # Gemini 실패 시 폴백 분석 사용
            logger.warning("Gemini 실패로 폴백 분석 사용")
            return self._fallback_analysis(user_query)
    
    def _fallback_analysis(self, user_query: str) -> Dict:
        """Gemini AI를 사용할 수 없을 때의 폴백 분석"""
        logger.info("🔄 폴백 분석 시작 (Gemini AI 미사용)")
        
        # 간단한 키워드 기반 분석
        keywords = []
        categories = []
        
        # 자연 관련 키워드
        nature_keywords = ['자연', '경관', '산', '계곡', '강', '호수', '나무', '숲', '풍경']
        cultural_keywords = ['문화', '역사', '유적', '박물관', '전통', '고택', '사찰', '절']
        experience_keywords = ['체험', '활동', '놀이', '축제', '이벤트']
        
        query_lower = user_query.lower()
        
        for keyword in nature_keywords:
            if keyword in user_query:
                keywords.append(keyword)
                if '자연관광지' not in categories:
                    categories.append('자연관광지')
        
        for keyword in cultural_keywords:
            if keyword in user_query:
                keywords.append(keyword)
                if '문화재/유적지' not in categories:
                    categories.append('문화재/유적지')
        
        for keyword in experience_keywords:
            if keyword in user_query:
                keywords.append(keyword)
                if '체험관광지' not in categories:
                    categories.append('체험관광지')
        
        # 기본값 설정
        if not keywords:
            keywords = ['관광', '여행']
        if not categories:
            categories = ['일반']
        
        logger.info(f"폴백 분석 결과 - 키워드: {keywords}, 카테고리: {categories}")
        
        analysis_result = {
            'keywords': keywords,
            'categories': categories,
            'preferences': [],
            'intent': 'general_search',
            'processed_query': user_query,
            'confidence': 0.7,
            'fallback': True
        }
        
        return {
            'success': True,
            'original_query': user_query,
            'analysis': analysis_result,
            'processed_query': user_query,
            'gemini_used': False  # Gemini가 사용되지 않았음을 표시
        }
    
    def recommend_tourism_spots(self, user_query: str, max_results: int = 30) -> Dict:
        """사용자 쿼리를 기반으로 관광지 추천"""
        try:
            # 1. 쿼리 분석
            analysis_result = self.analyze_user_query(user_query)
            
            if not analysis_result['success']:
                return analysis_result
            
            analysis = analysis_result['analysis']
            
            # 2. 관광지 검색
            recommended_spots = []
            
            # 키워드 기반 검색
            if analysis.get('keywords'):
                spots = self.tourism_service.search_spots_by_keywords(analysis['keywords'])
                recommended_spots.extend(spots)
            
            # 카테고리 기반 검색
            if analysis.get('categories'):
                for category in analysis['categories']:
                    spots = self.tourism_service.get_spots_by_category(category)
                    recommended_spots.extend(spots)
            
            # 중복 제거
            unique_spots = list({spot.id: spot for spot in recommended_spots}.values())
            
            # 3. AI 기반 재순위 매기기
            if unique_spots and len(unique_spots) > max_results:
                ranked_spots = self._rank_spots_with_ai(user_query, unique_spots, max_results)
            else:
                ranked_spots = unique_spots[:max_results]
            
            # 4. 결과 포맷팅
            result_data = []
            for spot in ranked_spots:
                result_data.append(spot.to_dict())
            
            return {
                'success': True,
                'query': user_query,
                'analysis': analysis,
                'recommended_spots': result_data,
                'total_found': len(unique_spots),
                'returned_count': len(result_data)
            }
            
        except Exception as e:
            logger.error(f"Error recommending tourism spots: {e}")
            return {'success': False, 'message': str(e)}
    
    def _create_analysis_prompt(self, user_query: str) -> str:
        """사용자 쿼리 분석을 위한 프롬프트 생성"""
        return f"""
        의성군 관광지 추천 시스템입니다. 사용자의 자연어 쿼리를 분석해주세요.

        사용자 쿼리: "{user_query}"

        다음 정보를 추출하여 JSON 형태로 반환해주세요:
        {{
            "keywords": ["추출된 키워드들"],
            "categories": ["관광지 카테고리들"],
            "preferences": ["사용자 선호사항들"],
            "intent": "사용자 의도",
            "processed_query": "정제된 검색 쿼리",
            "confidence": 0.0-1.0
        }}

        가능한 카테고리:
        - 문화재/유적지
        - 자연관광지
        - 체험관광지
        - 축제/이벤트
        - 음식/맛집
        - 숙박시설
        - 레저/스포츠

        의성군의 특색:
        - 마늘과 양파의 고장
        - 조문국 유적지
        - 빙계계곡
        - 사촌역 은행나무
        - 의성 조문국사적지
        """
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """AI 응답을 파싱하여 구조화된 데이터로 변환"""
        try:
            # JSON 부분 추출
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # JSON 형태가 아닌 경우 기본값 반환
                return {
                    'keywords': [response_text.strip()],
                    'categories': [],
                    'preferences': [],
                    'intent': 'general_search',
                    'processed_query': response_text.strip(),
                    'confidence': 0.5
                }
                
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse AI response as JSON: {response_text}")
            return {
                'keywords': [],
                'categories': [],
                'preferences': [],
                'intent': 'unknown',
                'processed_query': response_text.strip(),
                'confidence': 0.3
            }
    
    def _rank_spots_with_ai(self, user_query: str, spots: List[Dict], max_results: int) -> List[Dict]:
        """AI를 이용하여 관광지 순위 매기기"""
        try:
            if not self.model:
                return spots[:max_results]
            
            # 관광지 정보를 텍스트로 변환
            spots_info = []
            for i, spot in enumerate(spots):
                spots_info.append(f"{i}: {spot.get('title', '')} - {spot.get('overview', '')} ({spot.get('category', '')})")
            
            prompt = f"""
            사용자 쿼리: "{user_query}"
            
            다음 관광지들 중에서 사용자 쿼리에 가장 적합한 순서로 {max_results}개를 선택해주세요:
            
            {chr(10).join(spots_info)}
            
            선택된 관광지의 인덱스를 쉼표로 구분하여 반환해주세요 (예: 0,3,7,12,5):
            """
            
            response = self.model.generate_content(prompt)
            indices_str = response.text.strip()
            
            # 인덱스 파싱
            try:
                indices = [int(idx.strip()) for idx in indices_str.split(',')]
                ranked_spots = [spots[i] for i in indices if 0 <= i < len(spots)]
                return ranked_spots[:max_results]
            except (ValueError, IndexError):
                logger.warning(f"Failed to parse ranking indices: {indices_str}")
                return spots[:max_results]
                
        except Exception as e:
            logger.error(f"Error ranking spots with AI: {e}")
            return spots[:max_results]
    
    def generate_tourism_description(self, spots: List[Dict]) -> str:
        """선택된 관광지들에 대한 종합 설명 생성"""
        try:
            if not self.model or not spots:
                return ""
            
            spots_info = []
            for spot in spots:
                spots_info.append(f"- {spot.get('name', '')}: {spot.get('description', '')}")
            
            prompt = f"""
            다음 의성군 관광지들에 대한 매력적인 여행 설명을 작성해주세요:
            
            {chr(10).join(spots_info)}
            
            요구사항:
            1. 각 관광지의 특색을 살린 설명
            2. 의성군의 지역 특색 포함
            3. 방문객들이 흥미를 느낄 수 있는 내용
            4. 200-300자 내외
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating tourism description: {e}")
            return ""
    
    def recommend_tourism_spots(self, user_query: str, all_spots: List[Dict]) -> Dict:
        """사용자 쿼리를 기반으로 관광지 추천"""
        try:
            # 1. 사용자 쿼리 분석
            analysis_result = self.analyze_user_query(user_query)
            
            if not analysis_result.get('success'):
                return {
                    'success': False,
                    'message': '쿼리 분석 실패',
                    'analysis': {},
                    'recommended_spots': []
                }
            
            analysis = analysis_result.get('analysis', {})
            
            # 2. 관광지 필터링 및 순위 매기기
            recommended_spots = self._rank_spots_with_ai(user_query, all_spots, 20)
            
            # 3. 데이터 정리 (중복 필드 제거)
            cleaned_spots = [self._clean_spot_data(spot) for spot in recommended_spots[:15]]
            
            return {
                'success': True,
                'analysis': analysis,
                'recommended_spots': cleaned_spots,
                'total_analyzed': len(all_spots)
            }
            
        except Exception as e:
            logger.error(f"Error in recommend_tourism_spots: {e}")
            return {
                'success': False,
                'message': str(e),
                'analysis': {},
                'recommended_spots': []
            }
    
    def _clean_spot_data(self, spot: Dict) -> Dict:
        """관광지 데이터에서 중복 필드 제거 및 정리"""
        # 필요한 필드만 선택하여 깔끔한 응답 생성
        cleaned_spot = {
            'id': spot.get('id', spot.get('contentid', '')),
            'title': spot.get('title', ''),
            'category': spot.get('category', ''),
            'addr1': spot.get('addr1', ''),
            'addr2': spot.get('addr2', ''),
            'overview': spot.get('overview', ''),
            'tel': spot.get('tel', ''),
            'homepage': spot.get('homepage', ''),
            'firstimage': spot.get('firstimage', ''),
            'firstimage2': spot.get('firstimage2', ''),
            'latitude': spot.get('latitude', spot.get('mapy', '')),
            'longitude': spot.get('longitude', spot.get('mapx', '')),
            'contentid': spot.get('contentid', ''),
            'contenttypeid': spot.get('contenttypeid', ''),
            'areacode': spot.get('areacode', ''),
            'sigungucode': spot.get('sigungucode', ''),
            'booktour': spot.get('booktour', ''),
            'tags': spot.get('tags', [])
        }
        
        # 빈 값 제거
        return {k: v for k, v in cleaned_spot.items() if v is not None and v != ''}
