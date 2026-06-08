from django.urls import path

from . import views


urlpatterns = [

    path(

        'absent-tracker/',

        views.absent_tracker,

        name='absent_tracker'

    ),

    path(

        'low-attendance/',

        views.low_attendance_alerts,

        name='low_attendance'

    ),

    path(

        'reports/',

        views.reports,

        name='reports'

    ),
    
    path(
        'send-notification/<int:alert_id>/',
        views.send_notification,
        name='send_notification'
    ),
    
    path(
        'send-low-attendance-notification/<int:tracker_id>/',
        views.send_low_attendance_notification,
        name='send_low_attendance_notification'
    ),
    
    path(
    'send-sms/<int:tracker_id>/',
    views.send_sms_notification,
    name='send_sms_notification'
    ),

    path(
    'send-email-all/',
    views.send_email_all,
    name='send_email_all'
    ),

    path(
    'send-sms-all/',
    views.send_sms_all,
    name='send_sms_all'
    ),

    path(
    'send-monthly-report/',
    views.send_monthly_report,
    name='send_monthly_report'
    ),

    path(
    'analytics-pdf/',
    views.analytics_pdf,
    name='analytics_pdf'
    ),

    path(
    'analytics-excel/',
    views.analytics_excel,
    name='analytics_excel'
    ),

    path(
    'report-pdf/',
    views.report_pdf,
    name='report_pdf'
    ),

    path(
    'report-excel/',
    views.report_excel,
    name='report_excel'
    ),
    
    path(
    'save-admin-notes/',
    views.save_admin_notes,
    name='save_admin_notes'
    ),

]

