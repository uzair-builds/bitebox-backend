from django.urls import path
from account.views import SendPasswordResetEmailView,UpdateUserLocationView, UserChangePasswordView, UserLoginView, UserProfileView, UserRegistrationView, UserPasswordResetView,ProfileView,ActivateUser
urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('account/<user_id>/', ProfileView.as_view(), name='account'),
    path('changepassword/', UserChangePasswordView.as_view(), name='changepassword'),
    path('send-reset-password-email/', SendPasswordResetEmailView.as_view(), name='send-reset-password-email'),
    path('reset-password/<uid>/<token>/', UserPasswordResetView.as_view(), name='reset-password'),
    path('update-location/', UpdateUserLocationView.as_view(), name='update-location'),
    path('activate/<uidb64>/<token>/', ActivateUser.as_view(), name='activate-user'),
]