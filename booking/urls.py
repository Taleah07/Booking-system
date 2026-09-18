"""
URL configuration for booking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from system import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_page, name='home'),
    path('contact/', views.contact_page, name='contact'),
    path('operator/', views.operator_page, name='operator'),
    path('technical/', views.technical_page, name='technical'),
    path('bookings/', views.bookings_list, name='bookings_list'),
    path('bookings/accept/<int:booking_id>/', views.accept_booking, name='accept_booking'),
    path('bookings/decline/<int:booking_id>/', views.decline_booking, name='decline_booking'),
    path('bookings/decline/<int:booking_id>/preview/', views.preview_decline_booking, name='preview_decline_booking'),
    path('bookings/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('bookings/delete/<int:booking_id>/', views.delete_booking, name='delete_booking'),
    path('export/technical/', views.export_technical, name='bookings_export'),
    path('bookings/accept/legislative/<int:booking_id>/', views.accept_booking_legislative, name='accept_booking_legislative'),
    path('bookings/decline/legislative/<int:booking_id>/', views.decline_booking_legislative, name='decline_booking_legislative'),
    path('bookings/decline/legislative/<int:booking_id>/preview/', views.preview_decline_booking_legislative, name='preview_decline_booking_legislative'),
    path('bookings/cancel/legislative/<int:booking_id>/', views.cancel_booking_legislative, name='cancel_booking_legislative'),
    path('bookings/delete/legislative/<int:booking_id>/', views.delete_booking_legislative, name='delete_booking_legislative'),
    path('operator/done/<int:booking_id>/', views.mark_operator_done, name='mark_operator_done'),
    path('operator/delete/<int:booking_id>/', views.delete_operator_booking, name='delete_operator_booking'),
    path('export/technical/', views.export_technical, name='export_technical'),
    path('export/legislative/', views.export_legislative, name='export_legislative'),
    path('technical/book/<int:slot_id>/', views.book_training_technical, name='book_training_technical'),
    path('technical/book/<int:slot_id>/', views.book_training_technical, name='book_training'),
    path('legislative/', views.legislative_page, name='legislative'),
    path('legislative/book/<int:slot_id>/', views.book_training_legislative, name='book_training_legislative'),
    path('legislative/book/<int:slot_id>/', views.book_training_legislative, name='book_legislative_training'),
    path('technical/week/add/', views.add_technical_week, name='add_technical_week'),
    path('technical/week/add/', views.add_week, name='add_week'),
    path('technical/slot/add/', views.add_technical_slot, name='add_technical_slot'),
    path('technical/slot/add/', views.add_technical_slot, name='add_slot'),
    path('legislative/week/add/', views.add_legislative_week, name='add_legislative_week'),
    path('legislative/slot/add/', views.add_legislative_slot, name='add_legislative_slot'),
    path('technical/slot/<int:slot_id>/edit/', views.edit_technical_slot, name='edit_technical_slot'),
    path('technical/slot/<int:slot_id>/delete/', views.delete_technical_slot, name='delete_technical_slot'),
    path('legislative/slot/<int:slot_id>/edit/', views.edit_legislative_slot, name='edit_legislative_slot'),
    path('legislative/slot/<int:slot_id>/delete/', views.delete_legislative_slot, name='delete_legislative_slot'),
    path('technical/week/<int:week_id>/edit/', views.edit_week_technical, name='edit_week_technical'),
    path('technical/week/<int:week_id>/delete/', views.delete_week_technical, name='delete_week_technical'),
    path('legislative/week/<int:week_id>/edit/', views.edit_week_legislative, name='edit_week_legislative'),
    path('legislative/week/<int:week_id>/delete/', views.delete_week_legislative, name='delete_week_legislative'),
    path('technical/instructor/<int:instructor_id>/edit/', views.edit_instructor_technical, name='edit_instructor_technical'),
    path('technical/instructor/<int:instructor_id>/delete/', views.delete_instructor_technical, name='delete_instructor_technical'),
    path('legislative/instructor/<int:instructor_id>/edit/', views.edit_instructor_legislative, name='edit_instructor_legislative'),
    path('legislative/instructor/<int:instructor_id>/delete/', views.delete_instructor_legislative, name='delete_instructor_legislative'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)