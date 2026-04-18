from django.urls import path

from . import views

urlpatterns = [
    path("", views.inventory_list, name="inventory-list"),
    path("<uuid:product_id>/", views.inventory_detail, name="inventory-detail"),
]