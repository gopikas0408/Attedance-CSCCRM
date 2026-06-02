from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from .models import Student, Attendance, AbsentTracker
from .services import update_absent_tracker
from django.db.models import Count
from django.utils import timezone

# ABSENT TRACKER

def absent_tracker(request):

    update_absent_tracker()

    absent_students = (
    AbsentTracker.objects
    .select_related('student')
    .filter(total_absences__gt=0)
    .order_by(
        '-consecutive_absences',
        '-total_absences'
    )
)

    context = {
        'absent_students': absent_students
    }

    return render(
        request,
        'student_attendance/absent_tracker.html',
        context
    )

# NOTIFY PARENT

def send_notification(request, tracker_id):

    tracker = get_object_or_404(
        AbsentTracker,
        id=tracker_id
    )

    try:

        if tracker.student.email:

            send_mail(
                subject='Attendance Alert',
                message=f'''
Dear Parent,

Student Name:
{tracker.student.name}

Consecutive Absences:
{tracker.consecutive_absences}

Total Absences:
{tracker.total_absences}

Please contact the institute.

Thank You,
Academic CRM
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[tracker.student.email],
                fail_silently=False
            )

        tracker.notification_sent = True
        tracker.notification_status = 'Dispatched'
        tracker.last_notified_at = timezone.now()
        tracker.save()

        messages.success(
            request,
            f'Notification sent successfully to {tracker.student.name}'
        )

    except Exception as e:

        messages.error(
            request,
            f'Notification sending failed: {str(e)}'
        )

    return redirect('absent_tracker')

# LOW ATTENDANCE ALERTS

def low_attendance_alerts(request):

    update_absent_tracker()

    low_attendance_students = (

        AbsentTracker.objects
        .select_related('student')
        .filter(total_absences__gte=3)
        .order_by('-total_absences')

    )

    context = {

        'low_attendance_students':
        low_attendance_students

    }

    return render(

        request,

        'student_attendance/low_attendance.html',

        context

    )



# SEND SINGLE EMAIL

def send_low_attendance_notification(
    request,
    tracker_id
):

    tracker = get_object_or_404(
        AbsentTracker,
        id=tracker_id
    )

    try:

        if tracker.student.email:

            send_mail(
                subject='Low Attendance Alert',
                message=f'''
Dear Parent,

Student Name:
{tracker.student.name}

Attendance Percentage:
{tracker.attendance_percentage}%

Total Absences:
{tracker.total_absences}

Your ward has low attendance.

Please ensure regular attendance.

Thank You,
Academic CRM
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[tracker.student.email],
                fail_silently=False
            )

        tracker.notification_sent = True
        tracker.notification_status = 'Dispatched'
        tracker.last_notified_at = timezone.now()
        tracker.save()

        messages.success(
            request,
            f'Email sent successfully to {tracker.student.name}'
        )

    except Exception as e:

        messages.error(
            request,
            f'Email sending failed: {str(e)}'
        )

    return JsonResponse({
        "status": "success",

        "message":
        f"Email Sent Successfully to {tracker.student.name}"
    })



# SEND EMAIL TO ALL

def send_email_all(request):

    trackers = (
        AbsentTracker.objects
        .select_related('student')
        .all()
    )

    count = 0

    for tracker in trackers:

        try:

            if tracker.student.email:

                if tracker.total_absences >= 5:

                    subject = "Critical Attendance Alert"

                    message = f"""
Dear Student,

Student ID : {tracker.student.student_id}
Student Name : {tracker.student.name}
Course : {tracker.student.course}
Batch : {tracker.student.batch}

Attendance Percentage : {tracker.attendance_percentage}%
Total Absences : {tracker.total_absences}

Your attendance is currently in the CRITICAL category.

Immediate improvement is required to avoid academic consequences.

Academic CRM Team
"""

                else:

                    subject = "Attendance Warning Notification"

                    message = f"""
Dear Student,

Student ID : {tracker.student.student_id}
Student Name : {tracker.student.name}
Course : {tracker.student.course}
Batch : {tracker.student.batch}

Attendance Percentage : {tracker.attendance_percentage}%
Total Absences : {tracker.total_absences}

Please improve your attendance to avoid entering the Critical category.

Academic CRM Team
"""

                send_mail(

                    subject=subject,

                    message=message,

                    from_email=settings.DEFAULT_FROM_EMAIL,

                    recipient_list=[
                        tracker.student.email
                    ],

                    fail_silently=True

                )

                tracker.notification_sent = True

                tracker.notification_status = 'Dispatched'

                tracker.last_notified_at = timezone.now()

                tracker.save()

                count += 1

        except Exception:
            pass

    messages.success(

        request,

        f'All emails sent successfully. Total Emails Sent: {count}'

    )

    return JsonResponse({

        "status": "success",

        "message":
        f"All Emails Sent Successfully ({count})"

    })

