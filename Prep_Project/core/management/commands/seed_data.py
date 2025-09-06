from django.core.management.base import BaseCommand
from core.models import Site, Device, InventoryItem, Plan, Customer, Subscription, UsageEvent, Alert, Bill
from django.utils import timezone
import random
import datetime
from django.db.models import Sum

class Command(BaseCommand):
    help = "Seed database with sample data"

    def handle(self, *args, **kwargs):
        # Clear old data
        Bill.objects.all().delete()
        Alert.objects.all().delete()
        UsageEvent.objects.all().delete()
        Subscription.objects.all().delete()
        Customer.objects.all().delete()
        Plan.objects.all().delete()
        InventoryItem.objects.all().delete()
        Device.objects.all().delete()
        Site.objects.all().delete()

        # Create Sites
        site1 = Site.objects.create(name="Tower A", city="Hyderabad")
        site2 = Site.objects.create(name="Router Hub", city="Bangalore")

        # Create Devices
        devices = [
            Device.objects.create(site=site1, identifier="dev-001", type="TOWER", status="active"),
            Device.objects.create(site=site1, identifier="dev-002", type="ROUTER", status="maintenance"),
            Device.objects.create(site=site2, identifier="dev-003", type="CPE", status="faulty"),
        ]

        # Create Inventory
        InventoryItem.objects.create(name="Fiber Cable", stock_on_hand=20, reorder_point=5)
        InventoryItem.objects.create(name="WiFi Router", stock_on_hand=3, reorder_point=5)
        InventoryItem.objects.create(name="Set Top Box", stock_on_hand=15, reorder_point=10)

        # Create Plans
        plan_basic = Plan.objects.create(name="Basic", speed_mbps=50, monthly_price=499)
        plan_premium = Plan.objects.create(name="Premium", speed_mbps=200, monthly_price=999)
        plan_ultra = Plan.objects.create(name="Ultra", speed_mbps=500, monthly_price=1999)

        # Create Customers
        customers = [
            Customer.objects.create(name="Ravi Kumar", city="Hyderabad", tenure_months=12, complaints_last_90d=1, last_recharge_days_ago=5),
            Customer.objects.create(name="Anita Sharma", city="Bangalore", tenure_months=6, complaints_last_90d=0, last_recharge_days_ago=2),
            Customer.objects.create(name="John Doe", city="Chennai", tenure_months=3, complaints_last_90d=2, last_recharge_days_ago=10),
        ]

        # Subscriptions
        subs = [
            Subscription.objects.create(customer=customers[0], plan=plan_basic),
            Subscription.objects.create(customer=customers[1], plan=plan_premium),
            Subscription.objects.create(customer=customers[2], plan=plan_ultra),
        ]

        # Usage Events (last 5 days)
        today = timezone.now().date()
        for cust in customers:
            for i in range(5):
                UsageEvent.objects.create(
                    customer=cust,
                    date=today - datetime.timedelta(days=i),
                    gb_used=round(random.uniform(1, 10), 2)
                )

        # Alerts
        Alert.objects.create(severity="warning", type="DEVICE_OVERHEAT", message="Tower A temperature high", device=devices[0])
        Alert.objects.create(severity="critical", type="DEVICE_DOWN", message="Router dev-003 is not responding", device=devices[2])
        Alert.objects.create(severity="info", type="CUSTOMER_COMPLAINT", message="Customer John Doe filed a complaint", customer=customers[2])

        # Bills
        for sub in subs:
            cust = sub.customer
            # sum of usage in last 30 days
            usage_total = UsageEvent.objects.filter(customer=cust).aggregate(total=Sum("gb_used"))["total"] or 0
            usage_charge = usage_total * 10  # e.g., ₹10 per GB
            amount = sub.plan.monthly_price + usage_charge

            Bill.objects.create(
                customer=cust,
                month=today.replace(day=1),
                amount=round(amount, 2),
                status="unpaid"
            )
            
        # Bills
        for cust in customers:
            for i in range(3):  # last 3 months bills
                Bill.objects.create(
                    customer=cust,
                    month=(today.replace(day=1) - datetime.timedelta(days=30*i)),
                    amount=random.choice([499, 999, 1999]),
                    status=random.choice(["paid", "unpaid"])
                )

        self.stdout.write(self.style.SUCCESS("✅ Database seeded with sample data + bills"))
        
        
