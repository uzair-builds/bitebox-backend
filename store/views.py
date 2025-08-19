from django.shortcuts import render
from .models import Dish,Category,Cart,Tax,PortionSize,CartOrder,CartOrderItem,Notification,Restaurant
from account.models import User
from .serializers import DishSerializer,CategorySerializer,CartSerializer,CartOrderSerializer
from rest_framework import generics 
from rest_framework.permissions import AllowAny,IsAuthenticated 
from decimal import Decimal
from rest_framework.response import Response
from rest_framework import status
from math import radians, sin, cos, sqrt, atan2
from rest_framework.decorators import api_view

# Create your views here.

def send_notification(user=None, restaurant=None, order=None, order_item=None):
    Notification.objects.create(
        user=user,
        restaurant=restaurant,
        order=order,
        order_item=order_item,
    )

    
class CategoryListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Category.objects.order_by('?')[:6]


class DishListAPIView(generics.ListAPIView):
    queryset=Dish.objects.all()
    serializer_class=DishSerializer
    permission_classes=[AllowAny]
    def get_queryset(self):
        restaurant_id = self.request.query_params.get('restaurant_id')
        print(restaurant_id)
        if restaurant_id:
            print(Dish.objects.filter(restaurant_id=restaurant_id))
            return Dish.objects.filter(restaurant_id=restaurant_id)
        
        return Dish.objects.all()

class DishDetailAPIView(generics.RetrieveAPIView):
    queryset=Dish.objects.all()
    serializer_class=DishSerializer
    permission_classes=[AllowAny]

    def get_object(self):
        #Requires the slug field from the url
        slug=self.kwargs['slug']
        return Dish.objects.get(slug=slug)

        # return super().get_object()

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        portion_size = request.query_params.get('portion_size', None)

        # Get the product based on the slug
        dish = self.get_queryset().filter(slug=slug).first()
        price_by_portion_size=0
        if not dish:
            return Response({"error": "Product not found"}, status=404)

        # Modify product data based on size
        if portion_size:
            portion_size_obj=PortionSize()
            portion_size_price = portion_size_obj.get_price_by_portion(portion_size)
            print(portion_size_price)
            if portion_size_price > 0.00:
                price_by_portion_size=dish.price+portion_size_price
                print("price",price_by_portion_size)   
                
          
            else:
                price_by_portion_size=dish.price
        serializer = self.get_serializer(dish)
        data = serializer.data
        data['price_by_portion_size'] = price_by_portion_size  # Include the adjusted price in the response

        return Response(data)
       

class CartAPIView(generics.ListCreateAPIView):
    queryset=Cart.objects.all()
    serializer_class=CartSerializer
    permission_classes=[AllowAny]
    def create(self,request,*args, **kwargs):
        portion_size_obj=PortionSize()
        
        payload=request.data
        is_voice = payload.get('is_voice_item', 'false') == 'true'
        dish_id=payload['dish_id']
        user_id=payload['user_id']
        qty=payload['qty']
        print()
        price=payload['price']
        print(type(price))
        
        # shipping_amount=payload['shipping_amount']
        country=payload['country']
        if country == "undefined":
            country ="Pakistan"
        portion_size=payload['portionSize']
        print("size=============="+portion_size)
        if portion_size!="No portion size":
            portion_size_price=portion_size_obj.get_price_by_portion(portion_size)
            print(portion_size_price)
            print("size==============",portion_size_price)
            price= Decimal(price)+portion_size_price
            print(price)
            print(type(portion_size_price))
        spice_level=payload['spiceLevel']
        cart_id=payload['cart_id']
        
        dish=Dish.objects.get(id=dish_id)
        if user_id != "undefined":
            user=User.objects.get(id=user_id)
        else:
            user=None
        tax=Tax.objects.filter(country=country).first()
        if tax:
            tax_rate=tax.rate / 100
        else:
            tax_rate=0
        # cart=Cart.objects.filter(cart_id=cart_id,dish=dish ).first()
        cart=Cart.objects.filter(cart_id=cart_id,dish=dish,portion_size=portion_size,spice_level=spice_level).first()
