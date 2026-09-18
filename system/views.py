import datetime
import re

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookingForm, LegislativeBookingForm, OperatorBookingForm, ScheduleSlotForm, TrainingWeekForm, LegislativeScheduleSlotForm
from .models import Instructor, ScheduleSlot, TrainingBooking, TrainingWeek , LegislativeBooking , LegislativeScheduleSlot , OperatorTrainingBooking
from django.contrib.admin.views.decorators import staff_member_required
import csv
from django.http import HttpResponse
try:
    import openpyxl
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except Exception:
    OPENPYXL_AVAILABLE = False
from .models import TrainingWeek 

def home_page(request):
    return render(request, "index.html")


def contact_page(request):
    return render(request, "contact.html")

def operator_page(request):
    if request.method == "POST":
        form = OperatorBookingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your training booking request has been received.")
            return redirect("operator")
    else:
        form = OperatorBookingForm()

    return render (request, "operator.html",{"form": form})


def technical_page(request):
    instructors = Instructor.objects.filter(category="technical")
    weeks = TrainingWeek.objects.all().order_by("start_date")
    slots = ScheduleSlot.objects.select_related("week", "instructor").all()

    grid_lookup = {}
    for slot in slots:
        grid_lookup[(slot.week_id, slot.instructor_id)] = slot

    calendar_rows = []
    for week in weeks:
        row_cells = []
        for instructor in instructors:
            slot = grid_lookup.get((week.id, instructor.id))
            row_cells.append({"instructor": instructor, "slot": slot})

        calendar_rows.append({"week": week, "cells": row_cells, "booking_closed": week.is_booking_closed})

    context = {
        "technical_instructors": instructors,
        "technical_calendar_rows": calendar_rows,
    }

    return render(request, "technical.html", context)

def edit_instructor_technical(request, instructor_id):
    instructor = get_object_or_404(Instructor, id=instructor_id)
    if request.method == "POST":
        instructor.name = request.POST.get("name")
        instructor.save()
        return redirect("technical_page")
    return render(request, 'edit_instructor.html',{"instructor": instructor})

def delete_instructor_technical(request, instructor_id):
    instructor = get_object_or_404(Instructor, id=instructor_id)
    if request.method == "POST":
        instructor.name = request.POST.get("name")
        instructor.delete()
        return redirect("technical_page")
    return render(request, 'confirm_delete.html',{"instructor": instructor})

def edit_week_technical(request, week_id):
    week = get_object_or_404(TrainingWeek, id=week_id)

    if request.method == "POST":
        form = TrainingWeekForm(request.POST, instance=week)
        if form.is_valid():
            form.save()
            messages.success(request, "Week updated successfully.")
            return redirect("technical")
    else:
        form = TrainingWeekForm(instance=week)

    return render(request, "edit_week.html", {"form": form, "week": week})

def delete_week_technical(request, week_id):
    week = get_object_or_404(TrainingWeek, id=week_id)
    if request.method == "POST":
        week.delete()
        messages.success(request, "Week deleted successfully.")
        return redirect("technical")
    return render(request, 'confirm_delete.html', {"object": week, "object_type": "Week"})


def book_training_technical(request, slot_id):
    slot = get_object_or_404(ScheduleSlot, pk=slot_id)

    if slot.week.is_booking_closed and not request.user.is_staff:
        messages.error(request, "Bookings for this week are closed.")
        return redirect("technical")

    if slot.seats_remaining <= 0:
        messages.error(request, "No seats remaining for this training slot.")
        return render(request, "booking_form_technical.html", {"form": BookingForm(), "slot": slot, "is_full": True})

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                slot = ScheduleSlot.objects.select_for_update().get(pk=slot_id)
                if slot.seats_remaining <= 0:
                    messages.error(request, "No seats remaining for this training slot.")
                    return render(request, "booking_form_technical.html", {"form": form, "slot": slot, "is_full": True})

                booking = form.save(commit=False)
                booking.slot = slot
                booking.save()
          

            messages.success(request, "Your training booking request has been received.")
            return redirect("technical")
    else:
        form = BookingForm()

    return render(request, "booking_form_technical.html", {"form": form, "slot": slot})


