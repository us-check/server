"""
의성군 관광지 데이터 로더
76개의 관광지 데이터를 Firestore 및 Django 모델에 로드
"""
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from tourism.models import TourismSpot
from tourism.services import FirestoreService

class Command(BaseCommand):
    help = '의성군 관광지 데이터를 로드합니다'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--json-file',
            type=str,
            help='관광지 데이터 JSON 파일 경로',
        )
        parser.add_argument(
            '--upload-to-firestore',
            action='store_true',
            help='Firestore에 데이터 업로드',
        )
        parser.add_argument(
            '--sync-from-firestore',
            action='store_true',
            help='Firestore에서 데이터 동기화',
        )
    
    def handle(self, *args, **options):
        if options['json_file']:
            self.load_from_json(options['json_file'], options['upload_to_firestore'])
        elif options['sync_from_firestore']:
            self.sync_from_firestore()
        else:
            self.stdout.write(
                self.style.ERROR('--json-file 또는 --sync-from-firestore 옵션을 사용하세요')
            )
    
    def load_from_json(self, json_file_path, upload_to_firestore=False):
        """JSON 파일에서 관광지 데이터 로드"""
        try:
            if not os.path.exists(json_file_path):
                self.stdout.write(
                    self.style.ERROR(f'파일을 찾을 수 없습니다: {json_file_path}')
                )
                return
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'tourism_spots' in data:
                tourism_data = data['tourism_spots']
            elif isinstance(data, list):
                tourism_data = data
            else:
                self.stdout.write(
                    self.style.ERROR('JSON 데이터 형식이 올바르지 않습니다')
                )
                return
            
            self.stdout.write(f'총 {len(tourism_data)}개의 관광지 데이터를 발견했습니다')
            
            # Firestore에 업로드
            if upload_to_firestore:
                firestore_service = FirestoreService()
                upload_result = firestore_service.upload_tourism_data(tourism_data)
                
                if upload_result['success']:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Firestore에 {upload_result["uploaded_count"]}개 데이터 업로드 완료'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Firestore 업로드 실패: {upload_result["message"]}')
                    )
            
            # Django 모델에 저장
            created_count = 0
            updated_count = 0
            
            for item in tourism_data:
                try:
                    tourism_spot, created = TourismSpot.objects.update_or_create(
                        name=item.get('name', ''),
                        defaults={
                            'description': item.get('description', ''),
                            'address': item.get('address', ''),
                            'latitude': item.get('latitude'),
                            'longitude': item.get('longitude'),
                            'category': item.get('category', ''),
                            'tags': item.get('tags', []),
                            'contact_info': item.get('contact_info', ''),
                            'website': item.get('website', ''),
                            'opening_hours': item.get('opening_hours', ''),
                            'raw_data': item,
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'데이터 저장 오류: {item.get("name", "Unknown")} - {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Django 모델 저장 완료: 생성 {created_count}개, 업데이트 {updated_count}개'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'데이터 로드 중 오류 발생: {e}')
            )
    
    def sync_from_firestore(self):
        """Firestore에서 데이터 동기화"""
        try:
            firestore_service = FirestoreService()
            sync_result = firestore_service.sync_tourism_data()
            
            if sync_result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Firestore 동기화 완료: 새로 생성 {sync_result["synced_count"]}개, '
                        f'업데이트 {sync_result["updated_count"]}개'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Firestore 동기화 실패: {sync_result["message"]}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Firestore 동기화 중 오류 발생: {e}')
            )
