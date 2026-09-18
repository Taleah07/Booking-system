from datetime import date, timedelta

from django.contrib.admin.sites import site
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .forms import BookingForm
from .models import (
    Instructor,
    LegislativeBooking,
    LegislativeScheduleSlot,
    ScheduleSlot,
    TrainingBooking,
    TrainingWeek,
)
from django.contrib.auth import get_user_model


class AdminCalendarTests(TestCase):
    def test_calendar_models_are_registered_in_admin(self):
        self.assertIn(Instructor, site._registry)
        self.assertIn(TrainingWeek, site._registry)
        self.assertIn(ScheduleSlot, site._registry)


class TrainingBookingTests(TestCase):
    def setUp(self):
        self.instructor = Instructor.objects.create(name="Alex")
        self.week = TrainingWeek.objects.create(week_range="Week 1")
        self.slot = ScheduleSlot.objects.create(
            week=self.week,
            instructor=self.instructor,
            training_title="ADT E# PIN 3 (5 Days)",
            venue_info="JetPark",
        )

    def test_technical_page_lists_training_slots(self):
        response = self.client.get(reverse("technical"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ADT E# PIN 3 (5 Days)")
        self.assertContains(response, "Book this training")

    def test_booking_form_saves_a_booking(self):
        response = self.client.post(
            reverse("book_training", args=[self.slot.id]),
            {
                "full_name": "Jane",
                "surname": "Doe",
                "id_number": "9988776655",
                "email": "jane@example.com",
                "phone": "0123456789",
                "company": "Bell Internal",
                "bell_branch": "Bell Richards Bay",
                "company_number": "12345",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(TrainingBooking.objects.count(), 1)
        booking = TrainingBooking.objects.get()
        self.assertEqual(booking.slot, self.slot)
        self.assertEqual(booking.full_name, "Jane")
        self.assertEqual(booking.surname, "Doe")
        self.assertEqual(booking.id_number, "9988776655")
        self.assertEqual(booking.company_number, "12345")
        self.assertEqual(booking.bell_branch, "Bell Richards Bay")

    def test_booking_form_renders_company_dropdown(self):
        response = self.client.get(reverse("book_training", args=[self.slot.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="company"')
        self.assertContains(response, 'value="Bell Internal"')
        self.assertContains(response, 'value="Dealers"')
        self.assertEqual(response.context["form"]["company"].value(), "Bell Internal")


    def test_booking_form_requires_company_number_for_bell_internal(self):
        form = BookingForm(
            data={
                "full_name": "Jane",
                "surname": "Doe",
                "id_number": "9988776655",
                "email": "jane@example.com",
                "phone": "0123456789",
                "company": "Bell Internal",
                "bell_branch": "Bell Equipment Richards Bay",
                "company_number": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("company_number", form.errors)

    def test_booking_form_requires_dealer_for_dealers(self):
        form = BookingForm(
            data={
                "full_name": "Jane",
                "surname": "Doe",
                "id_number": "9988776655",
                "email": "jane@example.com",
                "phone": "0123456789",
                "company": "Dealers",
                "dealer": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("dealer", form.errors)

    def test_booking_form_shows_bell_branch_dropdown_for_bell_internal(self):
        response = self.client.get(reverse("book_training", args=[self.slot.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="bell_branch"')
        self.assertContains(response, 'id="bell-branch-group"')
        self.assertContains(response, 'display: none;')
        self.assertContains(response, 'Bell Richards Bay')
        self.assertContains(response, 'Bell Midrand')

    def test_booking_form_shows_dealer_dropdown_for_dealers(self):
        response = self.client.get(reverse("book_training", args=[self.slot.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="dealer"')
        self.assertContains(response, 'id="dealer-group"')
        self.assertContains(response, 'type="text"')

    def test_company_number_renders_after_company(self):
        response = self.client.get(reverse("book_training", args=[self.slot.id]))

        self.assertEqual(response.status_code, 200)
        company_pos = response.content.decode().index('id="id_company"')
        company_number_pos = response.content.decode().index('id="id_company_number"')
        self.assertLess(company_pos, company_number_pos)

    def test_booking_sends_confirmation_emails(self):
        mail.outbox = []

        response = self.client.post(
            reverse("book_training", args=[self.slot.id]),
            {
                "full_name": "Jane",
                "surname": "Doe",
                "id_number": "9988776655",
                "email": "jane@example.com",
                "phone": "0123456789",
                "company": "Bell Equipment",
                "company_number": "12345",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)

        user_email = mail.outbox[0]
        admin_email = mail.outbox[1]

        self.assertEqual(user_email.to, ["jane@example.com"])
        self.assertIn("Training booking confirmation", user_email.subject)
        self.assertIn("Hello Jane", user_email.body)

        self.assertEqual(admin_email.to, ["admin@example.com"])
        self.assertIn("New training booking received", admin_email.subject)
        self.assertIn("Name: Jane", admin_email.body)

    def test_accept_booking_sends_confirmation_email(self):
        booking = TrainingBooking.objects.create(
            slot=self.slot,
            full_name="Jane Doe",
            surname="Doe",
            id_number="1122334455",
            admin_email="admin@example.com",
            candidate_email="candidate@example.com",
            phone="0123456789",
            company="Bell Equipment",
            company_number="12345",
        )

        mail.outbox = []

        response = self.client.post(reverse("accept_booking", args=[booking.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["candidate@example.com"])
        self.assertIn("accepted", mail.outbox[0].subject.lower())
        self.assertIn("Jane Doe", mail.outbox[0].body)

    def test_accept_legislative_booking_sends_confirmation_email(self):
        legislative_slot = LegislativeScheduleSlot.objects.create(
            week=self.week,
            instructor=self.instructor,
            training_title="Legislative Compliance",
            venue_info="Cape Town",
        )
        booking = LegislativeBooking.objects.create(
            slot=legislative_slot,
            full_name="John Smith",
            surname="Smith",
            id_number="9988776655",
            admin_email="admin@example.com",
            candidate_email="candidate.leg@example.com",
            phone="0123456789",
            department="Safety",
            company_number="54321",
        )

        mail.outbox = []

        response = self.client.post(reverse("accept_booking_legislative", args=[booking.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["candidate.leg@example.com"])
        self.assertIn("accepted", mail.outbox[0].subject.lower())
        self.assertIn("John Smith", mail.outbox[0].body)

    def test_accept_booking_sends_to_candidate_and_company_email(self):
        booking = TrainingBooking.objects.create(
            slot=self.slot,
            full_name="Jane Doe",
            surname="Doe",
            id_number="1122334455",
            admin_email="training@bellequipment.co.za",
            candidate_email="candidate@gmail.com",
            phone="0123456789",
            company="Bell Equipment",
            company_number="12345",
        )

        mail.outbox = []

        response = self.client.post(reverse("accept_booking", args=[booking.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], "candidate@gmail.com")
        self.assertIn("training@bellequipment.co.za", mail.outbox[0].to)
        self.assertIn("accepted", mail.outbox[0].subject.lower())
        self.assertIn("Jane Doe", mail.outbox[0].body)

    def test_cancel_booking_sends_cancellation_email(self):
        booking = TrainingBooking.objects.create(
            slot=self.slot,
            full_name="Jane Doe",
            surname="Doe",
            id_number="1122334455",
            admin_email="admin@example.com",
            candidate_email="candidate@example.com",
            phone="0123456789",
            company="Bell Equipment",
            company_number="12345",
        )

        mail.outbox = []

        response = self.client.post(reverse("cancel_booking", args=[booking.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["candidate@example.com"])
        self.assertIn("cancelled", mail.outbox[0].subject.lower())
        self.assertIn("Jane Doe", mail.outbox[0].body)

    def test_decline_email_can_be_edited_before_sending(self):
        booking = TrainingBooking.objects.create(
            slot=self.slot,
            full_name="Jane Doe",
            surname="Doe",
            id_number="1122334455",
            admin_email="admin@example.com",
            candidate_email="candidate@example.com",
            phone="0123456789",
            company="Bell Equipment",
            company_number="12345",
        )

        mail.outbox = []

        preview_response = self.client.get(reverse("preview_decline_booking", args=[booking.id]))
        self.assertEqual(preview_response.status_code, 200)
        self.assertContains(preview_response, "textarea")

        custom_message = "Unfortunately your booking was declined because the required training date is full."
        response = self.client.post(
            reverse("preview_decline_booking", args=[booking.id]),
            {
                "subject": "Your booking has been declined",
                "message": custom_message,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["candidate@example.com"])
        self.assertEqual(mail.outbox[0].subject, "Your booking has been declined")
        self.assertIn(custom_message, mail.outbox[0].body)

        booking.refresh_from_db()
        self.assertTrue(booking.is_declined)
        self.assertIsNone(booking.slot)

    def test_cancel_legislative_booking_sends_cancellation_email(self):
        legislative_slot = LegislativeScheduleSlot.objects.create(
            week=self.week,
            instructor=self.instructor,
            training_title="Legislative Compliance",
            venue_info="Cape Town",
        )
        booking = LegislativeBooking.objects.create(
            slot=legislative_slot,
            full_name="John Smith",
            surname="Smith",
            id_number="9988776655",
            admin_email="admin@example.com",
            candidate_email="candidate.leg@example.com",
            phone="0123456789",
            department="Safety",
            company_number="54321",
        )

        mail.outbox = []

        response = self.client.post(reverse("cancel_booking_legislative", args=[booking.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["candidate.leg@example.com"])
        self.assertIn("cancelled", mail.outbox[0].subject.lower())
        self.assertIn("John Smith", mail.outbox[0].body)

    def test_booking_list_javascript_keeps_delete_button_after_cancel_or_decline(self):
        response = self.client.get(reverse("bookings_list"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        cancel_block_start = content.index("else if (actionType === 'cancel')")
        cancel_block_end = content.index("}).catch", cancel_block_start)
        cancel_block = content[cancel_block_start:cancel_block_end]
        self.assertIn("delete_booking", cancel_block)
        self.assertIn("Delete", cancel_block)

        decline_block_start = content.index("else if (actionType === 'decline')")
        decline_block_end = content.index("} else if (actionType === 'cancel')", decline_block_start)
        decline_block = content[decline_block_start:decline_block_end]
        self.assertIn("delete_booking", decline_block)
        self.assertIn("Delete", decline_block)

    def test_edit_week_page_renders_form_fields(self):
        response = self.client.get(reverse("edit_week_technical", args=[self.week.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Training Week")
        self.assertContains(response, 'name="start_date"')
        self.assertContains(response, 'name="end_date"')

    def test_delete_cancelled_technical_booking(self):
        booking = TrainingBooking.objects.create(
            slot=self.slot,
            full_name="Jane Doe",
            surname="Doe",
            id_number="1122334455",
            admin_email="admin@example.com",
            candidate_email="candidate@example.com",
            phone="0123456789",
            company="Bell Equipment",
            company_number="12345",
            is_cancelled=True,
        )

        response = self.client.post(reverse("delete_booking", args=[booking.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(TrainingBooking.objects.filter(id=booking.id).exists())

    def test_delete_declined_legislative_booking(self):
        legislative_slot = LegislativeScheduleSlot.objects.create(
            week=self.week,
            instructor=self.instructor,
            training_title="Legislative Compliance",
            venue_info="Cape Town",
        )
        booking = LegislativeBooking.objects.create(
            slot=legislative_slot,
            full_name="John Smith",
            surname="Smith",
            id_number="9988776655",
            admin_email="admin@example.com",
            candidate_email="candidate.leg@example.com",
            phone="0123456789",
            department="Safety",
            company_number="54321",
            is_declined=True,
        )

        response = self.client.post(reverse("delete_booking_legislative", args=[booking.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(LegislativeBooking.objects.filter(id=booking.id).exists())

    def test_seat_count_updates_after_booking(self):
        self.slot.capacity = 1
        self.slot.save(update_fields=["capacity"])

        response = self.client.post(
            reverse("book_training", args=[self.slot.id]),
            {
                "full_name": "Jane Doe",
                "surname": "Doe",
                "id_number": "1122334455",
                "email": "jane@example.com",
                "phone": "0123456789",
                "company": "Bell Equipment",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.seats_remaining, 0)

    def test_booking_is_blocked_when_capacity_is_full(self):
        self.slot.capacity = 1
        self.slot.save(update_fields=["capacity"])
        TrainingBooking.objects.create(
            slot=self.slot,
            full_name="Existing",
            surname="User",
            id_number="0011223344",
            email="existing@example.com",
            phone="0123456789",
            company_number="00001",
        )

        response = self.client.post(
            reverse("book_training", args=[self.slot.id]),
            {
                "full_name": "Jane Doe",
                "surname": "Doe",
                "id_number": "2233445566",
                "email": "jane@example.com",
                "phone": "0123456789",
                "company": "Bell Equipment",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No seats remaining")
        self.assertEqual(TrainingBooking.objects.count(), 1)

    def test_staff_can_export_bookings_csv(self):
        # create a staff user and log in
        User = get_user_model()
        user = User.objects.create_user("staff", "staff@example.com", "password")
        user.is_staff = True
        user.save()
        self.client.login(username="staff", password="password")

        # create a booking
        TrainingBooking.objects.create(
            slot=self.slot,
            full_name="CSV",
            surname="User",
            id_number="5566778899",
            email="csv@example.com",
            phone="000",
            company_number="98765",
        )

        response = self.client.get(reverse("bookings_export"))
        self.assertEqual(response.status_code, 200)
        content_type = response["Content-Type"]
        # Accept CSV or XLSX
        self.assertTrue(
            content_type.startswith("text/csv")
            or content_type.startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        )

        if content_type.startswith("text/csv"):
            self.assertIn("CSV User", response.content.decode())
        else:
            # validate xlsx content contains the full name in one of the cells
            try:
                import openpyxl
                from io import BytesIO

                wb = openpyxl.load_workbook(filename=BytesIO(response.content))
                values = []
                for row in wb.active.iter_rows(values_only=True):
                    values.extend([str(c) for c in row if c])
                self.assertIn("CSV User", " ".join(values))
            except Exception:
                self.fail("XLSX export produced invalid content")

    def test_legislative_page_shows_legislative_slots(self):
        legislative_slot = ScheduleSlot.objects.create(
            week=self.week,
            instructor=self.instructor,
            training_title="Legislative Compliance",
            venue_info="Cape Town",
            category="legislative",
        )

        response = self.client.get(reverse("legislative"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Legislative Compliance")
        self.assertContains(response, "Book this training")

    def test_legislative_booking_is_saved_with_legislative_category(self):
        legislative_slot = ScheduleSlot.objects.create(
            week=self.week,
            instructor=self.instructor,
            training_title="Legislative Compliance",
            venue_info="Cape Town",
            category="legislative",
        )

        response = self.client.post(
            reverse("book_legislative_training", args=[legislative_slot.id]),
            {
                "full_name": "Jane",
                "surname": "Doe",
                "id_number": "9988776655",
                "email": "jane@example.com",
                "phone": "0123456789",
                "company": "Bell Internal",
                "company_number": "12345",
            },
        )

        self.assertEqual(response.status_code, 302)
        booking = TrainingBooking.objects.get()
        self.assertEqual(booking.category, "legislative")

    def test_staff_can_add_a_new_week(self):
        User = get_user_model()
        user = User.objects.create_user("staff", "staff@example.com", "password")
        user.is_staff = True
        user.save()
        self.client.login(username="staff", password="password")

        response = self.client.post(
            reverse("add_week"),
            {"start_date": "2026-09-01", "end_date": "2026-09-05"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            TrainingWeek.objects.filter(start_date=date(2026, 9, 1), end_date=date(2026, 9, 5)).exists()
        )

    def test_staff_can_add_a_new_slot(self):
        User = get_user_model()
        user = User.objects.create_user("staff", "staff@example.com", "password")
        user.is_staff = True
        user.save()
        self.client.login(username="staff", password="password")

        week = TrainingWeek.objects.create(week_range="Week 99")
        instructor = Instructor.objects.create(name="Jamie")

        response = self.client.post(
            reverse("add_slot"),
            {
                "week": week.id,
                "instructor": instructor.id,
                "training_title": "New slot training",
                "venue_info": "Cape Town",
                "capacity": 10,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(ScheduleSlot.objects.filter(training_title="New slot training").exists())

    def test_add_slot_form_is_prefilled_for_selected_blank_cell(self):
        User = get_user_model()
        user = User.objects.create_user("staff", "staff@example.com", "password")
        user.is_staff = True
        user.save()
        self.client.login(username="staff", password="password")

        week = TrainingWeek.objects.create(week_range="Week 100")
        instructor = Instructor.objects.create(name="Taylor")

        response = self.client.get(
            reverse("add_slot"),
            {"week": week.id, "instructor": instructor.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["week"], str(week.id))
        self.assertEqual(response.context["form"].initial["instructor"], str(instructor.id))


class TrainingWeekBookingCutoffTests(TestCase):
    def setUp(self):
        self.instructor = Instructor.objects.create(name="Cutoff instructor")
        self.week = TrainingWeek.objects.create(
            week_range="Cutoff week",
            start_date=date.today() + timedelta(days=6),
            end_date=date.today() + timedelta(days=10),
        )
        self.technical_slot = ScheduleSlot.objects.create(
            week=self.week,
            instructor=self.instructor,
            training_title="Technical cutoff",
            venue_info="JetPark",
        )
        self.legislative_slot = LegislativeScheduleSlot.objects.create(
            week=self.week,
            instructor=self.instructor,
            training_title="Legislative cutoff",
            venue_info="JetPark",
        )

    def test_week_closes_seven_days_before_start(self):
        self.assertTrue(self.week.is_booking_closed)

        open_week = TrainingWeek(
            start_date=date.today() + timedelta(days=8),
            end_date=date.today() + timedelta(days=12),
        )
        self.assertFalse(open_week.is_booking_closed)

    def test_technical_booking_is_blocked_after_cutoff(self):
        response = self.client.get(reverse("book_training_technical", args=[self.technical_slot.id]))

        self.assertRedirects(response, reverse("technical"))
        self.assertEqual(TrainingBooking.objects.count(), 0)

    def test_legislative_booking_is_blocked_after_cutoff(self):
        response = self.client.get(reverse("book_training_legislative", args=[self.legislative_slot.id]))

        self.assertRedirects(response, reverse("legislative"))
        self.assertEqual(LegislativeBooking.objects.count(), 0)

    def test_staff_can_open_technical_booking_after_cutoff(self):
        user = get_user_model().objects.create_user("technical-staff", password="password", is_staff=True)
        self.client.force_login(user)

        response = self.client.get(reverse("book_training_technical", args=[self.technical_slot.id]))

        self.assertEqual(response.status_code, 200)

    def test_staff_can_open_legislative_booking_after_cutoff(self):
        user = get_user_model().objects.create_user("legislative-staff", password="password", is_staff=True)
        self.client.force_login(user)

        response = self.client.get(reverse("book_training_legislative", args=[self.legislative_slot.id]))

        self.assertEqual(response.status_code, 200)


