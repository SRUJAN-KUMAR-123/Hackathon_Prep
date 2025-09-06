from django.core.management.base import BaseCommand
from core.models import Customer, UsageEvent
import datetime, random

class Command(BaseCommand):
    help = "Seed random usage events for demo purposes"

    def handle(self, *args, **kwargs):
        today = datetime.date.today()

        customers = Customer.objects.all()
        if not customers.exists():
            self.stdout.write(self.style.ERROR("⚠️ No customers found. Seed customers first!"))
            return

        for c in customers:
            for i in range(7):  # last 7 days
                d = today - datetime.timedelta(days=i)
                gb_used = random.randint(2, 20)
                UsageEvent.objects.create(customer=c, gb_used=gb_used, date=d)
        
        self.stdout.write(self.style.SUCCESS("✅ Seeded 7 days usage for all customers"))
