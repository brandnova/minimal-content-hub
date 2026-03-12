from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    # Content
    path('', views.content_list, name='list'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('course/<slug:slug>/', views.course_detail, name='course_detail'),

    # Payments
    path('course/<slug:slug>/buy/', views.payment_select, name='payment_select'),
    path('course/<slug:slug>/pay/', views.payment_initiate, name='payment_initiate'),
    path('payment/verify/<str:gateway>/<uuid:reference>/', views.payment_verify, name='payment_verify'),

    # Profile
    path('profile/', views.profile, name='profile'),
]