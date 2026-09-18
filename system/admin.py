from django.contrib import admin

from .models import Instructor, ScheduleSlot, TrainingBooking, TrainingWeek , LegislativeScheduleSlot


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(TrainingWeek)
class TrainingWeekAdmin(admin.ModelAdmin):
    list_display = ("display_name", "start_date", "end_date")
    list_editable = ()
    search_fields = ("week_range", "start_date", "end_date")


@admin.register(ScheduleSlot)
class ScheduleSlotAdmin(admin.ModelAdmin):
    list_display = ("week", "instructor", "training_title", "venue_info")
    list_filter = ("week", "instructor")
    search_fields = ("training_title", "venue_info")


@admin.register(TrainingBooking)
class TrainingBookingAdmin(admin.ModelAdmin):
    list_display = ("full_name" , "company", "slot", "created_at")
    list_filter = ("slot", "created_at")
    search_fields = ("full_name", "company")

@admin.register(LegislativeScheduleSlot)
class LegislativeScheduleSlotAdmin(admin.ModelAdmin):
    list_display = ("week", "instructor", "training_title", "venue_info")
    list_filter = ("week", "instructor")