# SEND SINGLE SMS 

def send_sms_notification(
    request,
    tracker_id
):

    tracker = get_object_or_404(
        AbsentTracker,
        id=tracker_id
    )

    if tracker.total_absences >= 5:

        sms_message = (
            f"CRITICAL ALERT\n\n"
            f"Student: {tracker.student.name}\n"
            f"Student ID: {tracker.student.student_id}\n"
            f"Course: {tracker.student.course}\n"
            f"Batch: {tracker.student.batch}\n"
            f"Attendance: {tracker.attendance_percentage}%\n\n"
            f"Immediate improvement is required.\n\n"
            f"Academic CRM"
        )

    else:

        sms_message = (
            f"ATTENDANCE WARNING\n\n"
            f"Student: {tracker.student.name}\n"
            f"Student ID: {tracker.student.student_id}\n"
            f"Course: {tracker.student.course}\n"
            f"Batch: {tracker.student.batch}\n"
            f"Attendance: {tracker.attendance_percentage}%\n\n"
            f"Please improve attendance to avoid entering the critical category.\n\n"
            f"Academic CRM"
        )

    print(sms_message)

    tracker.notification_sent = True

    tracker.notification_status = 'Dispatched'

    tracker.last_notified_at = timezone.now()

    tracker.save()

    messages.success(

        request,

        f'SMS sent successfully to {tracker.student.phone_number}'

    )

    return JsonResponse({

        "status": "success",

        "message":
        f"SMS Sent Successfully to {tracker.student.name}"

    })
# SEND SMS TO ALL 

def send_sms_all(request):

    trackers = AbsentTracker.objects.all()

    count = 0

    for tracker in trackers:

        if tracker.total_absences >= 5:

            sms_message = (
                f"CRITICAL ALERT\n\n"
                f"Student: {tracker.student.name}\n"
                f"Student ID: {tracker.student.student_id}\n"
                f"Course: {tracker.student.course}\n"
                f"Batch: {tracker.student.batch}\n"
                f"Attendance: {tracker.attendance_percentage}%\n\n"
                f"Immediate improvement is required.\n\n"
                f"Academic CRM"
            )

        else:

            sms_message = (
                f"ATTENDANCE WARNING\n\n"
                f"Student: {tracker.student.name}\n"
                f"Student ID: {tracker.student.student_id}\n"
                f"Course: {tracker.student.course}\n"
                f"Batch: {tracker.student.batch}\n"
                f"Attendance: {tracker.attendance_percentage}%\n\n"
                f"Please improve attendance to avoid entering the critical category.\n\n"
                f"Academic CRM"
            )

        print(sms_message)

        tracker.notification_sent = True

        tracker.notification_status = 'Dispatched'

        tracker.last_notified_at = timezone.now()

        tracker.save()

        count += 1

    messages.success(

        request,

        f'All SMS messages sent successfully. Total SMS Sent: {count}'

    )

    return JsonResponse({

        "status": "success",

        "message":
        f"All SMS Messages Sent Successfully ({count})"

    })

# REPORTS

