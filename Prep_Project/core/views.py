import json
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Sum
from django.views.decorators.csrf import csrf_exempt
from datetime import date, timedelta
from rest_framework.authentication import BasicAuthentication
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import (
    Site, Device, InventoryItem, Plan, Customer,
    Subscription, UsageEvent, Alert, Bill, Ticket
)
from .serializers import (
    SiteSerializer, DeviceSerializer, InventoryItemSerializer, PlanSerializer,
    CustomerSerializer, SubscriptionSerializer, UsageEventSerializer, AlertSerializer,
    BillSerializer
)
from .churn import churn_score


# ----- API ViewSets -----
class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer


@method_decorator(csrf_exempt, name='dispatch')
class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    @action(
        detail=True,
        methods=['post'],
        authentication_classes=[],      # disable SessionAuthentication (avoids CSRF)
        permission_classes=[AllowAny],
    )
    def acknowledge(self, request, pk=None):
        device = self.get_object()
        alerts_qs = Alert.objects.filter(device=device, status="open")
        count = alerts_qs.count()
        if count == 0:
            return Response({"message": f"No open alerts for device {device.identifier}"})
        alerts_qs.update(status="acknowledged")
        return Response({"message": f"Acknowledged {count} alert(s) for device {device.identifier}"})

    @action(
        detail=True,
        methods=['post'],
        authentication_classes=[],
        permission_classes=[AllowAny],
    )
    def create_ticket(self, request, pk=None):
        device = self.get_object()
        desc = request.data.get("description", f"Ticket created from dashboard for {device.identifier}")
        ticket = Ticket.objects.create(device=device, description=desc, created_by=request.data.get("created_by", "engineer"))
        # Optionally set device to maintenance to reflect ticket
        device.status = "maintenance"
        device.save(update_fields=["status"])
        return Response({"message": f"Ticket #{ticket.id} created for device {device.identifier}", "ticket_id": ticket.id})

    @action(
        detail=True,
        methods=['post'],
        authentication_classes=[],
        permission_classes=[AllowAny],
    )
    def reserve_replacement(self, request, pk=None):
        device = self.get_object()

        # map device.type -> inventory name snippet (adjust if your inventory names differ)
        mapping = {
            "CPE": "Set Top Box",
            "ROUTER": "WiFi Router",
            "TOWER": "Fiber Cable",
        }
        mapped_name = mapping.get(device.type)

        inventory_item = None
        if mapped_name:
            inventory_item = InventoryItem.objects.filter(name__icontains=mapped_name).first()
        if not inventory_item:
            # fallback: try any inventory item if mapping fails
            inventory_item = InventoryItem.objects.first()

        if not inventory_item:
            return Response({"error": "No inventory items configured"}, status=404)

        if inventory_item.stock_on_hand <= 0:
            return Response({"error": "No stock available for replacement"}, status=400)

        inventory_item.stock_on_hand -= 1
        inventory_item.save(update_fields=["stock_on_hand"])
        return Response({
            "message": f"Replacement reserved ({inventory_item.name}) for device {device.identifier}",
            "remaining_stock": inventory_item.stock_on_hand
        })


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer

class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

class UsageEventViewSet(viewsets.ModelViewSet):
    queryset = UsageEvent.objects.all()
    serializer_class = UsageEventSerializer

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all().order_by('-created_at')
    serializer_class = AlertSerializer


from rest_framework.permissions import AllowAny

class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all().order_by('-month')
    serializer_class = BillSerializer

    def list(self, request, customer_id=None):
        if customer_id:
            bills = Bill.objects.filter(customer_id=customer_id).order_by('-month')
            serializer = self.get_serializer(bills, many=True)
            return Response(serializer.data)
        return super().list(request)

    # ⬇️ CSRF-free pay action (no SessionAuthentication)
    @action(
        detail=True,
        methods=['post'],
        authentication_classes=[],      # <-- disables SessionAuthentication (no CSRF)
        permission_classes=[AllowAny],  # <-- open for hackathon demo
        url_path='pay'
    )
    def pay(self, request, pk=None):
        bill = self.get_object()
        bill.status = "paid"
        bill.save()
        return Response({"message": f"Bill {bill.id} marked as paid"})




