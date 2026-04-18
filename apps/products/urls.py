from django.urls import path
from . import views

urlpatterns = [
    path("",views.product_list,name="product-list"),
    path("<uuid:product_id>/",views.product_detail,name="product-detail"),
    path("create/",views.product_create,name="product-create"),
    path("<uuid:product_id>/update/",views.product_update,name="product-update"),
    path("categories/",views.category_list,name="category-list")
]