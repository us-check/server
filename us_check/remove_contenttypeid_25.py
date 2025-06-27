#!/usr/bin/env python3
"""
contenttypeid가 25인 데이터를 us_tourdata.txt에서 제거하는 스크립트
"""
import json
import os

def remove_contenttypeid_25():
    file_path = "us_tourdata.txt"
    
    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 원본 아이템 수
    original_items = data['response']['body']['items']['item']
    original_count = len(original_items)
    
    # contenttypeid가 25인 항목들의 contentid 수집
    removed_contentids = []
    
    # contenttypeid가 25가 아닌 항목들만 필터링
    filtered_items = []
    for item in original_items:
        if item.get('contenttypeid') == '25':
            removed_contentids.append(item.get('contentid'))
            print(f"제거할 항목: {item.get('title')} (contentid: {item.get('contentid')})")
        else:
            filtered_items.append(item)
    
    # 데이터 업데이트
    data['response']['body']['items']['item'] = filtered_items
    data['response']['body']['totalCount'] = len(filtered_items)
    data['response']['body']['numOfRows'] = len(filtered_items)
    
    # 파일 쓰기
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"\n=== 작업 완료 ===")
    print(f"원본 항목 수: {original_count}")
    print(f"제거된 항목 수: {len(removed_contentids)}")
    print(f"남은 항목 수: {len(filtered_items)}")
    print(f"제거된 contentid 목록: {removed_contentids}")
    
    return removed_contentids

if __name__ == "__main__":
    removed_ids = remove_contenttypeid_25()