def book_training_legislative(request, slot_id):
    slot = get_object_or_404(LegislativeScheduleSlot, pk=slot_id)

    if slot.week.is_booking_closed and not request.user.is_staff:
        messages.error(request, "Bookings for this week are closed.")
        return redirect("legislative")

    if slot.seats_remaining <= 0:
        messages.error(request, "No seats remaining for this training slot.")
        return render(request, "booking_form_legislative.html", {"form": LegislativeBookingForm(slot=slot), "slot": slot, "is_full": True})

    if request.method == "POST":        
        form = LegislativeBookingForm(request.POST, request.FILES, slot=slot)
        if form.is_valid():
            with transaction.atomic():
                slot = LegislativeScheduleSlot.objects.select_for_update().get(pk=slot_id)
                if slot.seats_remaining <= 0:
                    messages.error(request, "No seats remaining for this training slot.")
                    return render(request, "booking_form_legislative.html", {"form": form, "slot": slot, "is_full": True})

                booking = form.save(commit=False)
                booking.slot = slot
                booking.category = "legislative"

                if request.FILES.get('id_pdf'):
                    booking.id_pdf = request.FILES['id_pdf']
                if request.FILES.get('education_pdf'):
                    booking.education_pdf = request.FILES['education_pdf']
                if request.FILES.get('medical_pdf'):
                    booking.medical_pdf = request.FILES['medical_pdf']
                if request.FILES.get('drivers_license_pdf'):
                    booking.drivers_license_pdf = request.FILES['drivers_license_pdf']
                if request.FILES.get('previous_license_pdf'):
                    booking.previous_license_pdf = request.FILES['previous_license_pdf']

                booking.save()

            messages.success(request, "Your legislative training booking request has been received.")
            return redirect("legislative")
    else:
        form = LegislativeBookingForm(slot=slot)

    return render(request, "booking_form_legislative.html", {"form": form, "slot": slot})


def legislative_page(request):
    instructors = Instructor.objects.filter(category="legislative")
    weeks = TrainingWeek.objects.all().order_by("start_date")
    slots = LegislativeScheduleSlot.objects.select_related("week", "instructor").all()

    grid_lookup = {}
    for slot in slots:
        week_id = slot.week_id
        instructor_id = slot.instructor_id
        key = f"{week_id}_{instructor_id}"

        if key not in grid_lookup:
            grid_lookup[key] = []

        if len(grid_lookup[key]) < 5:  # Limit to 5 slots per cell
            grid_lookup[key].append(slot)

    calendar_rows = []
    for week in weeks:
        row_cells = []
        for instructor in instructors:
            lookup_key = f"{week.id}_{instructor.id}"
            slots_list = grid_lookup.get(lookup_key, [])
            
            row_cells.append({"instructor": instructor, "slots": slots_list})

        calendar_rows.append({"week": week, "cells": row_cells, "booking_closed": week.is_booking_closed})

    context = {
        "legislative_instructors": instructors,
        "legislative_calendar_rows": calendar_rows,
    }

    return render(request, "legislative.html", context)

def edit_instructor_legislative(request, instructor_id):
    instructor = get_object_or_404(Instructor, id=instructor_id)
    if request.method == "POST":
        instructor.name = request.POST.get("name")
        instructor.save()
        return redirect("legislative_page")
    return render(request, 'edit_instructor.html',{"instructor": instructor})

def delete_instructor_legislative(request, instructor_id):
    instructor = get_object_or_404(Instructor, id=instructor_id)
    if request.method == "POST":
        instructor.name = request.POST.get("name")
        instructor.delete()
        return redirect("legislative_page")
    return render(request, 'confirm_delete.html',{"instructor": instructor})

def edit_week_legislative(request, week_id):
    week = get_object_or_404(TrainingWeek, id=week_id)

    if request.method == "POST":
        form = TrainingWeekForm(request.POST, instance=week)
        if form.is_valid():
            form.save()
            messages.success(request, "Week updated successfully.")
            return redirect("legislative")
    else:
        form = TrainingWeekForm(instance=week)

    return render(request, 'edit_week.html', {"form": form, "week": week})

def delete_week_legislative(request, week_id):
    week = get_object_or_404(TrainingWeek, id=week_id)
    if request.method == "POST":
        week.delete()
        messages.success(request, "Week deleted successfully.")
        return redirect("legislative")
    return render(request, 'confirm_delete.html', {"object": week, "object_type": "Week"})

