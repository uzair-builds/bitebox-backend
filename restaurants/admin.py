from django.contrib import admin
from .models import Restaurant,DeliveryBoy,RestaurantRequest


@admin.action(description='Approve selected restaurant requests')
def approve_requests(modeladmin, request, queryset):
    for obj in queryset.filter(status='pending'):
        print(f"Approving: {obj.name}")
        obj.status = 'approved'
        obj.save()

        # Prevent creating duplicate restaurants for the same user
        if not Restaurant.objects.filter(user=obj.user).exists():
            restaurant = Restaurant(
                user=obj.user,
                name=obj.name,
                image=obj.image,
                email=obj.email,
                phone_number=obj.contact_no,
                description=obj.description,
                latitude=obj.latitude,
                longitude=obj.longitude,
            )
            restaurant.save()  # Triggers slug generation in the save method

            print(f"✅ Restaurant created: {restaurant.name} (slug: {restaurant.slug})")
        else:
            print(f"⚠️ Restaurant already exists for user: {obj.user}")


@admin.register(RestaurantRequest)
class RestaurantRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'created_at']
    actions = [approve_requests]


admin.site.register(Restaurant)
admin.site.register(DeliveryBoy)
