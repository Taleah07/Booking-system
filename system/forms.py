import re

from django import forms
from .models import TrainingBooking, TrainingWeek, ScheduleSlot, Instructor, LegislativeBooking , LegislativeScheduleSlot , OperatorTrainingBooking


class BookingForm(forms.ModelForm):
    COMPANY_CHOICES = [
        ("Bell Internal", "Bell Internal"),
        ("Dealers", "Dealers"),
    ]
    PHONE_COUNTRY_CHOICES = [
        ("+27", "South Africa (+27)"),
        ("+1", "United States / Canada (+1)"),
        ("+44", "United Kingdom (+44)"),
        ("+31", "Netherlands (+31)"),
        ("+32", "Belgium (+32)"),
        ("+49", "Germany (+49)"),
        ("+61", "Australia (+61)"),
        ("+971", "UAE (+971)"),
        ("+33", "France (+33)"),
        ("+34", "Spain (+34)"),
        ("+39", "Italy (+39)"),
        ("+351", "Portugal (+351)"),
        ("+41", "Switzerland (+41)"),
        ("+46", "Sweden (+46)"),
        ("+47", "Norway (+47)"),
        ("+48", "Poland (+48)"),
        ("+52", "Mexico (+52)"),
        ("+55", "Brazil (+55)"),
        ("+56", "Chile (+56)"),
        ("+57", "Colombia (+57)"),
        ("+60", "Malaysia (+60)"),
        ("+65", "Singapore (+65)"),
        ("+66", "Thailand (+66)"),
        ("+81", "Japan (+81)"),
        ("+82", "South Korea (+82)"),
        ("+86", "China (+86)"),
        ("+91", "India (+91)"),
        ("+92", "Pakistan (+92)"),
        ("+94", "Sri Lanka (+94)"),
        ("+972", "Israel (+972)"),
        ("+966", "Saudi Arabia (+966)"),
        ("+27", "Other / not listed"),
    ]
   
    company = forms.CharField(
        label="Company",
        required=True,
        initial="Bell Internal",
        widget=forms.Select(choices=COMPANY_CHOICES),
    )

    full_name = forms.CharField(required=True)
    surname = forms.CharField(required=True)
    id_number = forms.CharField(required=True)
    admin_email = forms.EmailField(required=True)
    candidate_email = forms.EmailField(required=True)
    phone_country_code = forms.ChoiceField(
        choices=PHONE_COUNTRY_CHOICES,
        required=True,
        label="Region / Dial code",
        initial="+27",
    )
    phone = forms.CharField(
        required=True,
        label="Phone number",
        widget=forms.TextInput(attrs={"placeholder": "e.g. 0821234567", "inputmode": "numeric"}),
    )
    company_number = forms.CharField(required=False)
    company_name = forms.CharField(required=True)

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        digits_only = re.sub(r"\D", "", phone)
        if not digits_only:
            raise forms.ValidationError("Enter a valid phone number.")
        return digits_only

    def clean(self):
        cleaned_data = super().clean()
        country_code = cleaned_data.get("phone_country_code")
        phone = cleaned_data.get("phone")
        if country_code and phone:
            cleaned_data["phone"] = f"{country_code} {phone.strip()}"
        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.phone = self.cleaned_data.get("phone", booking.phone)
        if commit:
            booking.save()
        return booking

    class Meta:
        model = TrainingBooking
        fields = ["full_name", "surname", "id_number", "admin_email", "candidate_email", "phone_country_code", "phone", "company", "company_number", "company_name"]
        field_order = ["full_name", "surname", "id_number", "admin_email", "candidate_email", "phone_country_code", "phone", "company", "company_number", "company_name"]
        labels = {
            "id_number": "ID number",
            "company_number": "Company number",
        }

 

