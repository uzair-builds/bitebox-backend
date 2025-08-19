from django.urls import path
from .views import OrdersAPIView,OrdersDetailAPIView,CustomerNotificationView,MarkNotificationAsSeen
urlpatterns = [
    path('orders/<user_id>/',OrdersAPIView.as_view()),
    path('order/detail/<user_id>/<order_oid>/',OrdersDetailAPIView.as_view()),
    path('notifications/<user_id>/',CustomerNotificationView.as_view()),
    path('notification/<user_id>/<noti_id>/',MarkNotificationAsSeen.as_view()),
    ]