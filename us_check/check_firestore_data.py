#!/usr/bin/env python3
"""
Firestore 데이터 현황 확인 스크립트
"""
import os
import django
from google.cloud import firestore

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'us_check.settings')
django.setup()

def check_firestore_data():
    try:
        # Firestore 클라이언트 초기화
        db = firestore.Client()
        collection_name = 'uiseong_tourism_spots'
        
        print(f"🔍 Firestore 컬렉션 '{collection_name}' 확인 중...")
        
        # 문서 개수 확인
        docs = db.collection(collection_name).stream()
        doc_list = list(docs)
        total_count = len(doc_list)
        
        print(f"📊 총 문서 개수: {total_count}개")
        
        if total_count > 0:
            print(f"📝 첫 번째 문서 샘플:")
            first_doc = doc_list[0]
            data = first_doc.to_dict()
            print(f"   - ID: {first_doc.id}")
            print(f"   - 이름: {data.get('title', 'N/A')}")
            print(f"   - 주소: {data.get('addr1', 'N/A')}")
            print(f"   - 카테고리: {data.get('contenttypeid', 'N/A')}")
            
            # contenttypeid별 분포 확인
            content_types = {}
            for doc in doc_list:
                data = doc.to_dict()
                content_type = data.get('contenttypeid', 'Unknown')
                content_types[content_type] = content_types.get(content_type, 0) + 1
            
            print(f"📈 contenttypeid별 분포:")
            for content_type, count in sorted(content_types.items()):
                print(f"   - {content_type}: {count}개")
        else:
            print("❌ Firestore에 데이터가 없습니다.")
            print("💡 us_tourdata.txt에서 Firestore로 데이터를 로드해야 합니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("💡 Google Cloud 인증 또는 Firestore 설정을 확인하세요.")

if __name__ == "__main__":
    check_firestore_data()
