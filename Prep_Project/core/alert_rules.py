from django.utils import timezone
from .models import Device, Alert

def evaluate_device_rules():
    alerts_created = []
    now = timezone.now()
    for dev in Device.objects.all():
        # Rule 1: Heartbeat missed (>15 minutes)
        if dev.last_heartbeat and (now - dev.last_heartbeat).total_seconds() > 15*60:
            a = Alert.objects.create(
                severity="critical", type="HEARTBEAT_MISSED",
                message=f"No heartbeat for >15 minutes for {dev.identifier}", device=dev
            )
            alerts_created.append(a)

        # Rule 2: Temperature thresholds
        if dev.temp_c is not None:
            if dev.temp_c >= 80:
                a = Alert.objects.create(
                    severity="critical", type="OVERHEAT",
                    message=f"Device {dev.identifier} temp {dev.temp_c}C", device=dev
                )
                alerts_created.append(a)
            elif dev.temp_c >= 70:
                a = Alert.objects.create(
                    severity="warning", type="WARM",
                    message=f"Device {dev.identifier} temp {dev.temp_c}C", device=dev
                )
                alerts_created.append(a)

        # Rule 3: Approaching End-of-Life (≤30 days)
        if dev.eol_date:
            days = (dev.eol_date - timezone.localdate()).days
            if days <= 30:
                a = Alert.objects.create(
                    severity="warning", type="EOL_SOON",
                    message=f"Device {dev.identifier} EOL within {max(days,0)} days", device=dev
                )
                alerts_created.append(a)

    return alerts_created