#         cart=Cart.objects.filter(cart_id=cart_id,dish=dish,portion_size=portion_size,           # Added size
#  spice_level=spice_level ).first()
        if cart:
            cart.dish=dish
            cart.user=user
            cart.qty=qty
            cart.price=price 
            cart.is_voice_item=is_voice
            cart.sub_total=Decimal(price)*int(qty)
            # cart.shipping_amount=Decimal(shipping_amount)*int(qty)
            cart.tax_fee=int(qty) * Decimal(tax_rate)
            cart.spice_level=spice_level
            cart.portion_size=portion_size
            cart.country=country
            cart.cart_id=cart_id

            service_fee=2 / 100
            cart.service_fee=Decimal(service_fee)*cart.sub_total
            
            cart.total=cart.sub_total+cart.service_fee+cart.tax_fee
            cart.save()
            
            return Response({"message":"Cart Updated Successfully!"},status=status.HTTP_200_OK)
        else:
            cart=Cart()
            cart.dish=dish
            cart.user=user
            cart.qty=qty
            cart.price=price
            cart.is_voice_item=is_voice
            cart.sub_total=Decimal(price)*int(qty)
            # cart.shipping_amount=Decimal(shipping_amount)*int(qty)
            cart.tax_fee=int(qty) * Decimal(tax_rate)
            cart.spice_level=spice_level
            cart.portion_size=portion_size
            cart.country=country
            cart.cart_id=cart_id

            service_fee=2 / 100
            cart.service_fee=Decimal(service_fee) * cart.sub_total
            
            cart.total=cart.sub_total+cart.service_fee+cart.tax_fee
            cart.save()
        
            return Response({"message":"Cart Created Successfully!"},status=status.HTTP_201_CREATED)
            
class CartLisAPItView(generics.ListAPIView):
    serializer_class=CartSerializer
    permission_classes=[AllowAny]
    queryset=Cart.objects.all()

    def get_queryset(self):
        cart_id=self.kwargs['cart_id']
        user_id=self.kwargs.get("user_id")

        if user_id is not None:
            user=User.objects.get(id=user_id)
            queryset=Cart.objects.filter(user=user,cart_id=cart_id)
        else:
            queryset=Cart.objects.filter(cart_id=cart_id)
        return queryset


class CartDetailAPIView(generics.RetrieveAPIView):
    serializer_class=CartSerializer
    permission_classes=[AllowAny]
    lookup_field= "cart_id"

    def get_queryset(self):
        cart_id=self.kwargs['cart_id']
        user_id=self.kwargs.get("user_id")

        if user_id is not None:
            user=User.objects.get(id=user_id)
            queryset=Cart.objects.filter(user=user,cart_id=cart_id)
        else:
            queryset=Cart.objects.filter(cart_id=cart_id)
        return queryset

    def get(self,request,*args, **kwargs):
        queryset=self.get_queryset()

        # total_shipping=0.0
        total_tax=0.0
        total_service_fee=0.0
        total_subtotal=0.0
        total_total=0.0

        for cart_item in queryset:
            # total_shipping+=float(self.calculate_shipping(cart_item))
            total_tax+=float(self.calculate_tax(cart_item))
            total_service_fee+=float(self.calculate_service_fee(cart_item))
            total_subtotal+=float(self.calculate_subtotal(cart_item))
            total_total+=float(self.calculate_total(cart_item))

        data={
            # 'shipping':total_shipping,
            'tax':total_tax,
            'service_fee':total_service_fee,
            'subtotal':total_subtotal,
            'total':total_total,
            }

        return Response(data)
    
    # def calculate_shipping(self,cart_item):
    #     return cart_item.shipping_amount

    def calculate_tax(self,cart_item):
        return cart_item.tax_fee
    
    def calculate_service_fee(self,cart_item):
        return cart_item.service_fee
    
    def calculate_subtotal(self,cart_item):
        return cart_item.sub_total
    
    def calculate_total(self,cart_item):
        return cart_item.total

class CartDeleteAPIView(generics.DestroyAPIView):
     serializer_class=CartSerializer
     lookup_field='cart_id'
     
     def get_object(self):
        cart_id=self.kwargs['cart_id']
        item_id=self.kwargs['item_id']
        user_id=self.kwargs.get("user_id") #get for not breaking of api if the user_id deos not exist

        if user_id:
            user=User.objects.get(id=user_id)
            cart=Cart.objects.get(cart_id=cart_id,id=item_id,user=user)
        else:
            cart=Cart.objects.get(cart_id=cart_id,id=item_id)
        return cart