def bookings_list(request):
    if not request.user.is_staff:
        return redirect("home")

    technical_booking = TrainingBooking.objects.select_related("slot", "slot__instructor", "slot__week")\
    .order_by("slot__week__start_date", "slot__week__end_date", "slot__instructor__name", "-created_at")

    legislative_booking = LegislativeBooking.objects.select_related("slot", "slot__instructor", "slot__week")\
    .order_by("slot__week__start_date", "slot__week__end_date", "slot__instructor__name", "-created_at")
    
    context = {
        "technical_booking": technical_booking,
        "legislative_booking": legislative_booking,
    }

    return render(request, "bookings_list.html", context)


@staff_member_required
def export_technical(request):
    
    # Prefer XLSX if openpyxl is available
    if not OPENPYXL_AVAILABLE:
        return HttpResponse("openpyxl library is not installed. Please install it to export to XLSX.", status=500)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Technical Bookings"
    
    bookings = TrainingBooking.objects.select_related(
        "slot", "slot__instructor", "slot__week"
    ).order_by(
        "slot__week__start_date", "slot__week__end_date", "slot__instructor__name", "-created_at"
    )
    filename ="technical_bookings.xlsx"


    headers = [
        "created_at",
        "training",
        "week",
        "instructor",
        "full_name",
        "surname",
        "id_number",
        "admin_email",
        "candidate_email",
        "company",
        "company_number",
        "phone",
        "company name",
    ]
    ws.append(headers)

    for b in bookings:
        training_title = "No Slot Assigned"
        week_name = ""
        instructor_name = ""
        if b.slot:
            training_title = b.slot.training_title
            week_name = b.slot.week.display_name if b.slot.instructor else ""
            instructor_name = b.slot.instructor.name if b.slot.instructor else ""
        else:
            training_title = "No Slot Assigned"
            week_name = ""
            instructor_name = ""

        ws.append([
            b.created_at.isoformat() if b.created_at else "",
            training_title,
            week_name,
            instructor_name,
            b.full_name,
            b.surname,
            b.id_number,
            b.admin_email,
            b.candidate_email,
            getattr(b, "company", ''),
            getattr(b, "company_number", ''),
            b.phone,
            b.company_name,
        ])

        for i, column_cells in enumerate(ws.columns, 1):
            length = max((len(str(cell.value)) for cell in column_cells), default=0)
            ws.column_dimensions[get_column_letter(i)].width = min(max(length + 2, 10), 50)

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="bookings.xlsx"'
        wb.save(response)
        return response

    # Fallback to CSV
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="bookings.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "created_at",
        "training",
        "week",
        "instructor",
        "full_name",
        "surname",
        "id_number",
        "admin_email",
        "candidate_email",
        "company",
        "company_number",
        "phone",
        "company name",
    ])

    for b in bookings:
        writer.writerow([
            b.created_at.isoformat(),
            b.slot.training_title,
            b.slot.week.display_name if b.slot.week else "",
            b.slot.instructor.name if b.slot.instructor else "",
            b.full_name,
            b.surname,
            b.id_number,
            b.admin_email,
            b.candidate_email,
            b.company,
            b.company_number,
            b.phone,
            b.company_name,
        ])

    return response

@staff_member_required
def export_legislative(request):
    if not OPENPYXL_AVAILABLE:
        return HttpResponse("openpyxl library is not installed. Please install it to export to XLSX.", status=500)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Legislative Bookings"

    bookings = LegislativeBooking.objects.select_related(
        "slot", "slot__instructor", "slot__week"
    ).order_by(
        "slot__week__start_date", "slot__week__end_date", "slot__instructor__name", "-created_at"
    )
    filename = "legislative_bookings.xlsx"

    headers = [
        "created_at",
        "training",
        "week",
        "instructor",
        "full_name",
        "surname",
        "id_number",
        "admin_email",
        "supervisor_email",
        "company_number",
        "phone",
        "department",
    ]
    ws.append(headers)

    for b in bookings:
        training_title = "No Slot Assigned"
        week_name = ""
        instructor_name = ""
        if b.slot:
            training_title = b.slot.training_title
            week_name = b.slot.week.display_name if b.slot.instructor else ""
            instructor_name = b.slot.instructor.name if b.slot.instructor else ""
        else:
            last_history = b.history.filter(slot_id=None).order_by('-history_date').first()
            if last_history and last_history.slot:
                training_title = last_history.slot.training_title
                week_name = last_history.slot.week.display_name if last_history.slot.week else ""
                instructor_name = last_history.slot.instructor.name if last_history.slot.instuctor else "" 

        ws.append([
            b.created_at.isoformat() if b.created_at else "",
            training_title,
            week_name,
            instructor_name,
            b.full_name,
            b.surname,
            b.id_number,
            b.admin_email,
            b.supervisor_email,
            getattr(b, "company_number", ''),
            b.phone,
            getattr(b, "department", ''),
         ])


        # Autosize columns
        for i, column_cells in enumerate(ws.columns, 1):
            length = max((len(str(cell.value)) for cell in column_cells), default=0)
            ws.column_dimensions[get_column_letter(i)].width = min(max(length + 2, 10), 50)

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="bookings.xlsx"'
        wb.save(response)
        return response

    # Fallback to CSV
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="bookings.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "created_at",
        "training",
        "week",
        "instructor",
        "full_name",
        "surname",
        "id_number",
        "admin_email",
        "supervisor_email",
        "company_number",
        "phone",
        "department",
    ])

    for b in bookings:
        writer.writerow([
            b.created_at.isoformat(),
            b.slot.training_title,
            b.slot.week.display_name if b.slot.week else "",
            b.slot.instructor.name if b.slot.instructor else "",
            b.full_name,
            b.surname,
            b.id_number,
            b.admin_email,
            b.supervisor_email,
            b.company_number,
            b.phone,
            b.department,
        ])

    return response


