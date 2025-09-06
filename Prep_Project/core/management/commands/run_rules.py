from django.core.management.base import BaseCommand
from core.alert_rules import evaluate_device_rules

class Command(BaseCommand):
    help = "Evaluate device rules and create alerts"

    def handle(self, *args, **kwargs):
        alerts = evaluate_device_rules()
        self.stdout.write(self.style.SUCCESS(f"Created {len(alerts)} alerts"))
