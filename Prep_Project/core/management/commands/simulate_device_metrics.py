from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
import random
from core.models import Device

class Command(BaseCommand):
    help = "Set random metrics on devices to demo rules"

    def handle(self, *args, **kwargs):
        for dev in Device.objects.all():
            dev.last_heartbeat = timezone.now() - timedelta(minutes=random.choice([5, 10, 20, 45]))
            dev.temp_c = random.choice([65, 72, 78, 83])
            dev.eol_date = date.today() + timedelta(days=random.choice([10, 25, 60, 120]))
            dev.save()
        self.stdout.write(self.style.SUCCESS("Simulated device metrics"))
