from django.urls import path
from .views import CategoryListAPIView,DishListAPIView,DishDetailAPIView,CartAPIView,CartLisAPItView,CartDetailAPIView,CartDeleteAPIView,createOrderAPIView,checkoutAPIView,SearchDishAPIView,clear_cart,CartAPIViewVoiceOrder
urlpatterns = [
    path('categories/',CategoryListAPIView.as_view()),
    path('dishes/',DishListAPIView.as_view()),
    path('dish/<slug>',DishDetailAPIView.as_view()),
    path('cart/',CartAPIView.as_view()),
    path('cart-voice-order/',CartAPIViewVoiceOrder.as_view()),
    path('cart-list/<str:cart_id>/<int:user_id>/',CartLisAPItView.as_view()),
    path('cart-list/<str:cart_id>/',CartLisAPItView.as_view()),
    path('cart-detail/<str:cart_id>/',CartDetailAPIView.as_view()),
    path('cart-detail/<str:cart_id>/<int:user_id>/',CartDetailAPIView.as_view()),
    path('cart-delete/<str:cart_id>/<int:user_id>/<int:item_id>/',CartDeleteAPIView.as_view()),
    path('cart-delete/<str:cart_id>/<int:item_id>/',CartDeleteAPIView.as_view()),
    path('cart-delete/<str:cart_id>/<int:item_id>/',CartDeleteAPIView.as_view()),
    path('create-order/',createOrderAPIView.as_view()),
    path('checkout/<order_oid>/',checkoutAPIView.as_view()),
    path('search/',SearchDishAPIView.as_view()),
    path('cart-clear/<str:cart_id>/', clear_cart),
    path('cart-clear/<str:cart_id>/<int:user_id>/', clear_cart),

]