# ----- Pages -----
def dashboard(request):
    customers = Customer.objects.count()
    devices = Device.objects.count()
    alerts_open = Alert.objects.filter(status="open").count()
    plans = Plan.objects.count()

    alert_counts = Alert.objects.filter(status="open").values("severity").annotate(count=Count("id"))
    severity_map = {"info": 0, "warning": 0, "critical": 0}
    for row in alert_counts:
        severity_map[row["severity"]] = row["count"]

    plan_counts = Subscription.objects.values("plan__name").annotate(count=Count("id"))
    plan_labels = [p["plan__name"] for p in plan_counts]
    plan_values = [p["count"] for p in plan_counts]

    today = datetime.date.today()
    usage_labels, usage_values = [], []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        usage_labels.append(day.strftime("%b %d"))
        total_gb = UsageEvent.objects.filter(date=day).aggregate(Sum("gb_used"))["gb_used__sum"] or 0
        usage_values.append(round(total_gb, 2))

    recent_alerts = Alert.objects.filter(status="open").order_by("-created_at")[:10]

    inventory = InventoryItem.objects.all()
    inventory_labels = [item.name for item in inventory]
    inventory_stock = [item.stock_on_hand for item in inventory]
    inventory_reorder = [item.reorder_point for item in inventory]

    devices_list = Device.objects.select_related("site").all()

    context = {
        "customers": customers,
        "devices": devices,
        "alerts_open": alerts_open,
        "plans": plans,
        "alert_data": list(severity_map.values()),
        "plan_labels": plan_labels,
        "plan_values": plan_values,
        "usage_labels": usage_labels,
        "usage_values": usage_values,
        "recent_alerts": recent_alerts,
        "inventory_labels": inventory_labels,
        "inventory_stock": inventory_stock,
        "inventory_reorder": inventory_reorder,
        "devices_list": devices_list,
    }
    return render(request, "dashboard.html", context)


def portal_page(request):
    return render(request, "portal.html")


# ----- APIs -----
@csrf_exempt
def onboard(request):
    """Onboard new customer + subscription"""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = payload.get("name")
    city = payload.get("city")
    plan_id = payload.get("plan_id")

    if not (name and city and plan_id):
        return JsonResponse({"error": "name, city, plan_id required"}, status=400)

    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        return JsonResponse({"error": "Invalid plan_id"}, status=404)

    existing_customer = Customer.objects.filter(name=name, city=city).first()
    if existing_customer:
        existing_sub = Subscription.objects.filter(customer=existing_customer, plan=plan).first()
        if existing_sub:
            return JsonResponse({
                "error": f"Customer '{name}' in {city} is already subscribed to {plan.name}"
            }, status=409)

    if not existing_customer:
        existing_customer = Customer.objects.create(name=name, city=city)

    subscription = Subscription.objects.create(customer=existing_customer, plan=plan)

    return JsonResponse({
        "customer_id": existing_customer.id,
        "subscription_id": subscription.id,
        "message": "Activated"
    })


@csrf_exempt
def churn_api(request, id):
    """Churn score check"""
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    customer = get_object_or_404(Customer, id=id)

    avg7, avg30 = 1.5, 5.0  # demo values
    score = churn_score(customer, avg7, avg30)

    if score >= 70:
        action = "Offer 20% discount coupon"
    elif score >= 40:
        action = "Send personalized SMS reminder"
    else:
        action = "Normal engagement"

    return JsonResponse({
        "customer": customer.name,
        "city": customer.city,
        "score": score,
        "action": action
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@authentication_classes([BasicAuthentication])   # ✅ no CSRF check
def my_plan(request, customer_id):
    try:
        sub = Subscription.objects.get(customer_id=customer_id)
    except Subscription.DoesNotExist:
        return Response({"error": "Customer has no active subscription"}, status=404)

    if request.method == 'GET':
        return Response({
            "customer": sub.customer.name,
            "city": sub.customer.city,
            "plan": sub.plan.name,
            "price": sub.plan.monthly_price,
        })

    if request.method == 'POST':
        new_plan_id = request.data.get("plan_id")
        if not new_plan_id:
            return Response({"error": "plan_id is required"}, status=400)

        try:
            plan = Plan.objects.get(id=new_plan_id)
        except Plan.DoesNotExist:
            return Response({"error": "Invalid plan_id"}, status=404)

        sub.plan = plan
        sub.save()
        return Response({
            "message": f"Plan changed to {plan.name}",
            "price": plan.monthly_price
        })





@api_view(['GET'])
def customer_usage(request, id):
    """Fetch usage + simple bill estimate"""
    try:
        customer = Customer.objects.get(id=id)
        subscription = Subscription.objects.get(customer=customer)
        plan = subscription.plan

        today = date.today()
        usage_list = []
        total_gb = 0
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            gb = UsageEvent.objects.filter(customer=customer, date=day).aggregate(Sum("gb_used"))["gb_used__sum"] or 0
            usage_list.append({"date": day.strftime("%b %d"), "gb_used": float(gb)})
            total_gb += gb

        included_gb = 100
        overage_rate = 10
        bill = plan.monthly_price
        if total_gb > included_gb:
            bill += (total_gb - included_gb) * overage_rate

        return Response({
            "customer": customer.name,
            "plan": plan.name,
            "monthly_price": plan.monthly_price,
            "usage": usage_list,
            "total_gb": total_gb,
            "bill": round(bill, 2)
        })
    except (Customer.DoesNotExist, Subscription.DoesNotExist):
        return Response({"error": "Customer or subscription not found"}, status=404)


@api_view(['GET'])
def customer_bills(request, customer_id):
    """Fetch bills for a customer"""
    bills = Bill.objects.filter(customer_id=customer_id).order_by('-month')
    serializer = BillSerializer(bills, many=True)
    return Response(serializer.data)


