"""
텍스트 파일에서 의성군 관광지 데이터를 로드하는 명령어
JSON 형식과 일반 텍스트 형식 모두 지원
"""
import os
import re
import json
from django.core.management.base import BaseCommand
from tourism.models import TourismSpot

class Command(BaseCommand):
    help = '텍스트 파일에서 의성군 관광지 데이터를 로드합니다'
    
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
    
    def handle(self, *args, **options):
        txt_file_path = options['txt_file']
        encoding = options['encoding']
        
        if not os.path.exists(txt_file_path):
            self.stdout.write(
                self.style.ERROR(f'파일을 찾을 수 없습니다: {txt_file_path}')
            )
            return
        
        self.load_from_txt(txt_file_path, encoding)
    
    def load_from_txt(self, txt_file_path, encoding):
        """텍스트 파일에서 관광지 데이터 로드"""
        try:
            with open(txt_file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            self.stdout.write(f'파일 읽기 완료: {txt_file_path}')
            self.stdout.write(f'파일 크기: {len(content)} 문자')
            
            # 파일 내용 형식을 분석하여 데이터 파싱
            # 사용자가 제공하는 파일 형식에 따라 수정 필요
            tourism_data = self.parse_txt_content(content)
            
            if not tourism_data:
                self.stdout.write(
                    self.style.WARNING('파싱된 데이터가 없습니다. 파일 형식을 확인해주세요.')
                )
                return
            
            self.stdout.write(f'파싱된 데이터 개수: {len(tourism_data)}개')
            
            # 데이터베이스에 저장
            created_count = 0
            updated_count = 0
            error_count = 0
            
            for item in tourism_data:
                try:
                    tourism_spot, created = TourismSpot.objects.update_or_create(
                        name=item.get('name', '').strip(),
                        defaults={
                            'description': item.get('description', '').strip(),
                            'address': item.get('address', '').strip(),
                            'latitude': item.get('latitude'),
                            'longitude': item.get('longitude'),
                            'category': item.get('category', '').strip(),
                            'tags': item.get('tags', []),
                            'contact_info': item.get('contact_info', '').strip(),
                            'website': item.get('website', '').strip(),
                            'opening_hours': item.get('opening_hours', '').strip(),
                            'raw_data': item,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'생성: {item.get("name", "Unknown")}')
                    else:
                        updated_count += 1
                        self.stdout.write(f'업데이트: {item.get("name", "Unknown")}')
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'저장 오류: {item.get("name", "Unknown")} - {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'데이터 로드 완료!\n'
                    f'- 생성: {created_count}개\n'
                    f'- 업데이트: {updated_count}개\n'
                    f'- 오류: {error_count}개'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'파일 처리 중 오류 발생: {e}')
            )
    
    def parse_txt_content(self, content):
        """
        텍스트 파일 내용을 파싱하여 관광지 데이터 추출
        
        지원 형식:
        1. JSON 형식 (한국관광공사 API 응답)
        2. 파이프(|) 구분자 형식
        3. 단순 텍스트 목록
        """
        tourism_data = []
        
        # JSON 형식 파싱 시도
        try:
            json_data = json.loads(content)
            if self.is_korea_tourism_api_format(json_data):
                return self.parse_korea_tourism_api(json_data)
        except json.JSONDecodeError:
            pass  # JSON이 아니면 다른 형식으로 파싱
        
        # 일반 텍스트 형식 파싱
        return self.parse_plain_text(content)
    
    def is_korea_tourism_api_format(self, json_data):
        """한국관광공사 API 형식인지 확인"""
        return (
            isinstance(json_data, dict) and
            'response' in json_data and
            'body' in json_data['response'] and
            'items' in json_data['response']['body'] and
            'item' in json_data['response']['body']['items']
        )
    
    def parse_korea_tourism_api(self, json_data):
        """한국관광공사 API 응답 형식 파싱"""
        tourism_data = []
        
        try:
            items = json_data['response']['body']['items']['item']
            
            for item in items:
                # 카테고리 매핑
                category = self.map_category_code(item.get('cat1', ''), item.get('cat2', ''), item.get('cat3', ''))
                
                # 좌표 변환
                latitude = None
                longitude = None
                try:
                    if item.get('mapy'):
                        latitude = float(item['mapy'])
                    if item.get('mapx'):
                        longitude = float(item['mapx'])
                except (ValueError, TypeError):
                    pass
                
                # 태그 생성
                tags = []
                if item.get('firstimage'):
                    tags.append('사진있음')
                if item.get('tel'):
                    tags.append('연락처있음')
                
                tourism_spot = {
                    'name': item.get('title', '').strip(),
                    'description': '',  # API에서 상세 설명은 별도 호출 필요
                    'address': item.get('addr1', '').strip(),
                    'latitude': latitude,
                    'longitude': longitude,
                    'category': category,
                    'tags': tags,
                    'contact_info': item.get('tel', '').strip(),
                    'website': '',
                    'opening_hours': '',
                    'raw_data': item,  # 원본 API 데이터 보존
                }
                
                tourism_data.append(tourism_spot)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'JSON 파싱 중 오류 발생: {e}')
            )
        
        return tourism_data
    
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
    
    def parse_plain_text(self, content):
        """일반 텍스트 형식 파싱 (기존 로직)"""
        tourism_data = []
        lines = content.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 파이프 구분자로 분리 시도
            if '|' in line:
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 2:
                    item = {
                        'name': parts[0] if len(parts) > 0 else '',
                        'address': parts[1] if len(parts) > 1 else '',
                        'category': parts[2] if len(parts) > 2 else '일반',
                        'description': parts[3] if len(parts) > 3 else '',
                        'contact_info': parts[4] if len(parts) > 4 else '',
                        'website': parts[5] if len(parts) > 5 else '',
                        'opening_hours': parts[6] if len(parts) > 6 else '',
                        'tags': [],
                        'latitude': None,
                        'longitude': None,
                        'raw_data': {'source': 'text_file', 'line': line_num}
                    }
                    tourism_data.append(item)
                    continue
            
            # 단순 텍스트 줄 단위로 관광지명만 추출
            if line and len(line) > 1:
                item = {
                    'name': line,
                    'address': '',
                    'category': '일반',
                    'description': '',
                    'contact_info': '',
                    'website': '',
                    'opening_hours': '',
                    'tags': [],
                    'latitude': None,
                    'longitude': None,
                    'raw_data': {'source': 'text_file', 'line': line_num}
                }
                tourism_data.append(item)
        
        return tourism_data
    
    def display_sample_data(self, tourism_data, count=5):
        """샘플 데이터 출력"""
        self.stdout.write(f'\n=== 처음 {count}개 데이터 미리보기 ===')
        for i, item in enumerate(tourism_data[:count]):
            self.stdout.write(f'{i+1}. {item["name"]} - {item["category"]} ({item["address"]})')