def reports(request):

    total_students = Student.objects.count()

    present_today = Attendance.objects.filter(
        status='Present'
    ).count()

    absent_today = Attendance.objects.filter(
        status='Absent'
    ).count()

    low_attendance = AbsentTracker.objects.filter(
        total_absences__gte=3
    ).count()

    report_students = (
        AbsentTracker.objects
        .select_related('student')
        .all()
        .order_by('-total_absences')
    )

    for tracker in report_students:

        total_days = Attendance.objects.values(
            'date'
        ).distinct().count()

        present_count = Attendance.objects.filter(
            student=tracker.student,
            status='Present'
        ).count()

        absent_count = Attendance.objects.filter(
            student=tracker.student,
            status='Absent'
        ).count()

        late_count = Attendance.objects.filter(
            student=tracker.student,
            status='Late'
        ).count()

        if total_days > 0:

            attendance_rate = (
                present_count / total_days
            ) * 100

        else:

            attendance_rate = 0

        tracker.present_count = present_count
        tracker.absent_count = absent_count
        tracker.late_count = late_count
        tracker.total_days = total_days
        tracker.attendance_rate = round(
            attendance_rate,
            1
        )

    monthly_present = []
    monthly_absent = []
    monthly_late = []

    for month in range(1, 13):

        monthly_present.append(

            Attendance.objects.filter(
                date__month=month,
                status='Present'
            ).count()

        )

        monthly_absent.append(

            Attendance.objects.filter(
                date__month=month,
                status='Absent'
            ).count()

        )

        monthly_late.append(

            Attendance.objects.filter(
                date__month=month,
                status='Late'
            ).count()

        )

    # COURSE WISE DATA

    course_labels = []
    course_counts = []

    courses = Student.objects.values(
        'course'
    )

    unique_courses = {}

    for course in courses:

        course_name = course['course']

        if course_name not in unique_courses:

            unique_courses[course_name] = Student.objects.filter(
                course=course_name
            ).count()

    for key, value in unique_courses.items():

        course_labels.append(key)

        course_counts.append(value)

    from django.utils import timezone

    # BATCH WISE ATTENDANCE DATA

    today = timezone.now().date()

    batch_labels = []
    batch_counts = []
    batch_present_counts = []
    batch_absent_counts = []
    batch_attendance_percentages = []

    for batch_name in ['A', 'B', 'C']:

        present_count = Attendance.objects.filter(
            student__batch=batch_name,
            date=today,
            status='Present'
        ).count()

        absent_count = Attendance.objects.filter(
            student__batch=batch_name,
            date=today,
            status='Absent'
        ).count()

        total_count = present_count + absent_count

        if total_count > 0:

            attendance_percentage = round(
                (present_count / total_count) * 100,
                1
            )

        else:

            attendance_percentage = 0

        batch_labels.append(batch_name)

        batch_counts.append(present_count)

        batch_present_counts.append(
            present_count
        )

        batch_absent_counts.append(
            absent_count
        )

        batch_attendance_percentages.append(
            attendance_percentage
        )
        
        # BATCH PERFORMANCE DATA
    
    today = timezone.now().date()

    batch_performance_labels = []

    batch_performance_counts = []

    students = Student.objects.all()
    
    unique_batches = {}

    for student in students:

        batch_key = (
            f"{student.course}-{student.batch}"
        )

        if batch_key not in unique_batches:

            present_count = Attendance.objects.filter(
                student__course=student.course,
                student__batch=student.batch,
                date=today,
                status='Present'
            ).count()

            unique_batches[
               batch_key
            ] = present_count

    for key, value in unique_batches.items():

        batch_performance_labels.append(key)

        batch_performance_counts.append(value)
    
        
       
    context = {

        'total_students': total_students,

        'present_today': present_today,

        'absent_today': absent_today,

        'low_attendance': low_attendance,

        'report_students': report_students,

        'monthly_present': monthly_present,

        'monthly_absent': monthly_absent,

        'monthly_late': monthly_late,

        'course_labels': course_labels,

        'course_counts': course_counts,

        'batch_labels': batch_labels,

        'batch_present_counts': batch_present_counts,
        'batch_absent_counts': batch_absent_counts,
        'batch_attendance_percentages': batch_attendance_percentages,

        'batch_performance_labels': batch_performance_labels,
        
        'batch_performance_counts': batch_performance_counts,
        
    }
    
    

    return render(
        request,
        'student_attendance/reports.html',
        context
    )

    
    #Monthly Report

def send_monthly_report(request):

    trackers = (
        AbsentTracker.objects
        .select_related('student')
        .all()
    )

    count = 0

    for tracker in trackers:

        if tracker.student.email:

            if tracker.total_absences >= 5:

                report_status = "CRITICAL"

                report_note = (
                    "Immediate attendance improvement is required."
                )

            else:

                report_status = "WARNING"

                report_note = (
                    "Please improve attendance to avoid entering the Critical category."
                )

            send_mail(

                subject=f"Monthly Attendance Report - {report_status}",

                message=f"""
MONTHLY ATTENDANCE REPORT

Student ID : {tracker.student.student_id}
Student Name : {tracker.student.name}
Course : {tracker.student.course}
Batch : {tracker.student.batch}

Attendance Percentage : {tracker.attendance_percentage}%
Total Absences : {tracker.total_absences}
Consecutive Absences : {tracker.consecutive_absences}

Status : {report_status}

Remarks:
{report_note}

This is an automatically generated monthly attendance report.

Academic CRM Team
                """,

                from_email=settings.DEFAULT_FROM_EMAIL,

                recipient_list=[
                    tracker.student.email
                ],

                fail_silently=True

            )

            count += 1

    return JsonResponse({

        "status": "success",

        "message":
        f"Monthly Reports Sent Successfully ({count})"

    })