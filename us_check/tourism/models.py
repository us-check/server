# Django 모델 제거 - 완전히 Firestore 기반으로 전환
# 
# 기존의 Django ORM 모델들은 더 이상 사용하지 않습니다.
# 모든 데이터는 Firestore에서 직접 관리됩니다.
#
# 데이터 구조:
# 1. uiseong_tourism_spots: 관광지 정보
# 2. user_tourism_selections: 사용자 선택 기록  
# 3. qr_codes: QR 코드 정보
#
# 각 컬렉션의 스키마는 서비스 클래스에서 정의됩니다.

# 아무것도 import하지 않음 - 완전히 Firestore로 대체
pass
