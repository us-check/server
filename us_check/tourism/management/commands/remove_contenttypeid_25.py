from django.core.management.base import BaseCommand, CommandError
from tourism.models import TourismSpot
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'contenttypeid가 25인 관광지 데이터를 DB에서 삭제합니다'

    def handle(self, *args, **options):
        self.stdout.write('contenttypeid가 25인 데이터 삭제 시작...')
        
        # contenttypeid가 25인 데이터들의 contentid 목록
        contentids_to_remove = [
            '1944360',
            '1944358', 
            '2030578',
            '2631871',
            '1875578',
            '1875574'
        ]
        
        deleted_count = 0
        
        for contentid in contentids_to_remove:
            try:
                # TourismSpot에서 해당 contentid로 찾아서 삭제
                spots = TourismSpot.objects.filter(content_id=contentid)
                if spots.exists():
                    for spot in spots:
                        self.stdout.write(f'삭제 중: {spot.name} (content_id: {spot.content_id})')
                        spot.delete()
                        deleted_count += 1
                else:
                    self.stdout.write(f'찾을 수 없음: content_id = {contentid}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'삭제 실패 content_id {contentid}: {e}')
                )
        
        # 추가로 contenttypeid 필드가 있다면 직접 필터링
        try:
            additional_spots = TourismSpot.objects.filter(content_type_id='25')
            if additional_spots.exists():
                self.stdout.write(f'content_type_id가 25인 추가 데이터 {additional_spots.count()}개 발견')
                for spot in additional_spots:
                    self.stdout.write(f'추가 삭제: {spot.name} (content_type_id: {spot.content_type_id})')
                    spot.delete()
                    deleted_count += 1
        except Exception as e:
            self.stdout.write(f'content_type_id 필드로 검색 실패: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(f'총 {deleted_count}개의 데이터가 삭제되었습니다.')
        )
        
        # 남은 데이터 개수 확인
        remaining_count = TourismSpot.objects.count()
        self.stdout.write(f'DB에 남은 관광지 데이터: {remaining_count}개')
