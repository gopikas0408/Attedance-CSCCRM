from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.db.models import Sum
from django.core.validators import MinValueValidator 
from decimal import Decimal
from cloudinary.models import CloudinaryField


name_validator = RegexValidator(
    regex=r'^[A-Za-z ]+$',
    message="Only alphabets and spaces are allowed."
)

phone_validator = RegexValidator(
    regex=r'^\d{10}$',
    message="Phone number must be exactly 10 digits."
)

email_validator = RegexValidator(
    regex=r'^[\w\.-]+@[\w\.-]+\.\w+$',
    message="Enter a proper email (example: name@gmail.com)"
)



class Student(models.Model):
    first_name = models.CharField(max_length=20, blank=False, validators=[name_validator])
    last_name = models.CharField(max_length=20, blank=False, validators=[name_validator])
    dob = models.DateField()
    phone_no = models.CharField(max_length=10, blank=False, validators=[phone_validator], unique=True)

    gender_choice = [
        ('', 'Select Gender'),
        ('M','Male'),
        ('F','Female'),
        ('O','Others')
    ]
    gender = models.CharField(max_length=10, choices=gender_choice)

    email = models.EmailField(validators=[email_validator],unique=True)
    address = models.TextField()

    guardian_name = models.CharField(max_length=100, blank=False, validators=[name_validator])
    guardian_phone_no = models.CharField(max_length=10, blank=False, validators=[phone_validator], unique=True)
    
    photo=CloudinaryField('student_photos/',null=True, blank=True)
    id_proof=CloudinaryField('id_proofs/',null=True, blank=True, resource_type='raw')
    certificate=CloudinaryField('certificates/',null=True, blank=True, resource_type='raw')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def total_paid(self):
        return self.payments.filter(
        status='SUCCESS'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    def total_fee(self):
        admission = self.admissions.first()
        if admission and admission.course:
            return admission.course.course_fee
        return 0
    
    def pending_amount(self):
        pending = self.total_fee() - self.total_paid()
        return max(pending, 0)

class Payment(models.Model):
    PAYMENT_MODES = [
        ('UPI', 'UPI'),
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
    ]

    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )
    amount = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    validators=[MinValueValidator(Decimal('1.00'))]
    )
    mode = models.CharField(max_length=10, choices=PAYMENT_MODES)
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SUCCESS')

    def __str__(self):
        return f"{self.student.first_name} - ₹{self.amount}"



class Course(models.Model):
    course = models.CharField(max_length=50, null=False, blank=False)

    duration = models.CharField(max_length=20 ,null=False, blank=False)
    course_fee = models.IntegerField(null=False, blank=False)

    def __str__(self):
        return self.course


class Admission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='admissions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    STATUS = [
        ('enquiry', 'Enquiry'),
        ('confirmed', 'Confirmed'),
        ('enrolled', 'Enrolled'),
        ('dropped', 'Dropped'),
    ]

    status = models.CharField(max_length=20, choices=STATUS, default='enquiry')

    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.course}"


class Enrollment(models.Model):
    admission = models.OneToOneField(Admission, on_delete=models.CASCADE, related_name='enrollment')

    batch = models.CharField(max_length=10, choices=[
        ('', 'Select Batch'),
        ('Batch A','Batch A'),
        ('Batch B','Batch B'),
        ('Batch C','Batch C')
    ])

    start_date = models.DateField(null=False, blank=False)

    payment_status = models.CharField(max_length=20, choices=[
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Partial','Partial')
    ], default='Pending')

    def __str__(self):
        return str(self.admission)