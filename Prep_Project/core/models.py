from django.db import models

# Sites / Locations
class Site(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.city})"


# Devices in the network
class Device(models.Model):
    TYPE_CHOICES = [
        ("CPE", "Customer Premises Equipment"),
        ("ROUTER", "Router"),
        ("TOWER", "Cell Tower"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("maintenance", "Under Maintenance"),
        ("faulty", "Faulty"),
        ("decommissioned", "Decommissioned"),
    ]

    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True)
    identifier = models.CharField(max_length=100, unique=True)   # e.g., "dev-123"
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    last_heartbeat = models.DateTimeField(null=True, blank=True)  # last check-in time
    temp_c = models.FloatField(null=True, blank=True)             # device temp in Celsius
    eol_date = models.DateField(null=True, blank=True)            # end of life date

    def __str__(self):
        return f"{self.identifier} ({self.type})"

# Inventory items (spare parts, replacements)
class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    stock_on_hand = models.IntegerField(default=0)
    reorder_point = models.IntegerField(default=5)

    def __str__(self):
        return f"{self.name} (Stock: {self.stock_on_hand})"


# Plans for customers
class Plan(models.Model):
    name = models.CharField(max_length=100)
    speed_mbps = models.IntegerField()
    monthly_price = models.IntegerField()

    def __str__(self):
        return f"{self.name} - {self.speed_mbps} Mbps - ₹{self.monthly_price}"


# Customers
class Customer(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    tenure_months = models.IntegerField(default=0)
    complaints_last_90d = models.IntegerField(default=0)
    last_recharge_days_ago = models.IntegerField(default=0)

    def __str__(self):
        return self.name


# Subscription of a customer to a plan
class Subscription(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    start_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, default="active")

    def __str__(self):
        return f"{self.customer.name} → {self.plan.name}"


# Usage data (e.g., daily data consumption in GB)
class UsageEvent(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateField()
    gb_used = models.FloatField()

    def __str__(self):
        return f"{self.customer.name} - {self.date} - {self.gb_used} GB"


# Alerts (generated when devices/customers need attention)
class Alert(models.Model):
    SEVERITY = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]

    severity = models.CharField(max_length=10, choices=SEVERITY)
    type = models.CharField(max_length=100)  # e.g., "DEVICE_OVERHEAT"
    message = models.TextField()
    device = models.ForeignKey(Device, null=True, blank=True, on_delete=models.SET_NULL)
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, default="open")  # open/acknowledged/closed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.severity}] {self.type}"

# Bill for customers
class Bill(models.Model):
    STATUS_CHOICES = [
        ("paid", "Paid"),
        ("unpaid", "Unpaid"),
        ("overdue", "Overdue"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    month = models.DateField()  # first day of the billing month
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="unpaid")

    def __str__(self):
        return f"Bill for {self.customer.name} - {self.month.strftime('%B %Y')} ({self.status})"


# --- add this to core/models.py (below other models) ---
class Ticket(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
    ]
    device = models.ForeignKey("Device", on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    description = models.TextField(blank=True, default="")
    created_by = models.CharField(max_length=100, blank=True, default="engineer")

    def __str__(self):
        device_id = self.device.identifier if self.device else "N/A"
        return f"Ticket #{self.id} - {device_id} - {self.status}"