@staff_member_required
def add_week(request):
    if request.method == "POST":
        form = TrainingWeekForm(request.POST)
        if form.is_valid():
            week_instance = form.save(commit=False)
            if week_instance.start_date:
                week_instance.sort_order = int(week_instance.start_date.strftime('%j'))
            elif week_instance.end_date:
                week_instance.sort_order = int(week_instance.end_date.strftime('%j'))
            else:
                week_instance.sort_order = 999
            week_instance.save()
            messages.success(request, "Week added successfully.")
            return redirect("technical")
    else:
        form = TrainingWeekForm()

    return render(request, "edit_week.html", {"form": form, "week": None, "title": "Add Week"})

@staff_member_required
def add_technical_week(request):
    if request.method == "POST":
        form = TrainingWeekForm(request.POST)
        if form.is_valid():
            week_instance = form.save(commit=False)
            if week_instance.start_date:
                week_instance.sort_order = int(week_instance.start_date.strftime('%j'))
            elif week_instance.end_date:
                week_instance.sort_order = int(week_instance.end_date.strftime('%j'))
            else:
                week_instance.sort_order = 999
            week_instance.save()
            messages.success(request, "Week added successfully.")
            return redirect("technical")
    else:
        form = TrainingWeekForm()

    return render(request, "edit_week.html", {"form": form, "week": None, "title": "Add Week"})

@staff_member_required
def add_legislative_week(request):
    if request.method == "POST":
        form = TrainingWeekForm(request.POST)
        if form.is_valid():
            week_instance = form.save(commit=False)
            if week_instance.start_date:
                week_instance.sort_order = int(week_instance.start_date.strftime('%j'))
            elif week_instance.end_date:
                week_instance.sort_order = int(week_instance.end_date.strftime('%j'))
            else:
                week_instance.sort_order = 999
            week_instance.save()
            messages.success(request, "Week added successfully.")
            return redirect("legislative")
    else:
        form = TrainingWeekForm()

    return render(request, "edit_week.html", {"form": form, "week": None, "title": "Add Week"})


@staff_member_required
def add_technical_slot(request):
    initial = {}
    week_id = request.GET.get("week")
    instructor_id = request.GET.get("instructor")

    if week_id:
        initial["week"] = week_id
    if instructor_id:
        initial["instructor"] = instructor_id

    if request.method == "POST":
        form = ScheduleSlotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Slot added successfully.")
            return redirect("technical")
    else:
        form = ScheduleSlotForm(initial=initial)

    return render(request, "edit_slot.html", {"form": form, "slot": None, "title": "Add Slot"})

@staff_member_required
def add_legislative_slot(request):
    initial = {}
    week_id = request.GET.get("week")
    instructor_id = request.GET.get("instructor")

    if week_id:
        initial["week"] = week_id
    if instructor_id:
        initial["instructor"] = instructor_id

    if request.method == "POST":
        form = LegislativeScheduleSlotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Slot added successfully.")
            return redirect("legislative")
    else:
        form = LegislativeScheduleSlotForm(initial=initial)

    return render(request, "edit_slot.html", {"form": form, "slot": None, "title": "Add Slot"})


