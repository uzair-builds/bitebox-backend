from django.urls import re_path
from .consumers import OrderTrackingConsumer

websocket_urlpatterns = [
    re_path(r"ws/tracking/(?P<order_id>\w+)/(?P<tracking_token>[\w-]+)/$", OrderTrackingConsumer.as_asgi()),
]
