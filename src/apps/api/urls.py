from django.urls import path
from . import views
from .views import DeviceTokenView

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('run-browserbase/', views.run_browserbase_view, name='run-browserbase'),
    path('queue-automation/', views.queue_automation, name='queue-automation'),
    path('device-token/', DeviceTokenView.as_view(), name='device-token'),
] 