@staff_member_required
def edit_technical_slot(request, slot_id):
    from .forms import ScheduleSlotForm
    slot = get_object_or_404(ScheduleSlot, pk=slot_id)

    if request.method == "POST":
        form = ScheduleSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, "Slot updated successfully.")
            return redirect("technical")
    else:
        form = ScheduleSlotForm(instance=slot)

    return render(request, "edit_slot.html", {"form": form, "slot": slot})

@staff_member_required
def edit_legislative_slot(request, slot_id):
    from .forms import LegislativeScheduleSlotForm
    slot = get_object_or_404(LegislativeScheduleSlot, pk=slot_id)

    if request.method == "POST":
        form = LegislativeScheduleSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, "Slot updated successfully.")
            return redirect("legislative")
    else:
        form = LegislativeScheduleSlotForm(instance=slot)

    return render(request, "edit_slot.html", {"form": form, "slot": slot})


@staff_member_required
def delete_technical_slot(request, slot_id):
    slot = get_object_or_404(ScheduleSlot, pk=slot_id)

    if request.method == "POST":
        slot.delete()
        messages.success(request, "Slot deleted successfully.")
        return redirect("technical")

    return render(request, "confirm_delete.html", {"object": slot, "object_type": "Slot"})


@staff_member_required
def delete_legislative_slot(request, slot_id):
    slot = get_object_or_404(LegislativeScheduleSlot, pk=slot_id)

    if request.method == "POST":
        slot.delete()
        messages.success(request, "Slot deleted successfully.")
        return redirect("legislative")

    return render(request, "confirm_delete.html", {"object": slot, "object_type": "Slot"})


@staff_member_required
def edit_technical_week(request, week_id):
    from .forms import TrainingWeekForm
    week = get_object_or_404(TrainingWeek, pk=week_id)

    if request.method == "POST":
        form = TrainingWeekForm(request.POST, instance=week)
        if form.is_valid():
            form.save()
            messages.success(request, "Week updated successfully.")
            return redirect("technical")
    else:
        form = TrainingWeekForm(instance=week)

    return render(request, "edit_week.html", {"form": form, "week": week})

@staff_member_required
def edit_legislative_week(request, week_id):
    from .forms import TrainingWeekForm
    week = get_object_or_404(TrainingWeek, pk=week_id)

    if request.method == "POST":
        form = TrainingWeekForm(request.POST, instance=week)
        if form.is_valid():
            form.save()
            messages.success(request, "Week updated successfully.")
            return redirect("legislative")
    else:
        form = TrainingWeekForm(instance=week)

    return render(request, "edit_week.html", {"form": form, "week": week})


@staff_member_required
def delete_technical_week(request, week_id):
    week = get_object_or_404(TrainingWeek, pk=week_id)

    if request.method == "POST":
        week.delete()
        messages.success(request, "Week deleted successfully.")
        return redirect("technical")

    return render(request, "confirm_delete.html", {"object": week, "object_type": "Week"})

@staff_member_required
def delete_legislative_week(request, week_id):
    week = get_object_or_404(TrainingWeek, pk=week_id)

    if request.method == "POST":
        week.delete()
        messages.success(request, "Week deleted successfully.")
        return redirect("legislative")

    return render(request, "confirm_delete.html", {"object": week, "object_type": "Week"})

@staff_member_required
def edit_instructor_technical(request, instructor_id):
    from .forms import InstructorForm
    instructor = get_object_or_404(Instructor, pk=instructor_id)

    if request.method == "POST":
        form = InstructorForm(request.POST, instance=instructor)
        if form.is_valid():
            form.save()
            messages.success(request, "Instructor updated successfully.")
            return redirect("technical")
    else:
        form = InstructorForm(instance=instructor)

    return render(request, "edit_instructor.html", {"form": form, "instructor": instructor})


@staff_member_required
def delete_instructor_technical(request, instructor_id):
    instructor = get_object_or_404(Instructor, pk=instructor_id)

    if request.method == "POST":
        instructor.delete()
        messages.success(request, "Instructor deleted successfully.")
        return redirect("technical")

    return render(request, "confirm_delete.html", {"object": instructor, "object_type": "Instructor"})

