from django.contrib import admin
from .models import (
    Vehicle, VehicleHistory, Case, StatusLog, Quote, QuoteLine,
    Appointment, Notification, Invoice, InvoiceLine, Payment, UserProfile
)

admin.site.register(Vehicle)
admin.site.register(VehicleHistory)
admin.site.register(Case)
admin.site.register(StatusLog)
admin.site.register(Quote)
admin.site.register(QuoteLine)
admin.site.register(Appointment)
admin.site.register(Notification)
admin.site.register(Invoice)
admin.site.register(InvoiceLine)
admin.site.register(Payment)
admin.site.register(UserProfile)
