from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from .forms import StudentForm, AdmissionForm, EnrollmentForm 
from .models import *
from django.contrib import messages
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table
from .filters import StudentFilter
from datetime import date
from django.db import transaction
from xhtml2pdf import pisa
from django.template.loader import get_template
from . services import get_fee_summary

# Create your views here.

def home(request):
    return render(request, 'admissions/home.html')


def student(request):
    student_form = StudentForm()
    admission_form = AdmissionForm()
    enrollment_form = EnrollmentForm()

    courses = Course.objects.all()

    if request.method == "POST":
        student_form = StudentForm(request.POST, request.FILES)
        admission_form = AdmissionForm(request.POST)
        enrollment_form = EnrollmentForm(request.POST, request.FILES)

        if (student_form.is_valid() and 
            admission_form.is_valid() and 
            enrollment_form.is_valid()):

            with transaction.atomic():
                student = student_form.save()

                admission = Admission.objects.create(
                    student=student,
                    course=admission_form.cleaned_data['course'],
                    status=admission_form.cleaned_data['status']
                )

                enrollment = enrollment_form.save(commit=False)
                enrollment.admission = admission
                enrollment.save()

            messages.success(request, "Student enrolled successfully!")
            return redirect('student_list')
        
        else:
            messages.error(request, "Form has errors. Please check!")

    return render(request, 'admissions/register.html', {
        'student_form': student_form,
        'admission_form': admission_form,
        'enrollment_form': enrollment_form,
        'courses': courses,
    })


def fee_dashboard(request):

    students = Student.objects.all()

    payments = Payment.objects.order_by('-date')

    # SAVE PAYMENT
    if request.method == 'POST':

        student_id = request.POST.get('student')

        amount = request.POST.get('amount')

        mode = request.POST.get('mode')

        reference = request.POST.get('reference')

        remarks = request.POST.get('remarks')

        Payment.objects.create(
            student_id=student_id,
            amount=amount,
            mode=mode,
            reference_id=reference,
            remarks=remarks
        )

        messages.success(
            request,
            "Payment Added Successfully"
        )

        return redirect('fee_dashboard')

    # DASHBOARD SUMMARY
    summary = get_fee_summary()

    # STUDENT FEE STATUS
    student_fee_status = []

    for student in students:

        total_fee = student.total_fee()

        paid = student.total_paid()

        pending = student.pending_amount()

        # STATUS
        if pending <= 0:
            status = 'Paid'

        elif paid == 0:
            status = 'Pending'

        else:
            status = 'Partial'

        student_fee_status.append({
            'student': student,
            'total_fee': total_fee,
            'paid': paid,
            'pending': pending,
            'status': status
        })

    context = {
        'students': students,
        'payments': payments,
        'summary': summary,
        'student_fee_status': student_fee_status
    }

    return render(
        request,
        'admissions/fee_dashboard.html',
        context
    )


#Student Profile Integration===========
def student_detail(request, pk):
    student = Student.objects.get(id=pk)
    payments = student.payments.all()

    context = {
        'student': student,
        'payments': payments,
        'total_paid': student.total_paid(),
        'pending': student.pending_amount()
    }

    return render(request, 'students/detail.html', context)

# pdf view ========
def generate_receipt(request, pk):
    payment = Payment.objects.get(id=pk)

    template = get_template('admissions/fee_receipt.html')
    html = template.render({'payment': payment})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="receipt_{pk}.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response