class createOrderAPIView(generics.CreateAPIView):
    serializer_class=CartOrderSerializer
    permission_classes=[AllowAny]
    queryset=CartOrder.objects.all()
    def create(self,request):
        payload=request.data
        full_name=payload['full_name']
        mobile=payload['mobile']
        address=payload['address']
        city=payload['city']
        cart_id=payload['cart_id']
        user_id=payload['user_id']
        is_voice_order = payload.get('is_voice_order') == 'true'  # Check voice order flag
        
        
        try:
            user=User.objects.get(id=user_id)
        except:
            user=None
        cart_items=Cart.objects.filter(cart_id=cart_id)

        # total_shipping=Decimal(0.00)
        total_tax=Decimal(0.00)
        total_service_fee=Decimal(0.00)
        total_sub_total=Decimal(0.00)
        total_initial_total=Decimal(0.00) # for coupon functionality
        total_total=Decimal(0.00)
        order=CartOrder.objects.create(
            buyer=user,
            full_name=full_name,
            mobile=mobile,
            address=address,
            city=city,
        )
        if order.buyer !=None:
            send_notification(user=order.buyer,order=order)

        
        for c in cart_items:
            CartOrderItem.objects.create(
                order=order,
                dish=c.dish,
                restaurant=c.dish.restaurant,
                qty=c.qty,
                portion_size=c.portion_size,
                spice_level=c.spice_level,
                price=c.price,
                sub_total=c.sub_total,
                # shipping_amount=c.shipping_amount,
                service_fee=c.service_fee,
                tax_fee=c.tax_fee,
                total=c.total,
                initial_total=c.total,
            )
            # total_shipping+=Decimal(c.shipping_amount)
            total_tax+=Decimal(c.tax_fee)
            total_service_fee+=Decimal(c.service_fee)
            total_sub_total+=Decimal(c.sub_total)
            total_initial_total+=Decimal(c.total)
            total_total+=Decimal(c.total)
            order.restaurant.add(c.dish.restaurant)
        # order = CartOrder.objects.get(oid=order.oid)
        order_items = CartOrderItem.objects.filter(order=order)
        print(order_items)
        for o in order_items:
            send_notification(restaurant=o.restaurant,order=order,order_item=o)
        order.sub_total=total_sub_total
        # order.shipping_amount=total_shipping
        order.service_fee=total_service_fee
        order.tax_fee=total_tax
        order.initial_total=total_total
        order.total=total_total

        order.save()
        # cart_items.delete()
        if is_voice_order:
            Cart.objects.filter(cart_id=cart_id, is_voice_item=True).delete()
        else:
            # Normal behavior - delete all cart items
            Cart.objects.filter(cart_id=cart_id, is_voice_item=False).delete()
        return Response({"Message:":"Order created successfully","Order_Id":order.oid},status=status.HTTP_201_CREATED)
    
        
class checkoutAPIView(generics.RetrieveAPIView):
    serializer_class=CartOrderSerializer
    lookup_field="order_oid"
    # queryset=CartOrder.objects.all()

    def get_object(self):
        order_oid=self.kwargs['order_oid']
        print(order_oid)
        order=CartOrder.objects.get(oid=order_oid)
        print(order)
        return order   

# class SearchDishAPIView(generics.ListCreateAPIView):
#     serializer_class=DishSerializer
#     permission_classes=[AllowAny]

#     def get_queryset(self):
#         query=self.request.GET.get("query")
#         print(query)
#         dishes=Dish.objects.filter(status="published",title__icontains=query) 
#         print(dishes)  
#         return dishes   

#   

