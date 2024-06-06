from django.urls import path

from . import views

urlpatterns = [
    path("miniapp", views.miniapp, name="miniapp"),
    path('get_user_info/', views.get_user_info, name='get_user_info'),
    path('lottery/', views.lottery, name='lottery'),
    path('withdraw/', views.withdraw, name='withdraw'),
]