@staff_member_required
def edit_instructor_legislative(request, instructor_id):
    from .forms import InstructorForm
    instructor = get_object_or_404(Instructor, pk=instructor_id)

    if request.method == "POST":
        form = InstructorForm(request.POST, instance=instructor)
        if form.is_valid():
            form.save()
            messages.success(request, "Instructor updated successfully.")
            return redirect("legislative")
    else:
        form = InstructorForm(instance=instructor)

    return render(request, "edit_instructor.html", {"form": form, "instructor": instructor})


@staff_member_required
def delete_instructor_legislative(request, instructor_id):
    instructor = get_object_or_404(Instructor, pk=instructor_id)

    if request.method == "POST":
        instructor.delete()
        messages.success(request, "Instructor deleted successfully.")
        return redirect("legislative")

    return render(request, "confirm_delete.html", {"object": instructor, "object_type": "Instructor"})

def bookings_list(request):
    technical_bookings = TrainingBooking.objects.filter(category="technical").select_related("slot", "slot__instructor", "slot__week").order_by("slot__week__start_date", "slot__week__end_date", "slot__instructor__name", "-created_at")
    legislative_bookings = LegislativeBooking.objects.filter(category="legislative").select_related("slot", "slot__instructor", "slot__week").order_by("slot__week__start_date", "slot__week__end_date", "slot__instructor__name", "-created_at")
    operator_bookings = OperatorTrainingBooking.objects.all(

    )
    context = {
        "technical_bookings": technical_bookings,
        "legislative_bookings": legislative_bookings,
        "operator_bookings" : operator_bookings,
    }
    return  render(request, "bookings_list.html", context)


def send_booking_acceptance_email(booking, booking_type):
    recipients = []

    if getattr(booking, 'admin_email', None):
        recipients.append(booking.admin_email)

    if booking_type == "legislative":
        supervisor= getattr(booking, 'supervisor_email', None)
        if supervisor:
            recipients.append(booking.supervisor_email)

    else:
        candidate = getattr(booking, 'candidate_email', None)
        if candidate:
            recipients.append(booking.candidate_email)

    recipients = list(set(recipients))

    if not recipients:
        return

    if booking_type == "legislative":
        title = getattr(booking.slot, "training_title", "training") if booking.slot else "training"
        subject = "Your legislative training booking has been accepted"
        body = (
            f"Hello {booking.full_name},\n\n"
            f"Your booking for {title} has been accepted.\n"
            "Please ensure you have all the necessary documents and arrive on time for your training.\n\n"
            "Kind regards,\n"
            "Booking Team"
        )

    else:
        title = getattr(booking.slot, "training_title", "training") if booking.slot else "training"
        subject = "Your technical training booking has been accepted"
        body = (
            f"Hello {booking.full_name},\n\n"
            f"Your booking for {title} has been accepted.\n"
            "Please ensure you have all the necessary documents and arrive on time for your training.\n\n"
            "Kind regards,\n"
            "Booking Team"
        )

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)


def send_booking_cancellation_email(booking, booking_type):
    recipients = []

    if getattr(booking, 'admin_email', None):
        recipients.append(booking.admin_email)

    if booking_type == "legislative":
        supervisor= getattr(booking, 'supervisor_email', None)
        if supervisor:
            recipients.append(booking.supervisor_email)

    else:
        candidate = getattr(booking, 'candidate_email', None)
        if candidate:
            recipients.append(booking.candidate_email)

    recipients = list(set(recipients))

    if not recipients:
        return

    if booking_type == "legislative":
        title = getattr(booking.slot, "training_title", "training") if booking.slot else "training"
        subject = "Your legislative training booking has been cancelled"
        body = (
            f"Hello {booking.full_name},\n\n"
            f"Your booking for {title} has been cancelled.\n"
            "If this was a mistake, please contact our team to arrange the next steps.\n\n"
            "Kind regards,\n"
            "Booking Team"
        )
    else:
        title = getattr(booking.slot, "training_title", "training") if booking.slot else "training"
        subject = "Your technical training booking has been cancelled"
        body = (
            f"Hello {booking.full_name},\n\n"
            f"Your booking for {title} has been cancelled.\n"
            "If this was a mistake, please contact our team to arrange the next steps.\n\n"
            "Kind regards,\n"
            "Booking Team"
        )

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)


def accept_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(TrainingBooking, id=booking_id)
        if not booking.is_accepted:
            booking.is_accepted = True
            booking.save()
            send_booking_acceptance_email(booking, "technical")
    return redirect('bookings_list')

