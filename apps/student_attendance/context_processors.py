from .models import AbsentTracker

def sidebar_counts(request):

    low_attendance_count = (
        AbsentTracker.objects
        .filter(total_absences__gte=3)
        .count()
    )

    return {

        'low_attendance_count':
        low_attendance_count

    }