"""
QR 코드 생성 및 관리 서비스 - Firestore 기반
"""
import os
import logging
import qrcode
import json
import uuid
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class QRCodeService:
    """QR 코드 생성 및 관리 서비스 - Firestore 기반"""
    
    def __init__(self):
        self.qr_storage_path = getattr(settings, 'QR_CODE_STORAGE_PATH', '/tmp/qr_codes')
        self.qr_base_url = getattr(settings, 'QR_CODE_BASE_URL', 'http://localhost:8000/qr/')
        
        # QR 코드 저장 디렉토리 생성
        os.makedirs(self.qr_storage_path, exist_ok=True)
    
    def generate_qr_for_tourism_selection(self, selection_data: Dict) -> Dict:
        """관광지 선택 결과를 위한 QR 코드 생성"""
        try:
            logger.info(f"QR 코드 생성 시작: {selection_data.get('selection_id')}")
            
            # QR 코드에 포함될 데이터
            qr_data = {
                'type': 'tourism_selection',
                'selection_id': selection_data.get('selection_id'),
                'spots': selection_data.get('spots', []),
                'user_info': selection_data.get('user_info', {}),
                'timestamp': selection_data.get('timestamp'),
                'original_query': selection_data.get('original_query', '')
            }
            
            # QR 코드 생성
            qr_result = self._generate_qr_code(
                data=json.dumps(qr_data),
                filename=f"tourism_selection_{selection_data.get('selection_id')}"
            )
            
            if qr_result['success']:
                return {
                    'success': True,
                    'qr_url': qr_result['file_path'],
                    'access_url': f"{self.qr_base_url}{selection_data.get('selection_id')}",
                    'qr_data': qr_data,
                    'message': 'QR 코드가 성공적으로 생성되었습니다.'
                }
            else:
                return {
                    'success': False,
                    'message': f"QR 코드 생성 실패: {qr_result.get('message', '')}"
                }
        
        except Exception as e:
            logger.error(f"QR 코드 생성 오류: {e}")
            return {
                'success': False,
                'message': f'QR 코드 생성 중 오류가 발생했습니다: {str(e)}'
            }
    
    def _generate_qr_code(self, data: str, filename: str) -> Dict:
        """실제 QR 코드 이미지 생성"""
        try:
            # QR 코드 생성 설정
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            # QR 코드 이미지 생성
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 파일 저장
            file_path = os.path.join(self.qr_storage_path, f"{filename}.png")
            img.save(file_path)
            
            logger.info(f"QR 코드 파일 저장 완료: {file_path}")
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': f"{filename}.png",
                'url': f"{self.qr_base_url}{filename}.png"
            }
            
        except Exception as e:
            logger.error(f"QR 코드 이미지 생성 오류: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_qr_data(self, qr_id: str) -> Optional[Dict]:
        """QR 코드 데이터 조회 (간단한 구현)"""
        try:
            # 실제 구현에서는 Firestore에서 데이터를 조회해야 함
            # 현재는 기본적인 응답만 반환
            return {
                'qr_id': qr_id,
                'type': 'tourism_selection',
                'message': 'QR 코드 데이터 조회 성공',
                'access_time': 'now'
            }
            
        except Exception as e:
            logger.error(f"QR 데이터 조회 오류: {e}")
            return None
    
    def generate_spots_qr(self, selected_spots: list, user_id: str = None, session_id: str = None) -> Dict:
        """관광지 목록을 위한 QR 코드 생성 (호환성 메서드)"""
        try:
            qr_id = str(uuid.uuid4())
            
            selection_data = {
                'selection_id': qr_id,
                'spots': selected_spots,
                'user_info': {
                    'user_id': user_id,
                    'session_id': session_id
                },
                'timestamp': 'now'
            }
            
            return self.generate_qr_for_tourism_selection(selection_data)
            
        except Exception as e:
            logger.error(f"spots QR 생성 오류: {e}")
            return {
                'success': False,
                'message': str(e)
            }
