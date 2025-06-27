#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
us_tourdata.txt 파일에 overview 필드를 추가하는 스크립트
"""
import json
import re

def add_overview_to_data():
    """각 관광지 항목에 overview 필드 추가"""
    
    # overview 데이터 매핑 (title을 기반으로)
    overview_map = {
        "초해고택[한국관광 품질인증/Korea Quality]": "전통 한옥 숙박체험 고택",
        "의성 조문국박물관": "조문국 역사문화 전시관",
        "운람사(의성)": "고즈넉한 전통 사찰",
        "옥련사(의성)": "산속 깊은 고즈넉한 사찰",
        "고운사(의성)": "신라시대 유서깊은 고찰",
        "의성 산수유마을 꽃맞이행사": "봄철 산수유꽃 축제 행사",
        "의성 펫월드": "동물과 함께하는 체험공간",
        "의성 탑산약수온천": "천연 약수 온천 휴양지",
        "남선옥": "전통 한정식 맛집",
        "의성전통시장, 의성장 (2, 7일)": "2일과 7일 열리는 전통장터",
        "후산정사": "조선시대 선비문화 유적",
        "의성 금성산 고분군": "신라시대 고분군 유적지",
        "의성 소우당": "전통 한옥 고택 숙박시설",
        "의성 최치원문학관": "최치원 문학과 생애 전시관",
        "빙계얼음골 야영장": "여름철 피서 캠핑장",
        "비봉산": "등산과 자연경관 명소",
        "금성산(의성)": "의성군 대표 등산 명소",
        "의성 점곡계곡": "맑은 계곡물과 시원한 계곡",
        "만경촌마을": "전통문화 체험마을",
        "의성향교": "조선시대 교육기관 유적",
        "금봉자연휴양림": "숲속 휴양과 힐링 공간",
        "의성 사촌마을": "은행나무로 유명한 전통마을",
        "빙계계곡": "여름 피서지로 인기 계곡",
        "의성 조문국사적지": "고대 조문국 왕도 유적지",
        "의성 제오리 공룡발자국화석 산지": "중생대 공룡화석 발견지",
        "한국전통창조박물관": "전통문화와 창조예술 전시관",
        "의성가음지": "자연 습지와 생태 관찰지",
        "의성 경덕왕릉": "신라 경덕왕의 능묘",
        "수정사(의성)": "고요한 산사 명상 공간",
        "빙계서원": "조선시대 교육기관 서원",
        "개천지와 조성지": "천연 저수지와 습지",
        "비안향교": "조선시대 지방 교육기관",
        "의성 왜가리생태마을": "왜가리 서식지 생태마을",
        "의성문화원": "지역문화 전시와 교육공간",
        "장대서원": "조선시대 선현 추모 서원",
        "우곡서원": "유학자를 기리는 서원",
        "속수서원": "전통 유학 교육 서원",
        "산운마을": "산속 전통문화 체험마을",
        "의성 소계당": "조선시대 고택과 정원",
        "대곡사(의성)": "깊은 산중 고즈넉한 사찰",
        "달빛공원": "야경이 아름다운 공원",
        "의성 만취당": "조선시대 문인의 고택"
    }
    
    # 파일 읽기
    with open('us_tourdata.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # JSON 파싱
    data = json.loads(content)
    items = data['response']['body']['items']['item']
    
    # 각 항목에 overview 추가
    for item in items:
        title = item.get('title', '')
        if title in overview_map:
            item['overview'] = overview_map[title]
        else:
            # 제목을 기반으로 기본 설명 생성
            if '사' in title and ('절' in title or '암' in title):
                item['overview'] = "전통 불교 사찰"
            elif '박물관' in title:
                item['overview'] = "역사문화 전시 박물관"
            elif '마을' in title:
                item['overview'] = "전통문화 체험마을"
            elif '계곡' in title:
                item['overview'] = "자연 계곡 피서지"
            elif '산' in title:
                item['overview'] = "등산과 자연경관 명소"
            elif '온천' in title:
                item['overview'] = "자연 온천 휴양지"
            elif '향교' in title or '서원' in title:
                item['overview'] = "조선시대 교육기관"
            elif '고택' in title or '당' in title:
                item['overview'] = "전통 한옥 고택"
            elif '맛집' in title or item.get('cat1') == 'A05':
                item['overview'] = "지역 특색 맛집"
            elif '축제' in title or '행사' in title:
                item['overview'] = "지역 문화 축제 행사"
            else:
                item['overview'] = "의성군 대표 관광명소"
    
    # 파일 저장
    with open('us_tourdata.txt', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"✅ 총 {len(items)}개 항목에 overview 필드를 추가했습니다.")

if __name__ == "__main__":
    add_overview_to_data()
