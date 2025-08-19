from django.forms import ValidationError
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics,status
from store.models import Dish,CartOrder,CartOrderItem,Review,Coupon,Notification,PortionSize,SpiceLevel
from store.serializers import SummarySerializer,DishSerializer,RestaurantSerializer,NotificationSerializer,NotificationSummarySerializer,CouponSummarySerializer,CouponSerializer,ReviewSerializer, CartOrderSerializer,CartOrderItemSerializer,SpecificationSerializer,SpiceLevelSerializer,PortionSizeSerializer,GallerySerializer
from .models import DeliveryBoy, Restaurant,RestaurantRequest
from .serializers import DeliveryBoySerializer, EarningSummarySerializer, RestaurantCreateSerializer,RestaurantRequestSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from math import radians, sin, cos, sqrt, atan2
from account.models import User,Profile
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication 
from django.db import models
from account.serializers import ProfileSerializer
from django.db import transaction
from rest_framework.decorators import api_view,permission_classes
from django.db.models.functions import ExtractMonth
from datetime import datetime, timedelta
from django.db.models import F, Sum, ExpressionWrapper, DecimalField,Q
from .email import send_tracking_email
import uuid
import spacy
import re
from rapidfuzz import fuzz

class RestaurantCreateView(generics.CreateAPIView):
    serializer_class = RestaurantRequestSerializer
    queryset = RestaurantRequest.objects.all()
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        payload = request.data

        user_id = payload.get('user_id')

        # Check if a pending/approved request already exists
        if RestaurantRequest.objects.filter(user_id=user_id).exclude(status='rejected').exists():
            return Response({"message": "A restaurant request is already in progress or approved."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create a RestaurantRequest instance (status will default to 'pending')
        image = payload.get('image')
        name = payload.get('name')
        email = payload.get('email')
        description = payload.get('description')
        mobile = payload.get('mobile')
        latitude = payload.get('latitude')
        longitude = payload.get('longitude')

        RestaurantRequest.objects.create(
            image=image,
            name=name,
            email=email,
            description=description,
            contact_no=mobile,
            user_id=user_id,
            latitude=latitude,
            longitude=longitude
        )

        return Response({"message": "Restaurant request submitted for approval."},
                        status=status.HTTP_201_CREATED)

   

class NearbyRestaurants(APIView):

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        # Radius of the Earth in kilometers
        R = 6371.0  # Radius of the Earth in kilometers
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        # print(lat1, lon1, lat2, lon2)
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
        print ("Distance:-----------",distance)
        return distance

    def get(self, request):
        # Get user's current location from the database (assuming user's location is saved during registration)
        user = request.user
        print("User",user)
        # user=User.objects.get(email="wetucecoh@mailinator.com")
        user_latitude = user.latitude
        user_longitude=user.longitude  # Replace with your user model fields
        print("user_latitude",user_latitude)
        print("user_longitude",user_longitude)
        nearby_restaurants = []
        radius_km = 5  # Define the search radius in kilometers

        # Get all restaurants from the database
        restaurants = Restaurant.objects.all()
        print(restaurants)
        # Loop through all restaurants and calculate the distance using Haversine formula
        for restaurant in restaurants:
            restaurant_location = (restaurant.latitude, restaurant.longitude)
            print(restaurant_location)
            distance = self.haversine_distance(user_latitude, user_longitude, restaurant.latitude, restaurant.longitude)

            # Check if the restaurant is within the 5 km radius
            if distance <= radius_km:
                nearby_restaurants.append(restaurant)
        print(nearby_restaurants)
        # Serialize the filtered restaurants
        serializer = RestaurantCreateSerializer(nearby_restaurants, many=True)
        return Response(serializer.data)




class DashboardStatAPIView(generics.ListAPIView):
    serializer_class=SummarySerializer
    permission_classes=[AllowAny]
    def get_queryset(self):
        restaurant_id=self.kwargs['restaurant_id']
        restaurant=Restaurant.objects.get(id=restaurant_id)

        dish_count=Dish.objects.filter(restaurant=restaurant).count()
        order_count=CartOrder.objects.filter(restaurant=restaurant).count()
        # foriegn key
        revenue=CartOrderItem.objects.filter(restaurant=restaurant).aggregate(total_revenue=models.Sum(models.F('sub_total')))['total_revenue'] or 0


        return [{
            'dishes':dish_count,
            'orders':order_count,
            'revenue':revenue,
        }]
    

    def list(self,*args, **kwargs):
        queryset=self.get_queryset()
        serializer=self.get_serializer(queryset,many=True)
        return Response(serializer.data)


class DishAPIView(generics.ListAPIView):
    serializer_class=DishSerializer
    permission_classes=[AllowAny]

    def get_queryset(self):
        restaurant_id=self.kwargs['restaurant_id']
        restaurant=Restaurant.objects.get(id=restaurant_id)
        print(Dish.objects.filter(restaurant=restaurant).order_by('-id'))
        return Dish.objects.filter(restaurant=restaurant).order_by('-id')
    

class OrderAPIView(generics.ListAPIView):
    serializer_class=CartOrderSerializer
    permission_classes=[AllowAny]

    def get_queryset(self):
        restaurant_id=self.kwargs['restaurant_id']
        restaurant=Restaurant.objects.get(id=restaurant_id)
        return CartOrder.objects.filter(restaurant=restaurant).order_by('-id')



class OrderDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = CartOrderSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        restaurant_id = self.kwargs['restaurant_id']
        order_id = self.kwargs['order_id']
        restaurant = Restaurant.objects.get(id=restaurant_id)
        return CartOrder.objects.get(restaurant=restaurant, oid=order_id)

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        prev_status = order.order_status  # Save previous status
        new_status = request.data.get("order_status")

        # If status changes to 'fulfilled', generate token and send emails
        if new_status == 'fulfilled' and prev_status != 'fulfilled':
            
                order.tracking_token = uuid.uuid4()
                order.save()

                # Create tracking URL
                # tracking_url = f"https://bitebox.live/rider/tracking/{order.oid}/{order.tracking_token}/"
                tracking_url = f"http://bitebox.live/rider/tracking/{order.oid}/{order.tracking_token}/"

                # Get all active delivery boys
                restaurant = order.restaurant.first()  # Assuming one restaurant per order
                delivery_boys = restaurant.delivery_boys.filter(status='available')
                print("gggggggggggggggggggggggggggg")
                for boy in delivery_boys:
                    if boy.email:
                        send_tracking_email(boy.email, tracking_url, order.oid)

        # Proceed with default update
        return super().update(request, *args, **kwargs)
    
class RevenueAPIView(generics.ListAPIView):
    serializer_class=CartOrderItemSerializer
    permission_classes=[AllowAny]


    def get_queryset(self):
        restaurant_id=self.kwargs['restaurant_id']
        restaurant=Restaurant.objects.get(id=restaurant_id)
        return CartOrderItem.objects.filter(restaurant=restaurant,order__payment_status="paid").aggregate(total_revenue=models.Sum(models.F('sub_total')))['total_revenue'] or 0
    




class ReviewListAPIView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']
        dish = Dish.objects.get(id=dish_id)
        return Review.objects.filter(dish=dish)


    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        print("------------------",request.user)
    # Get user ID from token if authenticated
        user_id = request.user.id if request.user.is_authenticated else None

    # Check if user has reviewed
        has_reviewed = False
        if user_id:
            has_reviewed = queryset.filter(user_id=user_id).exists()

        return Response({
        "reviews": serializer.data,
        "has_reviewed": has_reviewed
        })
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)

        user = request.user
        dish_id = request.data.get('dish_id')
        rating = request.data.get('rating')
        review_text = request.data.get('review')

        try:
            dish = Dish.objects.get(id=dish_id)

            existing_review = Review.objects.filter(user=user, dish=dish).first()
            if existing_review:
                return Response({"error": "You have already submitted a review for this dish."}, status=400)

            Review.objects.create(
                user=user,
                dish=dish,
                rating=rating,
                review=review_text
            )
            return Response({"message": "Review Created Successfully"}, status=201)
        except Dish.DoesNotExist:
            return Response({"error": "Dish not found."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class CouponListAPIView(generics.ListAPIView):
    serializer_class=CouponSerializer
    permission_classes=[AllowAny]

    
    def get_queryset(self):
        restaurant_id=self.kwargs['restaurant_id']
        restaurant=Restaurant.objects.get(id=restaurant_id)

        return Coupon.objects.filter(restaurant=restaurant)

    def create(self,request,*args, **kwargs):
        payload=request.data
        restaurant_id=payload['restaurant_id']
        code=payload['code']
        discount=payload['discount']
        active=payload['active']

        restaurant=Restaurant.objects.get(id=restaurant_id)
        Coupon.objects.create(
            restaurant=restaurant,
            code=code,
            discount=discount,
            active=(active.lower()=='true')

        )
        return Response({"message":"Coupon created successfully"},status=status.HTTP_201_CREATED)
    

class CouponDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class=CouponSerializer
    permission_classes=[AllowAny]

    def get_object(self):
        restaurant_id=self.kwargs['restaurant_id']
        coupon_id=self.kwargs['coupon_id']

        restaurant=Restaurant.objects.get(id=restaurant_id)
        return Coupon.objects.get(restaurant=restaurant,id=coupon_id)
    
class CouponStatAPIView(generics.ListAPIView):
    serializer_class=CouponSerializer
    permission_classes=[AllowAny]

    def get_object(self):
        restaurant_id=self.kwargs['restaurant_id']
        restaurant=Restaurant.objects.get(id=restaurant_id)

        total_coupons=Coupon.objects.filter(
            restaurant=restaurant
        ).count()
        active_coupons=Coupon.objects.filter(restaurant=restaurant,active=True).count()
        return [{
            'total_coupons':total_coupons,
            'active_coupons':active_coupons,

        }]


    def list(self,*args, **kwargs):
        queryset=self.get_queryset()
        serializer=self.get_serializer(queryset,many=True)
        return Response(serializer.data)
    

class NotificationAPIView(generics.ListAPIView):
    serializer_class=NotificationSerializer
    permission_classes=[AllowAny]

    def get_queryset(self):
        restaurant_id=self.kwargs['restaurant_id']
        restaurant=Restaurant.objects.get(id=restaurant_id)
        return Notification.objects.filter(restaurant=restaurant,seen=False).order_by('-id')
    


class NotificationseenAPIView(generics.ListAPIView):
    serializer_class=NotificationSerializer
    permission_classes=[AllowAny]

    def get_queryset(self):
        restaurant_id=self.kwargs['restaurant_id']
        restaurant=Restaurant.objects.get(id=restaurant_id)
        return Notification.objects.filter(restaurant=restaurant,seen=True).order_by('-id')
    


class NotificationSummaryAPIView(generics.ListAPIView):
    serializer_class=NotificationSummarySerializer
    permission_classes=[AllowAny]

    def get_queryset(self):
        restaurant_id=self.kwargs['restaurant_id']
        restaurant=Restaurant.objects.get(id=restaurant_id)

        unread_notification=Notification.objects.filter(restaurant=restaurant,seen=False).count()
        read_notification=Notification.objects.filter(restaurant=restaurant,seen=True).count()
        all_notification=Notification.objects.filter(restaurant=restaurant).count()

        return[{
            'unread_notifications':unread_notification,
            'read_notifications':read_notification,
            'all_notifications':all_notification,
        }]
    
    def list(self,*args, **kwargs):
        queryset=self.get_queryset()
        serializer=self.get_serializer(queryset,many=True)
        return Response(serializer.data)


class NotificationRestaurantMarkAsSeenAPIView(generics.RetrieveAPIView):
    serializer_class=NotificationSerializer
    permission_classes=[AllowAny]

    def get_object(self):
        restaurant_id=self.kwargs['restaurant_id']
        notification_id=self.kwargs['notification_id']

        restaurant=Restaurant.objects.get(id=restaurant_id)
        notification=Notification.objects.get(restaurant=restaurant,id=notification_id)

        notification.seen = True
        notification.save()

        return notification
    


# class RestaurantOwnerProfileUpdateAPIView(generics.RetrieveUpdateAPIView):
#     queryset=Profile.objects.all()
#     serializer_class=ProfileSerializer
#     permission_classes=[AllowAny]

class RestaurantOwnerProfileUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs['user_id']
        user = User.objects.get(id=user_id)
        return Profile.objects.get(user=user)



class RestaurantUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset=Restaurant.objects.all()
    serializer_class=RestaurantSerializer
    permission_classes=[AllowAny]


class RestaurantAPIView(generics.RetrieveUpdateAPIView):
    serializer_class=RestaurantSerializer
    permission_classes=[AllowAny]

    def get_object(self):
        restaurant_slug=self.kwargs['restaurant_slug']
        return Restaurant.objects.get(slug=restaurant_slug)
    

class RestaurantDishAPIView(generics.ListAPIView):
    serializer_class=DishSerializer
    permission_classes=[AllowAny]
    # lookup_field = "slug"
    # def get_object(self):
    def get_queryset(self):
        restaurant_slug=self.kwargs['restaurant_slug']
        restaurant=Restaurant.objects.get(slug=restaurant_slug)
        
        return Dish.objects.filter(restaurant=restaurant)


class DishCreateAPIView(generics.CreateAPIView):
    queryset=Dish.objects.all()
    serializer_class=DishSerializer


    @transaction.atomic
    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # dish_instance=serializer.instance
        # specification_data=[]
        # level_data=[]
        # size_data=[]
        # gallery_data=[]
        
        # for key,value in self.request.data.item():
        #     if key.startwith('specifications') and ['title'] in key:
        #         index=key.split('[')[1].split(']')[0]
        #         title=value
        #         content_key=f'specifications[{index}][content]'
        #         content=self.request.data.get(content_key)
        #         specification_data.append({'title':title,'content':content})

        #     elif key.startwith('spiceLevel') and ['level_name'] in key:
        #         index=key.split('[')[1].split(']')[0]
        #         level_name=value
        #         additional_price_key=f'spiceLevel[{index}][additional_price]'
        #         additional_price=self.request.data.get(additional_price_key)
        #         level_data.append({'level_name':level_name,'additional_price':additional_price})
            
        #     elif key.startwith('sizes') and ['name'] in key:
        #         index=key.split('[')[1].split(']')[0]
        #         name=value
        #         price_key=f'sizes[{index}][price]'
        #         price=self.request.data.get(price_key)
        #         size_data.append({'name':name,'price':price})
            
        #     elif key.startwith('gallery') and ['image'] in key:
        #         index=key.split('[')[1].split(']')[0]
        #         image=value
        #         gallery_data.append({'image':image})

        dish_instance = serializer.instance
        specification_data = []
        level_data = []
        size_data = []
        gallery_data = []

        for key, value in self.request.data.items():  # ✅ Fix items() method
            if key.startswith('specifications') and 'title' in key:  # ✅ Fix startswith() and key checking
                index = key.split('[')[1].split(']')[0]
                title = value
                content_key = f'specifications[{index}][content]'
                content = self.request.data.get(content_key)
                specification_data.append({'title': title, 'content': content})

            elif key.startswith('spiceLevel') and 'level_name' in key:
                index = key.split('[')[1].split(']')[0]
                level_name = value
                additional_price_key = f'spiceLevel[{index}][additional_price]'
                additional_price = self.request.data.get(additional_price_key)
                level_data.append({'level_name': level_name, 'additional_price': additional_price})

            elif key.startswith('sizes') and 'size_name' in key:
                index = key.split('[')[1].split(']')[0]
                size_name = value
                price_key = f'sizes[{index}][price]'
                price = self.request.data.get(price_key)
                size_data.append({'size_name': size_name, 'price': price})

            elif key.startswith('gallery') and 'image' in key:
                index = key.split('[')[1].split(']')[0]
                image = value
                gallery_data.append({'image': image})  # ✅ Remove the extra comma

        
        print('specifications',specification_data)
        print('levels',level_data)
        print('sizes',size_data)
        print('gallery',gallery_data)
        self.save_nested_data(dish_instance,SpecificationSerializer,specification_data)
        self.save_nested_data(dish_instance,SpiceLevelSerializer,level_data)
        self.save_nested_data(dish_instance,PortionSizeSerializer,size_data)
        self.save_nested_data(dish_instance,GallerySerializer,gallery_data)
        # return super().perform_create(serializer)

    def save_nested_data(self,dish_instance,serializer_class,data):
            serializer=serializer_class(data=data,many=True,context={'dish_instance':dish_instance})
            serializer.is_valid(raise_exception=True)
            serializer.save(dish=dish_instance)


class DishDeleteAPIView(generics.DestroyAPIView):
    queryset = Dish.objects.all()
    serializer_class = DishSerializer
    permission_classes = (AllowAny, )

    def get_object(self):
        restaurant_id = self.kwargs['restaurant_id']
        dish_did = self.kwargs['dish_did']

        restaurant = Restaurant.objects.get(id=restaurant_id)
        dish = Dish.objects.get(restaurant=restaurant, did=dish_did)
        return dish



class DishUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset=Dish.objects.all()
    serializer_class=DishSerializer
    

    def get_object(self):
        restaurant_id = self.kwargs['restaurant_id']
        dish_did = self.kwargs['dish_did']

        restaurant = Restaurant.objects.get(id=restaurant_id)
        dish = Dish.objects.get(restaurant=restaurant, did=dish_did)
        return dish



    @transaction.atomic
    def update(self,request,*args, **kwargs ):
       
        dish = self.get_object()
        serializer=self.get_serializer(dish,data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        dish.specification().delete()
        dish.spice_level().delete()
        dish.portion_size().delete()
        dish.gallery().delete()



        specification_data = []
        level_data = []
        size_data = []
        gallery_data = []

        for key, value in self.request.data.items():  # ✅ Fix items() method
            if key.startswith('specifications') and 'title' in key:  # ✅ Fix startswith() and key checking
                index = key.split('[')[1].split(']')[0]
                title = value
                content_key = f'specifications[{index}][content]'
                content = self.request.data.get(content_key)
                specification_data.append({'title': title, 'content': content})

            elif key.startswith('spiceLevel') and 'level_name' in key:
                index = key.split('[')[1].split(']')[0]
                level_name = value
                additional_price_key = f'spiceLevel[{index}][additional_price]'
                additional_price = self.request.data.get(additional_price_key)
                level_data.append({'level_name': level_name, 'additional_price': additional_price})

            elif key.startswith('sizes') and 'size_name' in key:
                index = key.split('[')[1].split(']')[0]
                size_name = value
                price_key = f'sizes[{index}][price]'
                price = self.request.data.get(price_key)
                size_data.append({'size_name': size_name, 'price': price})

            elif key.startswith('gallery') and 'image' in key:
                index = key.split('[')[1].split(']')[0]
                image = value
                gallery_data.append({'image': image})  # ✅ Remove the extra comma

        
        print('specifications',specification_data)
        print('levels',level_data)
        print('sizes',size_data)
        print('gallery',gallery_data)
        self.save_nested_data(dish,SpecificationSerializer,specification_data)
        self.save_nested_data(dish,SpiceLevelSerializer,level_data)
        self.save_nested_data(dish,PortionSizeSerializer,size_data)
        self.save_nested_data(dish,GallerySerializer,gallery_data)
        # return super().perform_create(serializer)
        return Response({'message': 'Product Updated'}, status=status.HTTP_200_OK)

    def save_nested_data(self,dish_instance,serializer_class,data):
            serializer=serializer_class(data=data,many=True,context={'dish_instance':dish_instance})
            serializer.is_valid(raise_exception=True)
            serializer.save(dish=dish_instance)



class Earning(generics.ListAPIView):
    serializer_class = EarningSummarySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        restaurant_id = self.kwargs['restaurant_id']
        restaurant = Restaurant.objects.get(id=restaurant_id)

     
        revenue_expr = ExpressionWrapper(
            F('sub_total'),
            output_field=DecimalField()
        )

        one_month_ago = datetime.today() - timedelta(days=28)

        # Monthly revenue from last 28 days
        monthly_revenue = CartOrderItem.objects.filter(
            restaurant=restaurant,
            date__gte=one_month_ago
        ).aggregate(
            total_revenue=Sum(revenue_expr)
        )['total_revenue'] or 0

        # Total revenue from all paid orders
        total_revenue = CartOrderItem.objects.filter(
            restaurant=restaurant,
            
        ).aggregate(
            total_revenue=Sum(revenue_expr)
        )['total_revenue'] or 0

        return [{
            'monthly_revenue': monthly_revenue,
            'total_revenue': total_revenue,
        }]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@api_view(('GET',))
def MonthlyEarningTracker(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    monthly_earning_tracker = (
        CartOrderItem.objects
        .filter(restaurant=restaurant)
        .annotate(
            month=ExtractMonth("date")
        )
        .values("month")
        .annotate(
            sales_count=models.Sum("qty"),
            total_earning=models.Sum(
                models.F('sub_total'))
        )
        .order_by("-month")
    )
    return Response(monthly_earning_tracker)

class DeliveryBoyListCreateView(generics.ListCreateAPIView):
    # queryset = DeliveryBoy.objects.all()
    serializer_class = DeliveryBoySerializer
    permission_classes=[AllowAny]
    

    def get_queryset(self):
        restaurant_id = self.kwargs['restaurant_id']
        return DeliveryBoy.objects.filter(restaurant_id=restaurant_id)

    def perform_create(self, serializer):
        restaurant_id = self.kwargs['restaurant_id']
        serializer.save(restaurant_id=restaurant_id)
        


# views.py
class DeliveryBoyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DeliveryBoySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        restaurant_id = self.kwargs['restaurant_id']
        return DeliveryBoy.objects.filter(restaurant_id=restaurant_id)

    

class RestaurantReviewListAPIView(generics.ListAPIView):
    serializer_class=ReviewSerializer
    permission_classes=[AllowAny]

    def get_queryset(self):
        restaurant_id=self.kwargs['restaurant_id']
        restaurant=Restaurant.objects.get(id=restaurant_id)
        return Review.objects.filter(dish__restaurant=restaurant)
    

class ReviewDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class=ReviewSerializer
    permission_classes=[AllowAny]

    def get_object(self):
        restaurant_id=self.kwargs['restaurant_id']
        review_id=self.kwargs['review_id']

        restaurant=Restaurant.objects.get(id=restaurant_id)
        review=Review.objects.get(id=review_id,dish__restaurant=restaurant)


        return review




# class VoiceOrderView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         command = request.data.get('command', '')
#         latitude = request.data.get('latitude')
#         longitude = request.data.get('longitude')

#         if not command:
#             return Response({'error': 'No voice input provided'}, status=status.HTTP_400_BAD_REQUEST)
#         if not latitude or not longitude:
#             return Response({'error': 'Latitude and longitude are required.'}, status=400)

#         user_lat = float(latitude)
#         user_lon = float(longitude)

#         doc = nlp(command.lower())

#         nearby_restaurants = self.get_nearby_restaurants(user_lat, user_lon, radius_km=5)
#         nearby_restaurant_ids = [r.id for r in nearby_restaurants]
#         print("Nearby Restaurant IDs:", nearby_restaurant_ids)
#         matched_dishes = []
#         dishes = Dish.objects.filter(restaurant_id__in=nearby_restaurant_ids)
#         print("Matched Dishes:", dishes)
#         for dish in dishes:
#             similarity = fuzz.partial_ratio(dish.title.lower(), command.lower())
#             if similarity >= 70:  # threshold, can be tuned
#                 quantity = self.extract_quantity(command, dish.title)
#                 matched_dishes.append({
#                     'id': dish.id,
#                     'title': dish.title,
#                     'price': dish.price,
#                     'quantity': quantity,
#                     'restaurant': dish.restaurant.name,
#                     'restaurant_': dish.restaurant.name,
#                     'match_score': similarity  # optional for debugging
#                 })

#         return Response({'order_items': matched_dishes}, status=status.HTTP_200_OK)

#     def get_nearby_restaurants(self, user_lat, user_lon, radius_km=5):
#         restaurants = Restaurant.objects.all()
#         nearby = []
#         for restaurant in restaurants:
#             distance = self.haversine_distance(user_lat, user_lon, restaurant.latitude, restaurant.longitude)
#             if distance <= radius_km:
#                 nearby.append(restaurant)
#         return nearby

#     def haversine_distance(self, lat1, lon1, lat2, lon2):
#         R = 6371.0
#         lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
#         dlat = lat2 - lat1
#         dlon = lon2 - lon1
#         a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
#         c = 2 * atan2(sqrt(a), sqrt(1 - a))
#         return R * c

#     def extract_quantity(self, text, dish_name):
#         text = text.lower()
#         numbers_map = {
#             "one": 1, "two": 2, "three": 3, "four": 4,
#             "five": 5, "six": 6, "seven": 7, "eight": 8,
#             "nine": 9, "ten": 10
#         }

#         for word, number in numbers_map.items():
#             if f"{word} {dish_name}" in text:
#                 return number

#         digit_match = re.search(r'(\d+)\s+' + re.escape(dish_name), text)
#         if digit_match:
#             return int(digit_match.group(1))

#         return 1


nlp = spacy.load("en_core_web_sm")

# class VoiceOrderView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         command = request.data.get('command', '')
#         latitude = request.data.get('latitude')
#         longitude = request.data.get('longitude')

#         if not command or not latitude or not longitude:
#             return Response({'error': 'Missing voice input or location.'}, status=400)

#         command = command.lower()
#         user_lat = float(latitude)
#         user_lon = float(longitude)

#         # Extract dish and restaurant name from command
#         dish_name, restaurant_name = self.extract_entities(command)
#         print("Restaurant Name:", restaurant_name)
#         print("Dish Name:", dish_name)

#         # Case: Restaurant is specified
#         if restaurant_name:
#             matched_restaurant = self.find_best_match_restaurant(restaurant_name)
#             if not matched_restaurant:
#                 return Response({'error': f"Could not find restaurant named '{restaurant_name}'."}, status=404)

#             distance = self.haversine_distance(user_lat, user_lon, matched_restaurant.latitude, matched_restaurant.longitude)
#             if distance > 5:
#                 return Response({'error': f"'{matched_restaurant.name}' is too far ({distance:.1f} km)."}, status=400)

#             dish = self.find_best_match_dish(dish_name, matched_restaurant.id)
#             if not dish:
#                 return Response({'error': f"'{dish_name}' is not available at '{matched_restaurant.name}'."}, status=404)

#             quantity = self.extract_quantity(command, dish.title)
#             return Response({
#                 'order_items': [{
#                     'id': dish.id,
#                     'title': dish.title,
#                     'price': dish.price,
#                     'quantity': quantity,
#                     'restaurant': matched_restaurant.name
#                 }]
#             }, status=200)

#         # Case: No restaurant specified — search nearby
#         else:
#             nearby_restaurants = self.get_nearby_restaurants(user_lat, user_lon, radius_km=5)
#             nearby_ids = [r.id for r in nearby_restaurants]

#             if not nearby_ids:
#                 return Response({'error': 'No nearby restaurants found within 5 km.'}, status=404)

#             for restaurant in nearby_restaurants:
#                 dish = self.find_best_match_dish(dish_name, restaurant.id)
#                 if dish:
#                     quantity = self.extract_quantity(command, dish.title)
#                     return Response({
#                         'order_items': [{
#                             'id': dish.id,
#                             'title': dish.title,
#                             'price': dish.price,
#                             'quantity': quantity,
#                             'restaurant': restaurant.name
#                         }]
#                     }, status=200)

#             return Response({'error': f"'{dish_name}' not available at any nearby restaurant."}, status=404)

#     def extract_entities(self, text):
#         text = text.lower()
#         all_restaurants = Restaurant.objects.values_list('name', flat=True)

#         matched_restaurant = None
#         matched_restaurant_text = ''

#         for restaurant_name in all_restaurants:
#             if restaurant_name.lower() in text:
#                 matched_restaurant = restaurant_name
#                 matched_restaurant_text = restaurant_name.lower()
#                 break

#     # Remove restaurant name from text to isolate dish name
#         cleaned_text = text.replace(matched_restaurant_text, '') if matched_restaurant_text else text
#         cleaned_text = cleaned_text.replace("from", "").replace("at", "").strip()

#     # Dish name is whatever is left
#         dish_name = cleaned_text.strip()

#         return dish_name, matched_restaurant

#     def find_best_match_restaurant(self, restaurant_name):
#         all_restaurants = Restaurant.objects.all()
#         best_match = None
#         best_score = 0
#         for restaurant in all_restaurants:
#             score = fuzz.partial_ratio(restaurant_name, restaurant.name.lower())
#             if score > best_score and score >= 70:
#                 best_score = score
#                 best_match = restaurant
#         return best_match

#     def find_best_match_dish(self, dish_name, restaurant_id):
#         dishes = Dish.objects.filter(restaurant_id=restaurant_id)
#         best_match = None
#         best_score = 0
#         for dish in dishes:
#             score = fuzz.partial_ratio(dish_name, dish.title.lower())
#             if score > best_score and score >= 65:
#                 best_score = score
#                 best_match = dish
#         return best_match

#     def get_nearby_restaurants(self, user_lat, user_lon, radius_km=5):
#         return [
#             restaurant for restaurant in Restaurant.objects.all()
#             if self.haversine_distance(user_lat, user_lon, restaurant.latitude, restaurant.longitude) <= radius_km
#         ]

#     def haversine_distance(self, lat1, lon1, lat2, lon2):
#         R = 6371.0
#         lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
#         dlat = lat2 - lat1
#         dlon = lon2 - lon1
#         a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
#         c = 2 * atan2(sqrt(a), sqrt(1 - a))
#         return R * c

#     def extract_quantity(self, text, dish_name):
#         text = text.lower()
#         numbers_map = {
#             "one": 1, "two": 2, "three": 3, "four": 4,
#             "five": 5, "six": 6, "seven": 7, "eight": 8,
#             "nine": 9, "ten": 10
#         }

#         for word, number in numbers_map.items():
#             if f"{word} {dish_name}" in text:
#                 return number

#         digit_match = re.search(r'(\d+)\s+' + re.escape(dish_name), text)
#         if digit_match:
#             return int(digit_match.group(1))

#         return 1

# class VoiceOrderView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         command = request.data.get('command', '')
#         latitude = request.data.get('latitude')
#         longitude = request.data.get('longitude')

#         if not command or not latitude or not longitude:
#             return Response({'error': 'Missing voice input or location.'}, status=400)

#         command = command.lower()
#         user_lat = float(latitude)
#         user_lon = float(longitude)

#         # Extract dish and restaurant name from command
#         dish_name, restaurant_name = self.extract_entities(command)
#         print("Restaurant Name:", restaurant_name)
#         print("Dish Name:", dish_name)

#         # Case: Restaurant is specified
#         if restaurant_name:
#             matched_restaurant = self.find_best_match_restaurant(restaurant_name)
#             if not matched_restaurant:
#                 return Response({'error': f"Could not find restaurant named '{restaurant_name}'."}, status=404)

#             distance = self.haversine_distance(user_lat, user_lon, matched_restaurant.latitude, matched_restaurant.longitude)

#             dish = self.find_best_match_dish(dish_name, matched_restaurant.id)

#             if distance > 5:
#                 if dish:
#                     return Response({
#                         'error': f"'{matched_restaurant.name}' is too far ({distance:.1f} km), but the dish '{dish.title}' is available there."
#                     }, status=400)
#                 else:
#                     return Response({
#                         'error': f"'{matched_restaurant.name}' is too far ({distance:.1f} km) and does not have '{dish_name}'."
#                     }, status=400)

#             if not dish:
#                 return Response({'error': f"'{dish_name}' is not available at '{matched_restaurant.name}'."}, status=404)

#             quantity = self.extract_quantity(command, dish.title)
#             return Response({
#                 'order_items': [{
#                 'id': dish.id,
#                 'title': dish.title,
#                 'price': dish.price,
#                 'quantity': quantity,
#                 'restaurant': matched_restaurant.name
#             }]
#         }, status=200)

#     # Case: No restaurant specified — search nearby
#         else:
#             nearby_restaurants = self.get_nearby_restaurants(user_lat, user_lon, radius_km=5)
#             nearby_ids = [r.id for r in nearby_restaurants]

#             if not nearby_ids:
#                 return Response({'error': 'No nearby restaurants found within 5 km.'}, status=404)

#             for restaurant in nearby_restaurants:
#                 dish = self.find_best_match_dish(dish_name, restaurant.id)
#                 if dish:
#                     quantity = self.extract_quantity(command, dish.title)
#                     return Response({
#                         'order_items': [{
#                         'id': dish.id,
#                         'title': dish.title,
#                         'price': dish.price,
#                         'quantity': quantity,
#                         'restaurant': restaurant.name
#                     }]
#                     }, status=200)

#             return Response({'error': f"'{dish_name}' not available at any nearby restaurant."}, status=404)


#     def extract_entities(self, text):
#         text = text.lower()
#         all_restaurants = Restaurant.objects.values_list('name', flat=True)

#         matched_restaurant = None
#         matched_restaurant_text = ''

#         for restaurant_name in all_restaurants:
#             if restaurant_name.lower() in text:
#                 matched_restaurant = restaurant_name
#                 matched_restaurant_text = restaurant_name.lower()
#                 break

#     # Remove restaurant name from text to isolate dish name
#         cleaned_text = text.replace(matched_restaurant_text, '') if matched_restaurant_text else text
#         cleaned_text = cleaned_text.replace("from", "").replace("at", "").strip()

#     # Dish name is whatever is left
#         dish_name = cleaned_text.strip()

#         return dish_name, matched_restaurant

#     def find_best_match_restaurant(self, restaurant_name):
#         all_restaurants = Restaurant.objects.all()
#         best_match = None
#         best_score = 0
#         for restaurant in all_restaurants:
#             score = fuzz.partial_ratio(restaurant_name, restaurant.name.lower())
#             if score > best_score and score >= 70:
#                 best_score = score
#                 best_match = restaurant
#         return best_match

#     def find_best_match_dish(self, dish_name, restaurant_id):
#         dishes = Dish.objects.filter(restaurant_id=restaurant_id)
#         best_match = None
#         best_score = 0
#         for dish in dishes:
#             score = fuzz.partial_ratio(dish_name, dish.title.lower())
#             if score > best_score and score >= 65:
#                 best_score = score
#                 best_match = dish
#         return best_match

#     def get_nearby_restaurants(self, user_lat, user_lon, radius_km=5):
#         return [
#             restaurant for restaurant in Restaurant.objects.all()
#             if self.haversine_distance(user_lat, user_lon, restaurant.latitude, restaurant.longitude) <= radius_km
#         ]

#     def haversine_distance(self, lat1, lon1, lat2, lon2):
#         R = 6371.0
#         lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
#         dlat = lat2 - lat1
#         dlon = lon2 - lon1
#         a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
#         c = 2 * atan2(sqrt(a), sqrt(1 - a))
#         return R * c

#     def extract_quantity(self, text, dish_name):
#         text = text.lower()
#         numbers_map = {
#             "one": 1, "two": 2, "three": 3, "four": 4,
#             "five": 5, "six": 6, "seven": 7, "eight": 8,
#             "nine": 9, "ten": 10
#         }

#         for word, number in numbers_map.items():
#             if f"{word} {dish_name}" in text:
#                 return number

#         digit_match = re.search(r'(\d+)\s+' + re.escape(dish_name), text)
#         if digit_match:
#             return int(digit_match.group(1))

#         return 1



class VoiceOrderView(APIView):
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    def post(self, request):
        command = request.data.get('command', '')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if not command or not latitude or not longitude:
            return Response({'error': 'Missing voice input or location.'}, status=400)

        command = command.lower()
        user_lat = float(latitude)
        user_lon = float(longitude)

        dish_name, restaurant_name = self.extract_entities(command)
        spice_level = self.extract_spice_level(command)
        portion_size = self.extract_portion_size(command)

        if restaurant_name:
            matched_restaurant = self.find_best_match_restaurant(restaurant_name)
            if not matched_restaurant:
                return Response({'error': f"Could not find restaurant named '{restaurant_name}'."}, status=404)

            distance = self.haversine_distance(user_lat, user_lon, matched_restaurant.latitude, matched_restaurant.longitude)
            dish = self.find_best_match_dish(dish_name, matched_restaurant.id)

            if distance > 5:
                if dish:
                    return Response({'error': f"'{matched_restaurant.name}' is too far ({distance:.1f} km), but the dish '{dish.title}' is available there."}, status=400)
                return Response({'error': f"'{matched_restaurant.name}' is too far and does not have '{dish_name}'."}, status=400)

            if not dish:
                return Response({'error': f"'{dish_name}' is not available at '{matched_restaurant.name}'."}, status=404)

            return self.validate_and_respond(dish, matched_restaurant.name, spice_level, portion_size, command)

        else:
            nearby_restaurants = self.get_nearby_restaurants(user_lat, user_lon, radius_km=5)
            if not nearby_restaurants:
                return Response({'error': 'No nearby restaurants found within 5 km.'}, status=404)

            for restaurant in nearby_restaurants:
                dish = self.find_best_match_dish(dish_name, restaurant.id)
                if dish:
                    return self.validate_and_respond(dish, restaurant.name, spice_level, portion_size, command)

            return Response({'error': f"'{dish_name}' not available at any nearby restaurant."}, status=404)

    def validate_and_respond(self, dish, restaurant_name, spice_level, portion_size, command):
        quantity = self.extract_quantity(command, dish.title)
        base_price = dish.price
        final_price = base_price

        # Validate and calculate portion price
        if portion_size:
            portion = PortionSize.objects.filter(dish=dish, size_name__iexact=portion_size).first()
            if not portion:
                return Response({'error': f"Portion size '{portion_size}' is not available for '{dish.title}'."}, status=400)
            final_price += portion.price or 0
        else:
            portion = None

        # Validate spice level
        if spice_level:
            spice = SpiceLevel.objects.filter(dish=dish, level_name__iexact=spice_level).first()
            if not spice:
                return Response({'error': f"Spice level '{spice_level}' is not available for '{dish.title}'."}, status=400)
        else:
            spice = None

        return Response({
            'order_items': [{
                'id': dish.id,
                'title': dish.title,
                'base_price': str(base_price),
                'final_price': str(final_price * quantity),
                'quantity': quantity,
                'restaurant': restaurant_name,
                'spice_level': spice_level or None,
                'portion_size': portion_size or None
            }]
        }, status=200)

    def extract_entities(self, text):
        text = text.lower()
        all_restaurants = Restaurant.objects.values_list('name', flat=True)
        matched_restaurant = None
        matched_restaurant_text = ''

        for restaurant_name in all_restaurants:
            if restaurant_name.lower() in text:
                matched_restaurant = restaurant_name
                matched_restaurant_text = restaurant_name.lower()
                break

        cleaned_text = text.replace(matched_restaurant_text, '') if matched_restaurant_text else text
        cleaned_text = cleaned_text.replace("from", "").replace("at", "").strip()
        dish_name = cleaned_text.strip()

        return dish_name, matched_restaurant

    def extract_spice_level(self, text):
        levels = ['mild', 'spicy', 'hot', 'extra hot']
        for level in levels:
            if level in text:
                return level
        return None

    def extract_portion_size(self, text):
        sizes = ['small', 'medium', 'large', 'extra large']
        for size in sizes:
            if size in text:
                return size
        return None

    def extract_quantity(self, text, dish_name):
        text = text.lower()
        numbers_map = {
            "one": 1, "two": 2, "three": 3, "four": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8,
            "nine": 9, "ten": 10
        }

        for word, number in numbers_map.items():
            # if f"{word} {dish_name}" in text:
            if f"{number} quantity" in text or f"{number} quantities" in text:
                return number

        digit_match = re.search(r'(\d+)\s+' + re.escape(dish_name), text)
        if digit_match:
            return int(digit_match.group(1))

        return 1

    def find_best_match_restaurant(self, restaurant_name):
        best_score = 0
        best_match = None
        for restaurant in Restaurant.objects.all():
            score = fuzz.partial_ratio(restaurant_name.lower(), restaurant.name.lower())
            if score > best_score and score >= 70:
                best_score = score
                best_match = restaurant
        return best_match

    def find_best_match_dish(self, dish_name, restaurant_id):
        best_score = 0
        best_match = None
        for dish in Dish.objects.filter(restaurant_id=restaurant_id):
            score = fuzz.partial_ratio(dish_name.lower(), dish.title.lower())
            if score > best_score and score >= 65:
                best_score = score
                best_match = dish
        return best_match

    def get_nearby_restaurants(self, user_lat, user_lon, radius_km=5):
        return [
            restaurant for restaurant in Restaurant.objects.all()
            if self.haversine_distance(user_lat, user_lon, restaurant.latitude, restaurant.longitude) <= radius_km
        ]

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c


@api_view(["POST"])
@permission_classes([AllowAny])
def weather_based_nearby_dishes(request):
    user = request.user
    temperature = request.data.get("temperature")
    condition = request.data.get("condition", "").lower()

    if not user.is_authenticated:
        return Response({"error": "Authentication required"}, status=401)

    if temperature is None or condition == "":
        return Response({"error": "Temperature and condition are required."}, status=400)

    try:
        temperature = float(temperature)
    except ValueError:
        return Response({"error": "Invalid temperature format."}, status=400)

    user_lat = user.latitude
    user_lon = user.longitude

    # Step 1: Weather-to-Category Mapping
    weather_category_map = {
    "cold": [
        "Handi", "Karahi", "Qorma", "Soup", "Tea & Snacks",
         "Steaks & Grills", "Barbecue", "Biryani / Pulao", 
        "Fast Food", "Dessert", "Cakes & Pastries", "Chocolate Items",
        "Seafood",
    ],
    "hot": [
        "Ice Cream", "Beverages", "Falooda / Kulfi / Rabri",
        "Salads", "Continental", "Handi", "Karahi", "Qorma","Fast Food", "Barbecue", "Biryani / Pulao",
    ],
    "moderate": [
        "Barbecue", "Seafood", "Desi", "Daal", "Mexican (Tacos, Burritos)",
        "Japanese / Sushi", "Chocolate Items", "Dessert", "Cakes & Pastries",
        "Soup", "Tea & Snacks", "Qorma", "Nihari", "Haleem", 
        "Biryani / Pulao", "Fast Food", "Asian Fusion", "Sabzi", "Chinese",
    ],
    "rain": [
        "Soup", "Tea & Snacks", "Barbecue", "Biryani / Pulao", 
        "Fast Food", "Dessert", "Cakes & Pastries", "Steaks & Grills",
        "Handi", "Karahi", "Qorma"
    ],
    "snow": [
        "Beverages", "Chocolate Items", "Soup", "Tea & Snacks",
        "Steaks & Grills", "Handi", "Karahi", "Qorma"
    ],
    "clear": [
        "Barbecue", "Seafood", "Desi", "Daal", "Mexican (Tacos, Burritos)",
        "Japanese / Sushi", "Chocolate Items", "Dessert", "Cakes & Pastries",
        "Soup", "Tea & Snacks", "Qorma", "Nihari", "Haleem",
        "Biryani / Pulao", "Fast Food", "Asian Fusion", "Ice Cream",
        "Snacks / Street Food", "Continental"
    ],
    "clouds": [
        "Snacks / Street Food", "Karahi", "Barbecue", "Biryani / Pulao",
        "Fast Food", "Dessert", "Cakes & Pastries", "Steaks & Grills",
        "Tea & Snacks", "Handi", "Qorma",
    ]
}

    # Determine weather context
    selected_categories = []

    if temperature < 15:
        selected_categories += weather_category_map["cold"]
    elif temperature > 30:
        selected_categories += weather_category_map["hot"]
    else:
        selected_categories += weather_category_map["moderate"]

    if "rain" in condition:
        selected_categories += weather_category_map["rain"]
    if "snow" in condition:
        selected_categories += weather_category_map["snow"]
    if "clear" in condition or "sunny" in condition:
        selected_categories += weather_category_map["clear"]
    if "clouds" in condition:
        selected_categories += weather_category_map["clouds"]

    selected_categories = list(set(selected_categories))  # remove duplicates

    # Step 2: Filter restaurants within 5 km
    radius_km = 5
    nearby_restaurant_ids = []

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0  # Earth radius in km
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    for restaurant in Restaurant.objects.all():
        distance = haversine(user_lat, user_lon, restaurant.latitude, restaurant.longitude)
        if distance <= radius_km:
            nearby_restaurant_ids.append(restaurant.id)

    # Step 3: Filter dishes
    dishes = Dish.objects.filter(
        category__title__in=selected_categories,
        restaurant__id__in=nearby_restaurant_ids
    )

    serializer = DishSerializer(dishes, many=True)

    return Response({
        "recommended_categories": selected_categories,
        "dishes": serializer.data
    })




# class ReviewListAPIView(generics.ListCreateAPIView):
#     # queryset=Review.objects.all()
#     serializer_class=ReviewSerializer
#     permission_classes=[AllowAny]

#     def get_queryset(self):
#         dish_id=self.kwargs['dish_id']
#         dish=Dish.objects.get(id=dish_id)
#         reviews=Review.objects.filter(dish=dish)
#         return reviews
    
    
#     # def create(self,request,*args, **kwargs):
#     #     payload=request.data

#     #     user_id=payload['user_id']
#     #     dish_id=payload['dish_id']
#     #     rating=payload['rating']
#     #     review=payload['review']

#     #     user=User.objects.get(id=user_id)
#     #     dish=Dish.objects.get(id=dish_id)

#     #     Review.objects.create(
#     #         user=user,
#     #         dish=dish,
#     #         rating=rating,
#     #         review=review
#     #     )
#     #     return Response({"message":"Review Cretaed Successfully"},status=status.HTTP_200_OK)
#     # def list(self, request, *args, **kwargs):
#     #     queryset = self.get_queryset()
#     #     serializer = self.get_serializer(queryset, many=True)

#     #     user_has_reviewed = False
#     #     if request.user.is_authenticated:
#     #         user_has_reviewed = queryset.filter(user=request.user).exists()

#     #     return Response({
#     #     "reviews": serializer.data,
#     #     "has_reviewed": user_has_reviewed
#     #     })
#     def list(self, request, *args, **kwargs):
#         try:
#             queryset = self.get_queryset()
#             serializer = self.get_serializer(queryset, many=True)
            
#             response_data = {
#                 'reviews': serializer.data,
#                 'count': queryset.count(),
#                 'has_reviewed': False
#             }

#             # Only check for authenticated users
#             if request.user.is_authenticated:
#                 response_data['has_reviewed'] = queryset.filter(user=request.user).exists()

#             return Response(response_data)

#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)