#!/usr/bin/env python3
"""
us_tourdata.txt 파일의 데이터를 Firestore에 로드하는 스크립트
"""
import os
import sys
import json
import django
from datetime import datetime

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'us_check.settings')
django.setup()

from django.conf import settings

def load_data_to_firestore():
    """us_tourdata.txt 데이터를 Firestore에 로드"""
    try:
        # Firestore 클라이언트 가져오기
        db = getattr(settings, 'FIRESTORE_CLIENT', None)
        
        if not db:
            print("❌ Firestore 클라이언트가 초기화되지 않았습니다.")
            return
        
        # us_tourdata.txt 파일 읽기
        txt_file_path = 'us_tourdata.txt'
        
        if not os.path.exists(txt_file_path):
            print(f"❌ 파일을 찾을 수 없습니다: {txt_file_path}")
            return
        
        print(f"📖 파일 읽기 시작: {txt_file_path}")
        
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 데이터 구조 확인
        items = data['response']['body']['items']['item']
        total_count = len(items)
        
        print(f"📊 총 {total_count}개 항목 발견")
        print(f"🎯 Firestore 컬렉션: tourism_spots")
        print(f"📋 프로젝트: {settings.FIRESTORE_PROJECT_ID}")
        print(f"📋 데이터베이스: {settings.FIRESTORE_DATABASE_ID}")
        
        # Firestore 컬렉션 참조
        collection_ref = db.collection('tourism_spots')
        
        # 기존 데이터 삭제 확인
        existing_docs = list(collection_ref.stream())
        if existing_docs:
            print(f"⚠️  기존 {len(existing_docs)}개 문서가 존재합니다.")
            response = input("기존 데이터를 모두 삭제하고 새로 로드하시겠습니까? (y/N): ")
            if response.lower() == 'y':
                print("🗑️  기존 데이터 삭제 중...")
                for doc in existing_docs:
                    doc.reference.delete()
                print("✅ 기존 데이터 삭제 완료")
            else:
                print("❌ 작업이 취소되었습니다.")
                return
        
        # 데이터 로드
        success_count = 0
        error_count = 0
        
        for i, item in enumerate(items, 1):
            try:
                # contentid를 문서 ID로 사용
                doc_id = item.get('contentid', f'item_{i}')
                
                # 카테고리 매핑
                category = get_category_name(item.get('contenttypeid', ''))
                
                # 좌표 변환
                latitude = float(item.get('mapy', 0)) if item.get('mapy') else None
                longitude = float(item.get('mapx', 0)) if item.get('mapx') else None
                
                # 태그 생성
                tags = []
                if item.get('tel'):
                    tags.append('연락처있음')
                if item.get('firstimage'):
                    tags.append('이미지있음')
                if item.get('homepage'):
                    tags.append('홈페이지있음')
                
                # Firestore 문서 데이터 구성
                doc_data = {
                    # 기본 정보
                    'title': item.get('title', '').strip(),
                    'category': category,
                    'addr1': item.get('addr1', '').strip(),
                    'addr2': item.get('addr2', '').strip(),
                    'overview': item.get('overview', '').strip(),
                    
                    # 연락처 및 웹사이트
                    'tel': item.get('tel', '').strip(),
                    'homepage': item.get('homepage', '').strip(),
                    
                    # 이미지
                    'firstimage': item.get('firstimage', '').strip(),
                    'firstimage2': item.get('firstimage2', '').strip(),
                    
                    # 위치 정보
                    'latitude': latitude,
                    'longitude': longitude,
                    'mapx': item.get('mapx', '').strip(),
                    'mapy': item.get('mapy', '').strip(),
                    
                    # 분류 정보
                    'contentid': item.get('contentid', '').strip(),
                    'contenttypeid': item.get('contenttypeid', '').strip(),
                    'areacode': item.get('areacode', '').strip(),
                    'sigungucode': item.get('sigungucode', '').strip(),
                    
                    # 카테고리 정보
                    'cat1': item.get('cat1', '').strip(),
                    'cat2': item.get('cat2', '').strip(),
                    'cat3': item.get('cat3', '').strip(),
                    
                    # 기타 정보
                    'zipcode': item.get('zipcode', '').strip(),
                    'mlevel': item.get('mlevel', '').strip(),
                    'readcount': 0,
                    'booktour': item.get('booktour', '').strip(),
                    
                    # 시간 정보
                    'createdtime': item.get('createdtime', '').strip(),
                    'modifiedtime': item.get('modifiedtime', '').strip(),
                    
                    # 메타데이터
                    'tags': tags,
                    'source': 'us_tourdata.txt',
                    'loaded_at': datetime.now().isoformat(),
                    
                    # 원본 데이터 보존
                    # 'raw_data': item
                }
                
                # 빈 값 제거
                doc_data = {k: v for k, v in doc_data.items() if v is not None and v != ''}
                
                # Firestore에 저장
                collection_ref.document(doc_id).set(doc_data)
                
                success_count += 1
                if i % 10 == 0:
                    print(f"⏳ 진행률: {i}/{total_count} ({i/total_count*100:.1f}%)")
                
            except Exception as e:
                error_count += 1
                print(f"❌ 항목 {i} 저장 실패: {e}")
                continue
        
        print(f"\n🎉 데이터 로드 완료!")
        print(f"✅ 성공: {success_count}개")
        print(f"❌ 실패: {error_count}개")
        print(f"📊 총 처리: {total_count}개")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def get_category_name(contenttypeid):
    """contenttypeid를 카테고리명으로 변환"""
    category_map = {
        '12': '관광지',
        '14': '문화시설', 
        '15': '축제공연행사',
        # '25': '여행코스',
        '28': '레포츠',
        '32': '숙박',
        '38': '쇼핑',
        '39': '음식점'
    }
    
    detailed_map = {
        '12': '관광지',
        '14': '박물관/전시관',
        '15': '축제/행사',
        '28': '레저/체험',
        '32': '숙박시설',
        '38': '쇼핑/시장',
        '39': '음식/맛집'
    }
    
    return detailed_map.get(contenttypeid, '일반')

if __name__ == '__main__':
    load_data_to_firestore()
