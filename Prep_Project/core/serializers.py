from rest_framework import serializers

from .models import Site, Device, InventoryItem, Plan, Customer, Subscription, UsageEvent, Alert, Bill, Ticket

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = '__all__'

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = '__all__'

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)  # show plan details too
    class Meta:
        model = Subscription
        fields = '__all__'

class UsageEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageEvent
        fields = '__all__'

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'
        
        
class BillSerializer(serializers.ModelSerializer):
    month_display = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = ['id', 'customer', 'month', 'month_display', 'amount', 'status']

    def get_month_display(self, obj):
        return obj.month.strftime("%b %Y")  # e.g., Jan 2025
    
class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"

