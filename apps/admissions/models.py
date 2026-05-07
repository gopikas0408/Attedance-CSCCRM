from django.db import models
from django.core.validators import RegexValidator


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
    First_name = models.CharField(max_length=20, blank=False, validators=[name_validator])
    Last_name = models.CharField(max_length=20, blank=False, validators=[name_validator])
    dob = models.DateField()
    phone_no = models.CharField(max_length=10, blank=False, validators=[phone_validator])

    gender_choice = [
        ('M','Male'),
        ('F','Female'),
        ('O','Others')
    ]
    gender = models.CharField(max_length=10, choices=gender_choice)

    email = models.EmailField(validators=[email_validator])
    address = models.TextField()

    guardian_name = models.CharField(max_length=100, blank=False, validators=[name_validator])
    guardian_phone_no = models.CharField(max_length=10, blank=False, validators=[phone_validator])
    
    photo=models.ImageField(upload_to='student_photos/', null=False, blank=False)
    id_proof=models.FileField(upload_to='id_proofs/', null=False, blank=False)
    certificate=models.FileField(upload_to='certificates/', null=False, blank=False)

    def __str__(self):
        return f"{self.First_name} {self.Last_name}"


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