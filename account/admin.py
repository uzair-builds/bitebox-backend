from django.contrib import admin
from account.models import User,Profile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin



class UserAdmin(BaseUserAdmin):
    # Fields to be displayed in the admin panel
    list_display = ('email', 'name', 'phone', 'latitude', 'longitude', 'is_admin', 'is_active')
    list_filter = ('is_admin', 'is_active')
    
    # Organize fields into sections for the edit page
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'phone', 'latitude', 'longitude','is_verified')}),
        ('Permissions', {'fields': ('is_admin', 'is_active')}),
        ('Important Dates', {'fields': ('last_login',)}),
    )
    
    # Organize fields for the add user page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'latitude', 'longitude', 'is_active', 'is_admin','is_verified'),
        }),
    )
    
    search_fields = ('email', 'name')
    ordering = ('email',)
    filter_horizontal = ()


class ProfileAdmin(admin.ModelAdmin):
    list_display=["full_name",'gender','country']
    list_filter=['date']
    
# Register the custom user model
admin.site.register(User, UserAdmin)
admin.site.register(Profile,ProfileAdmin)