def build_decline_email_content(booking, booking_type):
    title = getattr(booking.slot, "training_title", "training") if booking.slot else "training"
    if booking_type in ["legislative", "technical"]:
        subject = f"Your {booking_type} training booking has been declined"
    else:
        subject = f"Your {booking_type} training booking has been declined"

    body = (
        f"Hello {booking.full_name},\n\n"
        f"We are sorry to let you know that your booking for {title} has been declined.\n"
        "Please contact our team if you would like to discuss your options or arrange an alternative booking.\n\n"
        "Kind regards,\n"
        "Technical Training Team"
    )
    return subject, body


def send_decline_email(booking, booking_type, subject=None, message=None):
    recipients = []

    if getattr(booking, 'admin_email', None):
        recipients.append(booking.admin_email)

    if booking_type == "legislative":
        supervisor= getattr(booking, 'supervisor_email', None)
        if supervisor:
            recipients.append(booking.supervisor_email)

    else:
        candidate = getattr(booking, 'candidate_email', None)
        if candidate:
            recipients.append(booking.candidate_email)

    recipients = list(set(recipients))

    if not recipients:
        return

    default_subject, default_message = build_decline_email_content(booking, booking_type)
    subject = subject if subject is not None else default_subject
    message = message if message is not None else default_message
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)


def preview_decline_booking(request, booking_id):
    booking = get_object_or_404(TrainingBooking, id=booking_id)
    booking_type = "technical"
    default_subject, default_message = build_decline_email_content(booking, booking_type)

    if request.method == 'POST': 
        subject = request.POST.get('subject', default_subject)
        message = request.POST.get('message', default_message)
        booking.is_declined = True
        booking.slot = None
        booking.save()
        send_decline_email(booking, booking_type, subject=subject, message=message)
        return redirect('bookings_list')

    return render(request, 'decline_email_preview.html', {
        'booking': booking,
        'subject': default_subject,
        'message': default_message,
        'booking_type': booking_type,
    })


def decline_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(TrainingBooking, id=booking_id)
        booking.is_declined = True
        booking.slot = None
        booking.save()
        send_decline_email(booking, "technical")
    return redirect('bookings_list')


def cancel_booking(request, booking_id):
    if request.method == 'POST':
        booking= get_object_or_404(TrainingBooking, id=booking_id)
        booking.is_accepted = False
        booking.is_cancelled = True
        booking.slot = None
        booking.save()
        send_booking_cancellation_email(booking, "technical")
    return redirect('bookings_list')


def delete_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(TrainingBooking, id=booking_id)
        booking.delete()
    return redirect('bookings_list')

def accept_booking_legislative(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(LegislativeBooking, id=booking_id)
        if not booking.is_accepted:
            booking.is_accepted = True
            booking.save()
            send_booking_acceptance_email(booking, "legislative")
    return redirect('bookings_list')

def preview_decline_booking_legislative(request, booking_id):
    booking = get_object_or_404(LegislativeBooking, id=booking_id)
    default_subject, default_message = build_decline_email_content(booking, "legislative")

    if request.method == 'POST':
        subject = request.POST.get('subject', default_subject)
        message = request.POST.get('message', default_message)
        booking.is_declined = True
        booking.slot = None
        booking.save()
        send_decline_email(booking, "legislative", subject=subject, message=message)
        return redirect('bookings_list')

    return render(request, 'decline_email_preview.html', {
        'booking': booking,
        'subject': default_subject,
        'message': default_message,
        'booking_type': 'legislative',
    })


def decline_booking_legislative(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(LegislativeBooking, id=booking_id)
        booking.is_declined = True
        booking.slot = None
        booking.save()
        send_decline_email(booking, "legislative")
    return redirect('bookings_list')


def cancel_booking_legislative(request, booking_id):
    if request.method == 'POST':
        booking= get_object_or_404(LegislativeBooking, id=booking_id)
        booking.is_accepted = False
        booking.is_cancelled = True
        booking.slot = None
        booking.save()
        send_booking_cancellation_email(booking, "legislative")
    return redirect('bookings_list')


def delete_booking_legislative(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(LegislativeBooking, id=booking_id)
        booking.delete()
    return redirect('bookings_list')


def mark_operator_done(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(OperatorTrainingBooking, id=booking_id)
        booking.is_done = True
        booking.save()
    return redirect('bookings_list')


@staff_member_required
def delete_operator_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(OperatorTrainingBooking, id=booking_id)
        if booking.is_done:
            booking.delete()
    return redirect('bookings_list')