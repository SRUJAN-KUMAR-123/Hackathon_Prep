from django.contrib import admin
from .models import Site, Device, InventoryItem, Plan, Customer, Subscription, UsageEvent, Alert

admin.site.register(Site)
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("identifier", "type", "status", "site", "last_heartbeat", "temp_c", "eol_date")
    list_filter = ("type", "status", "site")
    search_fields = ("identifier",)
    ordering = ("identifier",)
admin.site.register(InventoryItem)
admin.site.register(Plan)
admin.site.register(Customer)
admin.site.register(Subscription)
admin.site.register(UsageEvent)
@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("severity", "type", "message", "device", "status", "created_at")
    list_filter = ("severity", "status", "type")
    search_fields = ("message", "device__identifier")
    ordering = ("-created_at",)
