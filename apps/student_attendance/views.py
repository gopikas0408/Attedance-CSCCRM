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
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import (
    landscape,
    letter
)
from reportlab.lib.styles import getSampleStyleSheet
from django.http import JsonResponse
import json

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

def save_admin_notes(request):

    if request.method == "POST":

        data = json.loads(request.body)

        tracker_id = data.get("tracker_id")
        notes = data.get("notes")

        tracker = AbsentTracker.objects.get(
            id=tracker_id
        )

        tracker.admin_notes = notes

        tracker.save()

        return JsonResponse({
            "status": "success"
        })

    return JsonResponse({
        "status": "error"
    })

# LOW ATTENDANCE ALERTS

def low_attendance_alerts(request):

    #update_absent_tracker()

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

    latest_attendance = (
        Attendance.objects
        .order_by('-date')
        .first()
    )
    
    if latest_attendance:
        report_date = latest_attendance.date
    else:
        report_date = timezone.now().date()
        
    
    today = timezone.now().date()
    
    today_marked_count = Attendance.objects.filter(
        date=today
    ).values(
        'student'
    ).distinct().count()
    
    pending_count = (
        total_students - today_marked_count
    )
    
    if today_marked_count ==0:
        attendance_status = "not_started"
    elif today_marked_count < total_students:
        attendance_status = "in_progress"
        
    else:
        attendance_status = "completed"
        
   

    batch_labels = []
    batch_counts = []
    batch_present_counts = []
    batch_absent_counts = []
    batch_attendance_percentages = []

    for batch_name in ['A', 'B', 'C']:

        present_count = Attendance.objects.filter(
            student__batch=batch_name,
            date=report_date,
            status='Present'
        ).count()

        absent_count = Attendance.objects.filter(
            student__batch=batch_name,
            date=report_date,
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
                date=report_date,
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
        
        'report_date': report_date,
        
        'attendance_status': attendance_status,
        'today_marked_count': today_marked_count,
        'pending_count': pending_count,
        
   
        
    }
    
    

    return render(
        request,
        'student_attendance/reports.html',
        context
    )
    
    #Analytics pdf

from datetime import datetime

def analytics_pdf(request):

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename="Analytics_Report_{datetime.now().strftime("%Y%m%d")}.pdf"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    elements = []

    title = Paragraph(
        "Academic CRM Analytics Report",
        styles['Title']
    )

    elements.append(title)

    elements.append(
        Spacer(1, 12)
    )

    generated_date = Paragraph(
        f"Generated On: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}",
        styles['Normal']
    )

    elements.append(generated_date)

    elements.append(
        Spacer(1, 15)
    )

    total_students = Student.objects.count()

    today = timezone.now().date()

    present_count = Attendance.objects.filter(
        date=today,
        status='Present'
    ).count()

    absent_count = Attendance.objects.filter(
        date=today,
        status='Absent'
    ).count()

    low_attendance = AbsentTracker.objects.filter(
        total_absences__gte=3
    ).count()

    data = [

        ["Metric", "Value"],

        ["Total Students", total_students],

        ["Present Students", present_count],

        ["Absent Students", absent_count],

        ["Low Attendance Alerts", low_attendance]

    ]

    table = Table(
        data,
        colWidths=[250, 150]
    )

    table.setStyle(
        TableStyle([

            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),

            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

            ('GRID', (0, 0), (-1, -1), 1, colors.black),

            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke)

        ])
    )

    elements.append(table)

    elements.append(
        Spacer(1, 20)
    )

    footer = Paragraph(
        "Generated by Academic CRM",
        styles['Italic']
    )

    elements.append(footer)

    doc.build(elements)

    return response

#Analytics Excel