class LegislativeBookingForm(forms.ModelForm):
    PHONE_COUNTRY_CHOICES = [
        ("+27", "South Africa (+27)"),
        ("+1", "United States / Canada (+1)"),
        ("+44", "United Kingdom (+44)"),
        ("+31", "Netherlands (+31)"),
        ("+32", "Belgium (+32)"),
        ("+49", "Germany (+49)"),
        ("+61", "Australia (+61)"),
        ("+971", "UAE (+971)"),
        ("+33", "France (+33)"),
        ("+34", "Spain (+34)"),
        ("+39", "Italy (+39)"),
        ("+351", "Portugal (+351)"),
        ("+41", "Switzerland (+41)"),
        ("+46", "Sweden (+46)"),
        ("+47", "Norway (+47)"),
        ("+48", "Poland (+48)"),
        ("+52", "Mexico (+52)"),
        ("+55", "Brazil (+55)"),
        ("+56", "Chile (+56)"),
        ("+57", "Colombia (+57)"),
        ("+60", "Malaysia (+60)"),
        ("+65", "Singapore (+65)"),
        ("+66", "Thailand (+66)"),
        ("+81", "Japan (+81)"),
        ("+82", "South Korea (+82)"),
        ("+86", "China (+86)"),
        ("+91", "India (+91)"),
        ("+92", "Pakistan (+92)"),
        ("+94", "Sri Lanka (+94)"),
        ("+972", "Israel (+972)"),
        ("+966", "Saudi Arabia (+966)"),
        ("+27", "Other / not listed"),
    ]
    company_number = forms.CharField(required=True, label="Company Number")
    department = forms.CharField(required=True, label="Department")
    full_name = forms.CharField(required=True)
    surname = forms.CharField(required=True)
    id_number = forms.CharField(required=True)
    admin_email = forms.EmailField(required=True)
    supervisor_email = forms.EmailField(required=True)
    phone_country_code = forms.ChoiceField(
        choices=PHONE_COUNTRY_CHOICES,
        required=True,
        label="Region / Dial code",
        initial="+27",
    )
    phone = forms.CharField(
        required=True,
        label="Phone number",
        widget=forms.TextInput(attrs={"placeholder": "e.g. 0821234567", "inputmode": "numeric"}),
    )
    id_pdf = forms.FileField(required=True, label="ID Document (PDF)")
    education_pdf = forms.FileField(required=True, label="Education Document (PDF)")
    medical_pdf = forms.FileField(required=True, label="Medical Document (PDF)")
    drivers_license_pdf = forms.FileField(required=True, label="Driver's License Document (PDF)")
    previous_license_pdf = forms.FileField(required=True, label="Previous License Document (PDF)")

    def __init__(self, *args, slot=None, **kwargs):
        super().__init__(*args, **kwargs)
        title = (getattr(slot, "training_title", "") or "").lower()
        self.fields["drivers_license_pdf"].required = "forklift" in title or "reach truck" in title
        self.fields["previous_license_pdf"].required = "refresher" in title

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        digits_only = re.sub(r"\D", "", phone)
        if not digits_only:
            raise forms.ValidationError("Enter a valid phone number.")
        return digits_only

    def clean(self):
        cleaned_data = super().clean()
        country_code = cleaned_data.get("phone_country_code")
        phone = cleaned_data.get("phone")
        if country_code and phone:
            cleaned_data["phone"] = f"{country_code} {phone.strip()}"
        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.phone = self.cleaned_data.get("phone", booking.phone)
        if commit:
            booking.save()
        return booking

    class Meta:
        model = LegislativeBooking
        fields = ["full_name", "surname", "id_number", "admin_email","supervisor_email", "phone_country_code", "phone", "company_number", "department", "id_pdf", "education_pdf", "medical_pdf", "drivers_license_pdf","previous_license_pdf"]
        field_order = ["full_name", "surname", "id_number", "admin_email", "supervisor_email", "phone_country_code", "phone", "company_number", "department", "id_pdf", "education_pdf", "medical_pdf", "drivers_license_pdf","previous_license_pdf"]
        labels = {
            "id_number": "ID number",
            "company_number": "Company number",
        }

class OperatorBookingForm(forms.ModelForm):
    COMPANY_CHOICES = [
        ("Customer", "Customer"),
        ("Dealer", "Dealer"),
    ]
       
    company = forms.CharField(
        label="Company",
        required=True,
        initial="",
        widget=forms.Select(choices=COMPANY_CHOICES),
    )

    COURSE_TYPE_CHOICES = [
        ("Refresher", "Refresher"),
        ("Novice", "Novice"),
    ]
           
    course_type = forms.CharField(
        label="Course type",
        required=True,
        initial="",
        widget=forms.Select(choices=COURSE_TYPE_CHOICES),
    )

    LOCATION_CHOICES = [
        ("Bell", "Bell"),
        ("Customer", "Customer"),
    ]
           
    location = forms.CharField(
        label="Location",
        required=True,
        initial="",
        widget=forms.Select(choices=LOCATION_CHOICES),
    )

    branch = forms.CharField(required=True)
    full_name = forms.CharField(required=True)
    surname = forms.CharField(required=True)
    admin_email = forms.EmailField(required=True)
    company_name = forms.CharField(required=True)
    machine_name = forms.CharField(required=True)
    number_of_deligates = forms.IntegerField(required=True)
    location_name = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        location = cleaned_data.get('location')
        location_name = cleaned_data.get('location_name')

        if location == 'Customer' and not location_name:
            self.add_error('location_name', 'This field is required when location is customer.')

        return cleaned_data
        

    def save(self, commit=True):
        booking = super().save(commit=False)
        if commit:
            booking.save()
        return booking

    class Meta:
        model = OperatorTrainingBooking
        fields = ["branch","full_name", "surname", "admin_email", "company", "company_name", "course_type", "machine_name", "number_of_deligates", "location", "location_name"]
        field_order = ["branch","full_name", "surname", "admin_email", "company", "company_name", "course_type", "machine_name", "number_of_deligates", "location", "location_name"]
        labels = {
            "id_number": "ID number",
            "company_number": "Company number",
        }


class TrainingWeekForm(forms.ModelForm):
    class Meta:
        model = TrainingWeek
        fields = ["start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def save(self, commit=True):
        week = super().save(commit=False)
        start_date = self.cleaned_data.get("start_date")
        end_date = self.cleaned_data.get("end_date")
        if start_date and end_date:
            week.week_range = week.display_name
        elif start_date:
            week.week_range = start_date.strftime("%d %b %Y")
        elif end_date:
            week.week_range = end_date.strftime("%d %b %Y")
        if commit:
            week.save()
        return week


class ScheduleSlotForm(forms.ModelForm):
    class Meta:
        model = ScheduleSlot
        fields = ["week", "instructor", "training_title", "venue_info", "capacity"]

class LegislativeScheduleSlotForm(forms.ModelForm):
    class Meta:
        model = LegislativeScheduleSlot
        fields = ["week", "instructor", "training_title", "venue_info", "capacity"]



class InstructorForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = ["name"]
