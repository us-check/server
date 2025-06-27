"""
QR 코드 생성 및 관리 서비스
"""
import os
import logging
import qrcode
import json
from typing import Dict, Optional
from django.conf import settings
from django.core.files.storage import default_storage
from django.urls import reverse
from google.cloud import storage
# Django 모델 제거 - Firestore 기반으로 전환
# from .models import QRCode

logger = logging.getLogger(__name__)

class QRCodeService:
    """QR 코드 생성 및 관리 서비스"""
    
    def __init__(self):
        self.storage_path = getattr(settings, 'QR_CODE_STORAGE_PATH', 'qr_codes')
        self.base_url = getattr(settings, 'QR_CODE_BASE_URL', 'http://localhost:8000/qr/')
        self.gcp_bucket = getattr(settings, 'GCP_BUCKET_NAME', None)
        
        # 로컬 저장소 디렉토리 생성
        os.makedirs(self.storage_path, exist_ok=True)
    
    def generate_qr_for_tourism_selection(self, selection_data: Dict) -> Dict:
        """관광지 선택 데이터에 대한 QR 코드 생성"""
        try:
            # QR 코드에 포함될 데이터 구성
            qr_data = {
                'type': 'tourism_selection',
                'selection_id': selection_data.get('selection_id'),
                'spots': selection_data.get('spots', []),
                'timestamp': selection_data.get('timestamp'),
                'user_info': selection_data.get('user_info', {}),
                'access_url': f"{self.base_url}view/{selection_data.get('selection_id')}"
            }
            
            # QR 코드 생성
            qr_result = self._generate_qr_code(
                data=json.dumps(qr_data),
                filename=f"tourism_selection_{selection_data.get('selection_id')}"
            )
            
            if qr_result['success']:
                # Firestore에 QR 코드 정보 저장 (추후 구현)
                # TODO: Firestore에 QR 코드 정보 저장
                
                return {
                    'success': True,
                    'qr_code_id': qr_code.id,
                    'qr_url': qr_result['url'],
                    'gcp_url': qr_result.get('gcp_url', ''),
                    'access_url': qr_data['access_url']
                }
            else:
                return qr_result
                
        except Exception as e:
            logger.error(f"Error generating QR code for tourism selection: {e}")
            return {'success': False, 'message': str(e)}
    
    def _generate_qr_code(self, data: str, filename: str) -> Dict:
        """QR 코드 이미지 생성"""
        try:
            # QR 코드 생성
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # 이미지 생성
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 파일 저장
            filename = f"{filename}.png"
            local_path = os.path.join(self.storage_path, filename)
            
            # 로컬 저장
            img.save(local_path)
            
            result = {
                'success': True,
                'file_path': local_path,
                'filename': filename,
                'url': f"{self.base_url}{filename}"
            }
            
            # GCP Storage에 업로드 (옵션)
            if self.gcp_bucket:
                gcp_url = self._upload_to_gcp_storage(local_path, filename)
                if gcp_url:
                    result['gcp_url'] = gcp_url
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return {'success': False, 'message': str(e)}
    
    def _upload_to_gcp_storage(self, local_path: str, filename: str) -> Optional[str]:
        """GCP Cloud Storage에 QR 코드 업로드"""
        try:
            if not self.gcp_bucket:
                return None
            
            # GCP Storage 클라이언트 초기화
            client = storage.Client()
            bucket = client.bucket(self.gcp_bucket)
            
            # 파일 업로드
            blob_name = f"qr_codes/{filename}"
            blob = bucket.blob(blob_name)
            
            with open(local_path, 'rb') as f:
                blob.upload_from_file(f, content_type='image/png')
            
            # 공개 URL 생성
            blob.make_public()
            
            logger.info(f"QR code uploaded to GCP Storage: {blob_name}")
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Error uploading to GCP Storage: {e}")
            return None
    
    def get_qr_code_data(self, qr_code_id: int) -> Dict:
        """QR 코드 데이터 조회"""
        try:
            qr_code = QRCode.objects.get(id=qr_code_id)
            return {
                'success': True,
                'qr_code': {
                    'id': qr_code.id,
                    'type': qr_code.qr_type,
                    'data': qr_code.data,
                    'url': qr_code.url,
                    'gcp_url': qr_code.gcp_url,
                    'created_at': qr_code.created_at.isoformat(),
                    'is_active': qr_code.is_active
                }
            }
        except QRCode.DoesNotExist:
            return {'success': False, 'message': 'QR code not found'}
        except Exception as e:
            logger.error(f"Error getting QR code data: {e}")
            return {'success': False, 'message': str(e)}
    
    def deactivate_qr_code(self, qr_code_id: int) -> Dict:
        """QR 코드 비활성화"""
        try:
            qr_code = QRCode.objects.get(id=qr_code_id)
            qr_code.is_active = False
            qr_code.save()
            
            return {'success': True, 'message': 'QR code deactivated'}
        except QRCode.DoesNotExist:
            return {'success': False, 'message': 'QR code not found'}
        except Exception as e:
            logger.error(f"Error deactivating QR code: {e}")
            return {'success': False, 'message': str(e)}


class CloudFunctionService:
    """GCP Cloud Functions 연동 서비스"""
    
    def __init__(self):
        self.cloud_function_url = getattr(settings, 'CLOUD_FUNCTION_URL', None)
    
    def trigger_qr_generation(self, data: Dict) -> Dict:
        """Cloud Function을 통한 QR 코드 생성 트리거"""
        try:
            if not self.cloud_function_url:
                return {'success': False, 'message': 'Cloud Function URL not configured'}
            
            import requests
            
            response = requests.post(
                self.cloud_function_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return {'success': True, 'result': response.json()}
            else:
                return {
                    'success': False,
                    'message': f'Cloud Function error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error triggering Cloud Function: {e}")
            return {'success': False, 'message': str(e)}