def analytics_excel(request):

    workbook = Workbook()

    sheet = workbook.active

    sheet.title = "Analytics Report"

    today = timezone.now().date()

    total_students = Student.objects.count()

    present_today = Attendance.objects.filter(
        date=today,
        status='Present'
    ).count()

    absent_today = Attendance.objects.filter(
        date=today,
        status='Absent'
    ).count()

    marked_students = (
        present_today +
        absent_today
    )

    pending_students = (
        total_students -
        marked_students
    )

    low_attendance = AbsentTracker.objects.filter(
        total_absences__gte=3
    ).count()

    if marked_students == 0:

        attendance_status = "Not Started"

    elif marked_students < total_students:

        attendance_status = "In Progress"

    else:

        attendance_status = "Completed"

    sheet.append(
        ["Academic CRM Analytics Report"]
    )

    sheet.append([])

    sheet.append(
        ["Generated On", timezone.now().strftime("%d-%m-%Y %I:%M %p")]
    )

    sheet.append([])

    sheet.append(
        ["Metric", "Value"]
    )

    sheet.append(
        ["Total Students", total_students]
    )

    sheet.append(
        ["Marked Students", marked_students]
    )

    sheet.append(
        ["Pending Students", pending_students]
    )

    sheet.append(
        ["Present Today", present_today]
    )

    sheet.append(
        ["Absent Today", absent_today]
    )

    sheet.append(
        ["Low Attendance Alerts", low_attendance]
    )

    sheet.append(
        ["Attendance Status", attendance_status]
    )

    response = HttpResponse(
        content_type=
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response[
        'Content-Disposition'
    ] = (
        'attachment; filename="Analytics_Report.xlsx"'
    )

    workbook.save(response)

    return response
    
    #REport  Pdf

def report_pdf(request):

    response = HttpResponse(
        content_type='application/pdf'
    )

    response[
        'Content-Disposition'
    ] = (
        'attachment; filename="Student_Report.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(letter)
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(

        Paragraph(
            "Academic CRM Student Performance Report",
            styles['Title']
        )

    )

    elements.append(
        Spacer(1, 12)
    )

    data = [

        [
            "Student",
            "Course",
            "Batch",
            "Present",
            "Absent",
            "Late",
            "Attendance %",
            "Status"
        ]

    ]

    trackers = (
        AbsentTracker.objects
        .select_related('student')
        .all()
        .order_by('-total_absences')
    )

    total_days = Attendance.objects.values(
        'date'
    ).distinct().count()

    for tracker in trackers:

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

            attendance_rate = round(
                (present_count / total_days) * 100,
                1
            )

        else:

            attendance_rate = 0

        data.append(

            [

                tracker.student.name,

                tracker.student.course,

                tracker.student.batch,

                present_count,

                absent_count,

                late_count,

                f"{attendance_rate}%",

                tracker.alert_level

            ]

        )

    table = Table(data)

    table.setStyle(

        TableStyle([

            (
                'BACKGROUND',
                (0, 0),
                (-1, 0),
                colors.darkblue
            ),

            (
                'TEXTCOLOR',
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                'GRID',
                (0, 0),
                (-1, -1),
                1,
                colors.black
            ),

            (
                'FONTNAME',
                (0, 0),
                (-1, 0),
                'Helvetica-Bold'
            )

        ])

    )

    elements.append(table)

    doc.build(elements)

    return response

#Report Excel

def report_excel(request):

    workbook = Workbook()

    sheet = workbook.active

    sheet.title = "Student Report"

    headers = [

        "Student Name",
        "Student ID",
        "Course",
        "Batch",
        "Present",
        "Absent",
        "Late",
        "Attendance %",
        "Status"

    ]

    sheet.append(headers)

    trackers = (
        AbsentTracker.objects
        .select_related('student')
        .all()
        .order_by('-total_absences')
    )

    total_days = Attendance.objects.values(
        'date'
    ).distinct().count()

    for tracker in trackers:

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

            attendance_rate = round(
                (present_count / total_days) * 100,
                1
            )

        else:

            attendance_rate = 0

        sheet.append([

            tracker.student.name,

            tracker.student.student_id,

            tracker.student.course,

            tracker.student.batch,

            present_count,

            absent_count,

            late_count,

            f"{attendance_rate}%",

            tracker.alert_level

        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response[
        'Content-Disposition'
    ] = (
        'attachment; filename="Student_Report.xlsx"'
    )

    workbook.save(response)

    return response
    
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