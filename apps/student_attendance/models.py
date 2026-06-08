
from django.db import models

# STUDENT MODEL


class Student(models.Model):
    
    COURSE_CHOICES = [
    ("MERN", "MERN"),
    ("PYTHON", "PYTHON"),
    ("JAVA", "JAVA"),
    ("MEAN", "MEAN"),
    ("UI/UX", "UI/UX"),
    ]

    BATCH_CHOICES = [
    ("A", "A"),
    ("B", "B"),
    ("C", "C"),
    ]

    student_id = models.CharField(
        max_length=20,
        unique=True
    )

    name = models.CharField(
        max_length=100
    )

    phone_number = models.CharField(
        max_length=15
    )
    course = models.CharField(
    max_length=50,
    choices=COURSE_CHOICES,
    default="MERN"
    )

    batch = models.CharField(
        max_length=20,
        choices=BATCH_CHOICES,
        default="A"
    )

    email = models.EmailField(
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.name



# ATTENDANCE MODEL


class Attendance(models.Model):

    STATUS_CHOICES = [

        ('Present', 'Present'),

        ('Absent', 'Absent'),
        
        ('Late', 'Late'),

    ]

    student = models.ForeignKey(

        Student,

        on_delete=models.CASCADE

    )

    date = models.DateField()

    status = models.CharField(

        max_length=10,

        choices=STATUS_CHOICES

    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        unique_together = (

            'student',
            'date'

        )

    def __str__(self):

        return (
            f"{self.student.name}"
            f" - {self.date}"
        )



# ABSENT TRACKER MODEL


class AbsentTracker(models.Model):

    ALERT_CHOICES = [

        ('Low', 'Low'),

        ('Medium', 'Medium'),

        ('Critical', 'Critical'),

    ]

    NOTIFICATION_CHOICES = [

        ('SMS Pending', 'SMS Pending'),

        ('Dispatched', 'Dispatched'),

    ]

    student = models.ForeignKey(

        Student,

        on_delete=models.CASCADE

    )

    total_absences = models.IntegerField(
        default=0
    )

    consecutive_absences = models.IntegerField(
        default=0
    )

    attendance_percentage = models.FloatField(
        default=100
    )

    alert_level = models.CharField(

        max_length=10,

        choices=ALERT_CHOICES,

        default='Low'

    )

    observation_notes = models.TextField(

        blank=True,

        null=True

    )

    notification_status = models.CharField(

        max_length=20,

        choices=NOTIFICATION_CHOICES,

        default='SMS Pending'

    )
    
    attendance_status = models.CharField(
        max_length=20,
        default='Complete'
        
    )
    
    admin_notes = models.TextField(
        blank=True,
        null=True
    )

    notification_sent = models.BooleanField(
        default=False
    )

    last_notified_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return (
            f"{self.student.name}"
            f" - {self.alert_level}"
        )

