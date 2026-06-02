from django.contrib import admin

# Register your models here.
from .models import Student, Attendance, AbsentTracker

admin.site.register(Student)
admin.site.register(Attendance)
admin.site.register(AbsentTracker)