def student_list(request):

    students = Student.objects.prefetch_related(
        'payments',
        'admissions__enrollment',
        'admissions__course',
    ).all()

    #  FILTER
    student_filter = StudentFilter(request.GET, queryset=students)
    filtered_students = student_filter.qs.distinct().order_by('-id')

    #  PAGINATION
    paginator = Paginator(filtered_students, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    format = request.GET.get('format')

    # ================= EXCEL =================
    if format == 'excel':
        wb = Workbook()
        ws = wb.active
        ws.append(["Student", "Course", "Batch", "Phone", "Payment Status", "Joined"])

        for s in filtered_students:
            for admission in s.admissions.all():
                enrollment = getattr(admission, 'enrollment', None)

                ws.append([
                    f"{s.First_name} {s.Last_name}",
                    str(admission.course),
                    enrollment.batch if enrollment else "-",
                    s.phone_no,
                    enrollment.payment_status if enrollment else "-",
                    str(enrollment.start_date) if enrollment else "-"
                ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=students.xlsx'
        wb.save(response)
        return response

    # ================= PDF =================
    if format == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="students.pdf"'

        data = [["Student", "Course", "Batch", "Phone", "Payment Status", "Joined"]]

        for s in filtered_students:
            for admission in s.admissions.all():
                enrollment = getattr(admission, 'enrollment', None)

                data.append([
                    f"{s.First_name} {s.Last_name}",
                    str(admission.course),
                    enrollment.batch if enrollment else "-",
                    s.phone_no,
                    enrollment.payment_status if enrollment else "-",
                    str(enrollment.start_date) if enrollment else "-"
                ])

        doc = SimpleDocTemplate(response)
        table = Table(data)
        doc.build([table])

        return response

    return render(request, 'admissions/student_list.html', {
        'page_obj': page_obj,
        'filter': student_filter,
        'courses': Course.objects.all(),
        'total_students': filtered_students.count()
    })

from django.shortcuts import render, redirect, get_object_or_404

def edit_student(request, id):

    student = get_object_or_404(Student, id=id)

    admission = Admission.objects.get(student=student)

    enrollment = Enrollment.objects.get(admission=admission)

    courses = Course.objects.all()

    if request.method == 'POST':

        # ================= PERSONAL INFO =================

        student.First_name = request.POST.get('First_name')
        student.Last_name = request.POST.get('Last_name')
        student.email = request.POST.get('email')
        student.phone_no = request.POST.get('phone_no')
        student.dob = request.POST.get('dob')
        student.gender = request.POST.get('gender')
        student.guardian_name = request.POST.get('guardian_name')
        student.guardian_phone_no = request.POST.get('guardian_phone_no')
        student.address = request.POST.get('address')

        # ================= FILES =================

        if request.FILES.get('photo'):
            student.photo = request.FILES.get('photo')

        if request.FILES.get('id_proof'):
            student.id_proof = request.FILES.get('id_proof')

        if request.FILES.get('certificate'):
            student.certificate = request.FILES.get('certificate')

        student.save()

        # ================= ADMISSION =================

        course_id = request.POST.get('course')

        if course_id:
            admission.course_id = course_id

        admission.status = request.POST.get('status')

        admission.save()

        # ================= ENROLLMENT =================

        batch_id = request.POST.get('batch')

        if batch_id:
            enrollment.batch_id = batch_id

        enrollment.start_date = request.POST.get('start_date')
        enrollment.payment_status = request.POST.get('payment_status')

        enrollment.save()

        return redirect('student_list')

    context = {
        'student': student,
        'admission': admission,
        'enrollment': enrollment,
        'courses': courses
    }

    return render(request, "admissions/edit_student.html", context)

def delete_student(request, id):
    student=Student.objects.get(id=id)
    student.delete()
    messages.success(request, "✅Student deleted successfully")
    return redirect('student_list')

def search_students(request):

    students = Student.objects.prefetch_related(
        'admissions__course',
        'admissions__enrollment'
    )

    student_filter = StudentFilter(request.GET, queryset=students)
    filtered_students = student_filter.qs.distinct()

    paginator = Paginator(filtered_students, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "admissions/search_students.html", {
        'filter': student_filter,
        'page_obj': page_obj,
        'courses': Course.objects.all()
    })

    
def view_student(request, id):

    student = Student.objects.prefetch_related(
        'payments',
        'admissions__course',
        'admissions__enrollment'
    ).get(id=id)

    admission = student.admissions.first()

    enrollment = admission.enrollment if admission else None

    payments = student.payments.all().order_by('-date')

    return render(request, "admissions/view_student.html", {

        'student': student,
        'admission': admission,
        'enrollment': enrollment,
        'payments': payments,

        'total_paid': student.total_paid(),
        'pending': student.pending_amount(),

    })