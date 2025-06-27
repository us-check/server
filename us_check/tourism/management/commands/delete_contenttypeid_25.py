"""
contenttypeid가 25인 관광지 데이터 삭제 명령어
"""
from django.core.management.base import BaseCommand
from tourism.models import TourismSpot
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Delete tourism spots with contenttypeid = 25'
    
    def handle(self, *args, **options):
        """contenttypeid가 25인 관광지 데이터 삭제"""
        
        # contenttypeid가 25인 데이터 조회
        spots_to_delete = TourismSpot.objects.filter(content_type_id='25')
        
        if not spots_to_delete.exists():
            self.stdout.write(
                self.style.WARNING('contenttypeid가 25인 데이터가 없습니다.')
            )
            return
        
        # 삭제할 데이터 정보 출력
        self.stdout.write(f'삭제할 데이터 개수: {spots_to_delete.count()}')
        
        for spot in spots_to_delete:
            self.stdout.write(f'- ID: {spot.content_id}, 이름: {spot.name}, 타입: {spot.content_type_id}')
        
        # 사용자 확인
        confirm = input('정말로 삭제하시겠습니까? (y/N): ')
        
        if confirm.lower() in ['y', 'yes']:
            # 데이터 삭제
            deleted_count = spots_to_delete.count()
            spots_to_delete.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ {deleted_count}개의 관광지 데이터가 삭제되었습니다.')
            )
            
            logger.info(f'Deleted {deleted_count} tourism spots with contenttypeid=25')
        else:
            self.stdout.write(
                self.style.WARNING('삭제가 취소되었습니다.')
            )
