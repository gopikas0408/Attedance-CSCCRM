from .models import (
    Attendance,
    AbsentTracker,
    Student
)


def update_absent_tracker():
    print("SERVICE RUNNING")

    

    students = Student.objects.all()

    total_working_days = Attendance.objects.values(
        'date'
    ).distinct().count()

    for student in students:

        attendance_records = (
            Attendance.objects
            .filter(student=student)
            .order_by('-date')
        )

        total_absences = attendance_records.filter(
            status='Absent'
        ).count()

        present_count = attendance_records.filter(
            status='Present'
        ).count()

        consecutive_absences = 0

        for record in attendance_records:

            if record.status == 'Absent':

                consecutive_absences += 1

            else:

                break

        if total_working_days > 0:

            attendance_percentage = (
                present_count / total_working_days
            ) * 100

        else:

            attendance_percentage = 100

        if consecutive_absences >= 5:

            alert_level = "Critical"

        elif consecutive_absences >= 3 or total_absences >= 5:

            alert_level = "Medium"

        else:

            alert_level = "Low"

        notification_status = (
            "SMS Pending"
            if consecutive_absences >= 3 or total_absences >= 5
            else "Dispatched"
        )
        
        student_attendance_count = (
            attendance_records.count()
        )
        if student_attendance_count < total_working_days:
            attendance_status = "Incomplete"
        else:
            attendance_status = "Complete"
            

        #observation notes
        
        if consecutive_absences >= 5:
            observation_note = (
                "Critical Follow-up"
            )
        elif consecutive_absences >= 3:
            observation_note = (
            "Monitoring Required"
            )
        elif total_absences >= 5:
            observation_note = (
            "Frequent Absences"
            )
        else:
            observation_note = (
            "Normal Attendance"
            )

            

        AbsentTracker.objects.update_or_create(
            

            student=student,

            defaults={

                "total_absences":
                total_absences,

                "consecutive_absences":
                consecutive_absences,

                "attendance_percentage":
                round(attendance_percentage, 1),

                "alert_level":
                alert_level,

                "notification_status":
                notification_status,

                "observation_notes":
                observation_note,
                
                "attendance_status":
                attendance_status,

            }

        )
