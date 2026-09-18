from datetime import date, timedelta

from django.db import models

class Instructor(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=[("technical", "Technical"), ("legislative", "Legislative")], default="technical")
    def __str__(self):
        return self.name


class TrainingWeek(models.Model):
    week_range = models.CharField(max_length=100, unique=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['start_date']

    @property
    def display_name(self):
        if self.start_date and self.end_date:
            if self.start_date == self.end_date:
                return self.start_date.strftime('%d %b %Y')
            return f"{self.start_date.strftime('%d %b %Y')} - {self.end_date.strftime('%d %b %Y')}"
        return self.week_range or ""

    @property
    def is_booking_closed(self):
        today = date.today()
        if self.end_date and self.end_date < today:
            return True
        if not self.start_date:
            return False
        return today >= self.start_date - timedelta(days=7)

    def __str__(self):
        return self.display_name


class ScheduleSlot(models.Model):
    week = models.ForeignKey(TrainingWeek, models.CASCADE, related_name="slots")
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name="slots")
    training_title = models.CharField(max_length=200, help_text="e.g., ADT E# PIN 3 (5 Days)")
    venue_info = models.CharField(max_length=100, help_text="e.g., JetPark")
    prerequisite = models.TextField(blank=True, help_text="Optional prerequisite shown on the booking form")
    capacity = models.PositiveIntegerField(default=12, help_text="Total seats available")
    

    class Meta:
        unique_together = ("instructor", "week")

    @property
    def booked_count(self):
        tech_count = self.technical_booking.count()
        return tech_count 

    @property
    def title_prerequisites(self):
        title = self.training_title.casefold()
        if "allison transmission" in title:
            return ["Own laptop and an active Allison license", "Online training Allison Transimission Course"]
        if "bell programming & fleetmatic" in title:
            return ["Own laptop and UNICOM" , "Online training OMNI360"]
        if "mercedes" in title or "xentry" in title or "engine" in title:
            return ["Own laptop and Xentry Tool/SerDia 4.0", "Online training OM471/473 Engine Course"]
        if "service & maintenance" in title:
            return["Product training on a specific machine you require service and maintenance on"]
        if "adt" in title:
            return["Online training Basic Electrical & Hydraulic (Dealers & Customers)", "Online training MSSM and Stage 3 ADT(Bell internal mechanics)"]
        if "grader" in title:
            return ["Online training Basic Electrical & Hydraulic"]
        if "jcb large wheeler loader" in title or "jcb 3cx" in title or "jcb fel" in title:
            return ["JCB online training first row completed", "FEL on the 2nd row completed"]
        if "jcb backhoe loader" in title or "jcb bhl" in title:
            return ["JCB online training first row completed ", "BHL on the 2nd row completed"]
        if "jcb single drum roller" in title or "jcb roller" in title:
            return ["JCB online training first row completed"]
        if "jcb telehandler" in title:
            return ["JCB online training first row completed", "Telehandler on the 2nd row completed"]
        if "jcb excavator" in title:
            return ["JCB online training first row completed", "Excavator on the 2nd row completed"]
        if "jcb skidsteer" in title:
            return ["JCB online training first row completed", "Skidsteer on the 2nd row completed"]
        return []
    
    @property
    def seats_remaining(self):
        return max(self.capacity - self.booked_count, 0)
    
    def __str__(self):
        return f"{self.instructor} - {self.week}: {self.training_title}"
    

class LegislativeScheduleSlot(models.Model):    
    week = models.ForeignKey(TrainingWeek, models.CASCADE, related_name="legislative_slots")
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name="legislative_slots")
    training_title = models.CharField(max_length=200, help_text="e.g., ADT E# PIN 3 (5 Days)")
    venue_info = models.CharField(max_length=100, help_text="e.g., JetPark")
    capacity = models.PositiveIntegerField(default=12, help_text="Total seats available")

    class Meta:
        verbose_name = "Legislative Schedule Slot"
        verbose_name_plural = "Legislative Schedule Slots"

    @property
    def booked_count(self):
        legis_count = self.legislative_booking.count()
        return legis_count

    @property
    def seats_remaining(self):
        return max(self.capacity - self.booked_count, 0)

    def __str__(self):
        return f"{self.instructor} - {self.week}: {self.training_title}"


class TrainingBooking(models.Model):
    slot = models.ForeignKey(ScheduleSlot, on_delete=models.CASCADE, related_name="technical_booking", null=True, blank=True )
    full_name = models.CharField(max_length=150)
    admin_email = models.EmailField(blank=True, null=True)
    candidate_email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    company = models.CharField(max_length=150, blank=True)
    surname = models.CharField(max_length=100, default="")
    id_number = models.CharField(max_length=50, blank=True)
    company_number = models.CharField(max_length=50, blank=True)
    company_name = models.CharField(max_length=150, blank=True)
    category = models.CharField(max_length=20, default="technical")
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    is_declined = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} -> {self.slot}"
 

class LegislativeBooking(models.Model):
    slot = models.ForeignKey(LegislativeScheduleSlot, on_delete=models.CASCADE, related_name="legislative_booking", null=True, blank=True)
    full_name = models.CharField(max_length=150)
    admin_email= models.EmailField(blank=True, null=True)
    supervisor_email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    department = models.CharField(max_length=150, blank=True)
    surname = models.CharField(max_length=100, default="")
    id_number = models.CharField(max_length=50, blank=True)
    company_number = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=20, default="legislative")
    id_pdf = models.FileField(upload_to = 'booking/legislative/ids', blank=True, null=True)
    education_pdf = models.FileField(upload_to = 'booking/legislative/education', blank=True, null=True)
    medical_pdf = models.FileField(upload_to = 'booking/legislative/medical', blank=True, null=True)
    drivers_license_pdf = models.FileField(upload_to = 'booking/legislative/drivers_license', blank=True, null=True)
    previous_license_pdf = models.FileField(upload_to = 'booking/legislative/previous_license', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    is_declined = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} -> {self.slot}"

class OperatorTrainingBooking(models.Model):
    full_name = models.CharField(max_length=150)
    admin_email = models.EmailField(blank=True, null=True)
    company = models.CharField(max_length=150, blank=True)
    company_name = models.CharField(max_length=150, blank=True)
    surname = models.CharField(max_length=100, default="")
    branch = models.CharField(max_length=100, blank=True)
    course_type = models.CharField(max_length=150, blank=True)
    machine_name = models.CharField(max_length=150, blank=True)
    number_of_deligates = models.IntegerField( blank=True)
    location = models.CharField(max_length=150, blank=True)
    location_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_done = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name