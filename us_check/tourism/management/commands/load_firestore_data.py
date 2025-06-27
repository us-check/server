"""
텍스트 파일에서 의성군 관광지 데이터를 Firestore에 직접 로드하는 명령어
JSON 형식 데이터를 Firestore 컬렉션에 저장
"""
import os
import json
from django.core.management.base import BaseCommand
from tourism.services import FirestoreService

class Command(BaseCommand):
    help = '텍스트 파일에서 의성군 관광지 데이터를 Firestore에 로드합니다'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--txt-file',
            type=str,
            required=True,
            help='관광지 데이터 텍스트 파일 경로',
        )
        parser.add_argument(
            '--encoding',
            type=str,
            default='utf-8',
            help='파일 인코딩 (기본값: utf-8)',
        )
        parser.add_argument(
            '--collection',
            type=str,
            default='tourism_spots',
            help='Firestore 컬렉션 이름 (기본값: tourism_spots)',
        )
        parser.add_argument(
            '--clear-collection',
            action='store_true',
            help='기존 컬렉션 데이터를 삭제하고 새로 로드',
        )
    
    def handle(self, *args, **options):
        txt_file_path = options['txt_file']
        encoding = options['encoding']
        collection_name = options['collection']
        clear_collection = options['clear_collection']
        
        if not os.path.exists(txt_file_path):
            self.stdout.write(
                self.style.ERROR(f'파일을 찾을 수 없습니다: {txt_file_path}')
            )
            return
        
        # Firestore 서비스 초기화
        firestore_service = FirestoreService()
        
        # 기존 컬렉션 삭제 (옵션)
        if clear_collection:
            self.stdout.write(f'기존 컬렉션 "{collection_name}" 삭제 중...')
            try:
                firestore_service.clear_collection(collection_name)
                self.stdout.write(self.style.SUCCESS('컬렉션 삭제 완료'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'컬렉션 삭제 실패: {e}'))
        
        self.load_to_firestore(txt_file_path, encoding, collection_name, firestore_service)
    
    def load_to_firestore(self, txt_file_path, encoding, collection_name, firestore_service):
        """텍스트 파일에서 관광지 데이터를 Firestore에 로드"""
        try:
            with open(txt_file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            self.stdout.write(f'파일 읽기 완료: {txt_file_path}')
            self.stdout.write(f'파일 크기: {len(content)} 문자')
            
            # JSON 파싱
            tourism_data = self.parse_json_content(content)
            
            if not tourism_data:
                self.stdout.write(
                    self.style.WARNING('파싱된 데이터가 없습니다. 파일 형식을 확인해주세요.')
                )
                return
            
            self.stdout.write(f'파싱된 데이터 개수: {len(tourism_data)}개')
            
            # Firestore에 배치 저장
            created_count = 0
            error_count = 0
            
            for item in tourism_data:
                try:
                    # 문서 ID는 contentid를 사용하거나 자동 생성
                    doc_id = item.get('contentid') or None
                    
                    # Firestore 문서 구조 생성
                    firestore_doc = self.create_firestore_document(item)
                    
                    # Firestore에 저장
                    firestore_service.add_document(collection_name, firestore_doc, doc_id)
                    
                    created_count += 1
                    self.stdout.write(f'저장: {item.get("title", "Unknown")} (ID: {doc_id or "auto"})')
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'저장 오류: {item.get("title", "Unknown")} - {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Firestore 데이터 로드 완료!\n'
                    f'- 저장: {created_count}개\n'
                    f'- 오류: {error_count}개\n'
                    f'- 컬렉션: {collection_name}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'파일 처리 중 오류 발생: {e}')
            )
    
    def parse_json_content(self, content):
        """JSON 형식 파싱"""
        try:
            json_data = json.loads(content)
            
            # 한국관광공사 API 형식 확인
            if self.is_korea_tourism_api_format(json_data):
                return json_data['response']['body']['items']['item']
            else:
                # 단순 JSON 배열인 경우
                if isinstance(json_data, list):
                    return json_data
                else:
                    return [json_data]
                    
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'JSON 파싱 오류: {e}'))
            return []
    
    def is_korea_tourism_api_format(self, json_data):
        """한국관광공사 API 형식인지 확인"""
        return (
            isinstance(json_data, dict) and
            'response' in json_data and
            'body' in json_data['response'] and
            'items' in json_data['response']['body'] and
            'item' in json_data['response']['body']['items']
        )
    
    def create_firestore_document(self, item):
        """Firestore 문서 구조 생성"""
        # 기본 필드들
        doc = {
            'contentid': item.get('contentid', ''),
            'title': item.get('title', '').strip(),
            'addr1': item.get('addr1', '').strip(),
            'addr2': item.get('addr2', '').strip(),
            'zipcode': item.get('zipcode', ''),
            'tel': item.get('tel', '').strip(),
            'homepage': item.get('homepage', '').strip(),
            'overview': item.get('overview', '').strip(),
            'firstimage': item.get('firstimage', ''),
            'firstimage2': item.get('firstimage2', ''),
            'mapx': item.get('mapx', ''),
            'mapy': item.get('mapy', ''),
            'mlevel': item.get('mlevel', ''),
            'readcount': item.get('readcount', 0),
            'sigungucode': item.get('sigungucode', ''),
            'areacode': item.get('areacode', ''),
            'cat1': item.get('cat1', ''),
            'cat2': item.get('cat2', ''),
            'cat3': item.get('cat3', ''),
            'contenttypeid': item.get('contenttypeid', ''),
            'createdtime': item.get('createdtime', ''),
            'modifiedtime': item.get('modifiedtime', ''),
            'booktour': item.get('booktour', ''),
        }
        
        # 좌표 변환
        try:
            if item.get('mapy'):
                doc['latitude'] = float(item['mapy'])
            if item.get('mapx'):
                doc['longitude'] = float(item['mapx'])
        except (ValueError, TypeError):
            doc['latitude'] = None
            doc['longitude'] = None
        
        # 카테고리 매핑
        doc['category'] = self.map_category_code(
            item.get('cat1', ''), 
            item.get('cat2', ''), 
            item.get('cat3', '')
        )
        
        # 태그 생성
        tags = []
        if item.get('firstimage'):
            tags.append('사진있음')
        if item.get('tel'):
            tags.append('연락처있음')
        if item.get('homepage'):
            tags.append('홈페이지있음')
        doc['tags'] = tags
        
        # 메타데이터 추가
        from datetime import datetime
        doc['loaded_at'] = datetime.now()
        doc['source'] = 'us_tourdata.txt'
        
        # 원본 데이터 보존
        doc['raw_data'] = item
        
        return doc
    
    def map_category_code(self, cat1, cat2, cat3):
        """한국관광공사 카테고리 코드를 우리 카테고리로 매핑"""
        category_map = {
            'A01': '자연관광지',
            'A02': '문화재/유적지', 
            'A03': '레저/스포츠',
            'A04': '쇼핑',
            'A05': '음식/맛집',
            'B02': '숙박시설',
            'C01': '축제/이벤트',
        }
        
        # 더 세부적인 매핑
        detailed_map = {
            'A0101': '자연관광지',  # 자연관광지
            'A0201': '문화재/유적지',  # 역사관광지
            'A0202': '체험관광지',  # 휴양관광지
            'A0203': '체험관광지',  # 체험관광지
            'A0206': '문화재/유적지',  # 문화시설
            'A0207': '축제/이벤트',  # 축제
            'A0208': '레저/스포츠',  # 공연/행사
            'B0201': '숙박시설',  # 숙박시설
        }
        
        # 가장 구체적인 카테고리부터 확인
        if cat2 in detailed_map:
            return detailed_map[cat2]
        elif cat1 in category_map:
            return category_map[cat1]
        else:
            return '일반'
