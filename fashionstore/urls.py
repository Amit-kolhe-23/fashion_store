# fashionstore/urls.py
from django.contrib import admin
from django.urls import path, include  # Don't forget to import include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')), # Add this line to include the store app's URLs
]
