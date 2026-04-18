from django.urls import path

from . import views

urlpatterns = [
    path("", views.order_list, name="order-list"),
    path("create/", views.order_create, name="order-create"),
    path("<uuid:order_id>/", views.order_detail, name="order-detail"),
    path("<uuid:order_id>/cancel/", views.order_cancel, name="order-cancel"),
]