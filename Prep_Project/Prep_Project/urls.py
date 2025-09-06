from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from core.views import (
    BillViewSet, SiteViewSet, DeviceViewSet, InventoryItemViewSet, PlanViewSet,
    CustomerViewSet, SubscriptionViewSet, UsageEventViewSet, AlertViewSet,
    dashboard, my_plan, onboard, portal_page, churn_api, customer_usage, customer_bills,
)

router = routers.DefaultRouter()
router.register(r'sites', SiteViewSet)
router.register(r'devices', DeviceViewSet)
router.register(r'inventory', InventoryItemViewSet)
router.register(r'plans', PlanViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'subscriptions', SubscriptionViewSet)
router.register(r'usage', UsageEventViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'bills', BillViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),

    # Pages
    path('dashboard/', dashboard, name="dashboard"),
    path('portal/', portal_page, name='portal_page'),

    # APIs
    path('api/onboard/', onboard, name='onboard'),
    path('api/customers/<int:id>/churn_score/', churn_api, name='churn_api'),
    path("api/customers/<int:id>/usage/", customer_usage),

    # My Plan (get + change)
    path('api/customers/<int:customer_id>/my_plan/', my_plan, name="my_plan"),

    # Bills (fetch + pay)
    path('api/customers/<int:customer_id>/bills/', customer_bills, name="customer-bills"),

]