class SearchDishAPIView(generics.ListAPIView):
    serializer_class = DishSerializer
    permission_classes = [AllowAny]

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def get_queryset(self):
        query = self.request.GET.get("query", "").strip()
        user = self.request.user
        if not query:
            return Dish.objects.none()

    
        if not user.is_authenticated:
            return Dish.objects.none()  # Or fallback to all published dishes with the query

        user_latitude = user.latitude
        user_longitude = user.longitude
        radius_km = 5

        nearby_restaurant_ids = []

        for restaurant in Restaurant.objects.all():
            distance = self.haversine_distance(user_latitude, user_longitude, restaurant.latitude, restaurant.longitude)
            if distance <= radius_km:
                nearby_restaurant_ids.append(restaurant.id)

        return Dish.objects.filter(
            status="published",
            title__icontains=query,
            restaurant__id__in=nearby_restaurant_ids
        )
    
        

@api_view(['DELETE'])
def clear_cart(request, cart_id, user_id=None):
    if user_id:
        Cart.objects.filter(cart_id=cart_id, user_id=user_id).delete()
    else:
        Cart.objects.filter(cart_id=cart_id, user=None).delete()
    return Response({"message": "Cart cleared."}, status=204)



class CartAPIViewVoiceOrder(generics.ListCreateAPIView):
    queryset=Cart.objects.all()
    serializer_class=CartSerializer
    permission_classes=[AllowAny]
    def create(self,request,*args, **kwargs):
        portion_size_obj=PortionSize()

        payload=request.data
        is_voice = payload.get('is_voice_item', 'false') == 'true'
        dish_id=payload['dish_id']
        user_id=payload['user_id']
        qty=payload['qty']
        print()
        price=payload['price']
        print(type(price))
        
        # shipping_amount=payload['shipping_amount']
        country=payload['country']
        if country == "undefined":
            country ="Pakistan"
        portion_size=payload['portionSize']
        print("size=============="+portion_size)
        if portion_size!="No portion size":
            portion_size_price=portion_size_obj.get_price_by_portion(portion_size)
            print(portion_size_price)
            print("size==============",portion_size_price)
            price= Decimal(price)+portion_size_price
            print(price)
            print(type(portion_size_price))
        spice_level=payload['spiceLevel']
        cart_id=payload['cart_id']
        
        dish=Dish.objects.get(id=dish_id)
        if user_id != "undefined":
            user=User.objects.get(id=user_id)
        else:
            user=None
        tax=Tax.objects.filter(country=country).first()
        if tax:
            tax_rate=tax.rate / 100
        else:
            tax_rate=0
        # cart=Cart.objects.filter(cart_id=cart_id,dish=dish ).first()
        cart=Cart.objects.filter(cart_id=cart_id,dish=dish,portion_size=portion_size,spice_level=spice_level).first()
#         cart=Cart.objects.filter(cart_id=cart_id,dish=dish,portion_size=portion_size,           # Added size
#  spice_level=spice_level ).first()
        if cart:
            cart.dish=dish
            cart.user=user
            cart.qty=qty
            cart.price=price 
            cart.is_voice_item=is_voice
            cart.sub_total=Decimal(price)
            # cart.shipping_amount=Decimal(shipping_amount)*int(qty)
            cart.tax_fee=int(qty) * Decimal(tax_rate)
            cart.spice_level=spice_level
            cart.portion_size=portion_size
            cart.country=country
            cart.cart_id=cart_id

            service_fee=2 / 100
            cart.service_fee=Decimal(service_fee)*cart.sub_total
            
            cart.total=cart.sub_total+cart.service_fee+cart.tax_fee
            cart.save()
            
            return Response({"message":"Cart Updated Successfully!"},status=status.HTTP_200_OK)
        else:
            cart=Cart()
            cart.dish=dish
            cart.user=user
            cart.qty=qty
            cart.price=price
            cart.is_voice_item=is_voice
            cart.sub_total=Decimal(price)
            # cart.shipping_amount=Decimal(shipping_amount)*int(qty)
            cart.tax_fee=int(qty) * Decimal(tax_rate)
            cart.spice_level=spice_level
            cart.portion_size=portion_size
            cart.country=country
            cart.cart_id=cart_id

            service_fee=2 / 100
            cart.service_fee=Decimal(service_fee) * cart.sub_total
            
            cart.total=cart.sub_total+cart.service_fee+cart.tax_fee
            cart.save()
        
            return Response({"message":"Cart Created Successfully!"},status=status.HTTP_201_CREATED)