from django.core.mail import send_mail
from django.conf import settings

def send_tracking_email(recipient_email, tracking_url, order_id):
    subject = f"BITEBOX: New Delivery Available (Order {order_id})"
    message = f"""Hello,

A new order is ready for delivery.

Please open the link below to start sharing your real-time location:
{tracking_url}

This link is valid for this order only.

Regards,
BITEBOX
"""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email])
