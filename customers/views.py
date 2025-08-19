from django.shortcuts import render
from store.models import Dish,Category,Cart,Tax,PortionSize,CartOrder,CartOrderItem,Notification
from account.models import User
from store.serializers import DishSerializer,CategorySerializer,CartSerializer,NotificationSerializer,CartOrderSerializer
from rest_framework import generics 
from rest_framework.permissions import AllowAny,IsAuthenticated 
from decimal import Decimal
from rest_framework.response import Response
from rest_framework import status
# Create your views here.
# Create your views here.
class OrdersAPIView(generics.ListAPIView):
    serializer_class = CartOrderSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = User.objects.get(id=user_id)

        orders = CartOrder.objects.filter(buyer=user)
        return orders
    

class OrdersDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CartOrderSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'user_id'

    def get_object(self):
        user_id = self.kwargs['user_id']
        order_oid = self.kwargs['order_oid']

        user = User.objects.get(id=user_id)

        order = CartOrder.objects.get(buyer=user, oid=order_oid)
        return order
    

class CustomerNotificationView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = (AllowAny, )

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = User.objects.get(id=user_id)
        return Notification.objects.filter(user=user)
    
class MarkNotificationAsSeen(generics.RetrieveAPIView):
    serializer_class = NotificationSerializer
    permission_classes = (AllowAny, )

    def get_object(self):
        user_id = self.kwargs['user_id']
        noti_id = self.kwargs['noti_id']
        user = User.objects.get(id=user_id)
        noti = Notification.objects.get(id=noti_id,user=user)

        if noti.seen != True:
            noti.seen=True
            noti.save()

        return noti    

