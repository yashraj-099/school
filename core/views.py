from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render


from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import StudentForm, TeacherForm, SubjectForm, FeeRecordForm, EventForm, SchoolForm
from .models import Student, Teacher, Subject, FeeRecord, Event, School, Result 

from django.shortcuts import render

from reportlab.lib.colors import lightgrey


def error_404(request, exception):
    return render(request, "errors/error_404.html", status=404)

def error_500(request):
    return render(request, "errors/error_500.html", status=500)

def error_403(request, exception=None):
    return render(request, "errors/error_403.html", status=403)

def error_400(request, exception=None):
    return render(request, "errors/error_400.html", status=400)


def role_required(*role_names):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if hasattr(request.user, 'role') and request.user.role.name in role_names:
                return view_func(request, *args, **kwargs)
            return redirect('select_dashboard')
        return _wrapped_view
    return decorator
# Rolr switch
def switch_role(request, role_name):
    if not settings.DEMO_MODE:
        return redirect("login")

    User = get_user_model()

    if role_name == "admin":
        user = User.objects.filter(is_superuser=True).first()
        redirect_url = "admin_dashboard"

    elif role_name == "teacher":
        user = User.objects.filter(role__name="Teacher").first()
        redirect_url = "teacher_dashboard"

    elif role_name == "student":
        user = User.objects.filter(role__name="Student").first()
        redirect_url = "student_dashboard"

    else:
        return redirect("login")

    if user:
        login(request, user)
        return redirect(redirect_url)

    return redirect("login")

def demo_entry(request):
    if settings.DEMO_MODE:
        User = get_user_model()
        admin = User.objects.filter(is_superuser=True).first()

        if admin:
            login(request, admin)
            return redirect("admin_dashboard")

    # fallback to normal login
    return redirect("login")

def login_view(request):
    if settings.DEMO_MODE:
        return redirect("/")   # goes to demo_entry → admin dashboard
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('select_dashboard')
        return render(request, 'login.html', {'error':'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def select_dashboard(request):
    user = request.user
    options = []
    if user.is_superuser:
        name = 'Admin'
    else:
        role = getattr(user, 'role', None)
        name = role.name if role else 'User'
    if name == 'Admin':
        options = [{'label':'Admin Dashboard','url':'/admin-dashboard/'},{'label':'Students','url':'/students/'},{'label':'Teachers','url':'/teachers/'},{'label':'Subjects','url':'/subjects/'},{'label':'Fees','url':'/fees/'},{'label':'Events','url':'/events/'}]
    elif name == 'Teacher':
        options = [{'label':'Teacher Dashboard','url':'/teacher-dashboard/'},{'label':'My Subjects','url':'/subjects/'},{'label':'Events','url':'/events/'}]
    else:
        options = [{'label':'Student Dashboard','url':'/student-dashboard/'},{'label':'My Fees','url':'/fees/'},{'label':'Events','url':'/events/'}]
    return render(request,'select_dashboard.html',{'dashboard_options':options})

@login_required
def redirect_dashboard(request):
    selected = request.GET.get('module')
    return redirect(selected)

@login_required
@role_required('Admin')
def admin_dashboard(request):
    students = Student.objects.count()
    schools = School.objects.count()
    teachers = Teacher.objects.count()
    subjects = Subject.objects.count()
    events = Event.objects.count()
    result = Result.objects.count(),
    
    fees_pending = FeeRecord.objects.filter(status__icontains='Unpaid').count()
    return render(request,'dashboards/admin_dashboard.html',{'students':students,'schools':schools,'teachers':teachers,'subjects':subjects,'events':events,'fees_pending':fees_pending})

@login_required
@role_required('Teacher')
def teacher_dashboard(request):
    schools = School.objects.count()
    subjects = Subject.objects.count()
    students = Student.objects.count()
    events = Event.objects.count()
    fees_pending = FeeRecord.objects.filter(status__icontains='Unpaid').count()
    return render(request,'dashboards/teacher_dashboard.html',{'students':students,'schools':schools,'events':events,'fees_pending':fees_pending,'subjects':subjects,})  



@login_required
@role_required('Student')
def student_dashboard(request):
     student = request.user.student
     results = Result.objects.filter(student=student)

     return render(request, "student/dashboard.html", {
        "student": student,
        "results": results,
        "total_results": Result.objects.count(),
        
    })

@login_required
@role_required('Admin')
def students_list(request):
    students = Student.objects.all()
    return render(request,'students/list.html',{'students':students})

@login_required
@role_required('Admin')
def students_create(request):
    if request.method=='POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('students_list')
    else:
        form = StudentForm()
    return render(request,'students/form.html',{'form':form,'form_title':'Add Student'})

@login_required
@role_required('Admin')
def students_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method=='POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('students_list')
    else:
        form = StudentForm(instance=student)
    return render(request,'students/form.html',{'form':form,'form_title':'Edit Student'})

@login_required
@role_required('Admin')
def students_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.delete()
    return redirect('students_list')

@login_required
@role_required('Admin')
def teachers_list(request):
    teachers = Teacher.objects.all()
    return render(request,'teachers/list.html',{'teachers':teachers})

@login_required
@role_required('Admin')
def teachers_create(request):
    if request.method=='POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('teachers_list')
    else:
        form = TeacherForm()
    return render(request,'teachers/form.html',{'form':form,'form_title':'Add Teacher'})

@login_required
@role_required('Admin')
def teachers_update(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method=='POST':
        form = TeacherForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            return redirect('teachers_list')
    else:
        form = TeacherForm(instance=teacher)
    return render(request,'teachers/form.html',{'form':form,'form_title':'Edit Teacher'})

@login_required
@role_required('Admin')
def teachers_delete(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    teacher.delete()
    return redirect('teachers_list')

@login_required
@role_required('Admin', 'Teacher')
def subjects_list(request):
    subjects = Subject.objects.all()
    return render(request,'subjects/list.html',{'subjects':subjects})

@login_required
@role_required('Admin', 'Teacher')
def subjects_create(request):
    if request.method=='POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subjects_list')
    else:
        form = SubjectForm()
    return render(request,'subjects/form.html',{'form':form,'form_title':'Add Subject'})

@login_required
@role_required('Admin', 'Teacher')
def subjects_update(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method=='POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('subjects_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request,'subjects/form.html',{'form':form,'form_title':'Edit Subject'})

@login_required
@role_required('Admin', 'Teacher')
def subjects_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    subject.delete()
    return redirect('subjects_list')

@login_required
@role_required('Admin')
def fees_list(request):
    fees = FeeRecord.objects.all()
    return render(request,'fees/list.html',{'fees':fees})

@login_required
@role_required('Admin')
def fees_create(request):
    if request.method=='POST':
        form = FeeRecordForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('fees_list')
    else:
        form = FeeRecordForm()
    return render(request,'fees/form.html',{'form':form,'form_title':'Add Fee Record'})

@login_required
@role_required('Admin')
def fees_update(request, pk):
    fee = get_object_or_404(FeeRecord, pk=pk)
    if request.method=='POST':
        form = FeeRecordForm(request.POST, instance=fee)
        if form.is_valid():
            form.save()
            return redirect('fees_list')
    else:
        form = FeeRecordForm(instance=fee)
    return render(request,'fees/form.html',{'form':form,'form_title':'Edit Fee Record'})

@login_required
@role_required('Admin')
def fees_delete(request, pk):
    fee = get_object_or_404(FeeRecord, pk=pk)
    fee.delete()
    return redirect('fees_list')

@login_required
@role_required('Admin', 'Teacher', 'Student')
def events_list(request):
    events = Event.objects.all()
    return render(request,'events/list.html',{'events':events})

@login_required
@role_required('Admin', 'Teacher')
def events_create(request):
    if request.method=='POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('events_list')
    else:
        form = EventForm()
    return render(request,'events/form.html',{'form':form,'form_title':'Add Event'})

@login_required
@role_required('Admin', 'Teacher')
def events_update(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method=='POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('events_list')
    else:
        form = EventForm(instance=event)
    return render(request,'events/form.html',{'form':form,'form_title':'Edit Event'})

@login_required
@role_required('Admin', 'Teacher')
def events_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    event.delete()
    return redirect('events_list')

@login_required
@role_required('Admin')
def schools_list(request):
    schools = School.objects.all()
    return render(request,'schools/list.html',{'schools':schools})

@login_required
@role_required('Admin')
def schools_create(request):
    if request.method=='POST':
        form = SchoolForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('schools_list')
    else:
        form = SchoolForm()
    return render(request,'schools/form.html',{'form':form,'form_title':'Add School'})

@login_required
@role_required('Admin')
def schools_update(request, pk):
    school = get_object_or_404(School, pk=pk)
    if request.method=='POST':
        form = SchoolForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            return redirect('schools_list')
    else:
        form = SchoolForm(instance=school)
    return render(request,'schools/form.html',{'form':form,'form_title':'Edit School'})

@login_required
@role_required('Admin')
def schools_delete(request, pk):
    school = get_object_or_404(School, pk=pk)
    school.delete()
    return redirect('schools_list')

def dashboard_view(request):
    if not request.cas_user:
        return JsonResponse({'detail': 'Not authenticated'}, status=401)
    return JsonResponse({
        'message': f"Welcome {request.cas_user['username']}!",
        'permissions': request.cas_permissions
    })


# View For Fees PDF/GENERATION
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.http import HttpResponse
from django.conf import settings
import os
import qrcode
from .models import Student, FeeRecord

def generate_fee_invoice(request, student_id):
    student = Student.objects.get(id=student_id)
    fee = FeeRecord.objects.filter(student=student).last()
    school = student.school

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice_{student.name}.pdf"'

    # PDF setup
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 18)
    p.drawString(140, height - 80, school.name)

    # Logo
    logo_path = os.path.join(settings.BASE_DIR, "static/images/school_logo.png")
    if os.path.exists(logo_path):
        p.drawImage(logo_path, 40, height - 120, width=80, height=80)

    # School name
    p.setFont("Helvetica", 11)
    p.drawString(140, height - 100, school.address)

    # Invoice info
    p.setFont("Helvetica", 11)
    p.drawRightString(width - 40, height - 80, f"Invoice No: {fee.invoice_no}")
    p.drawRightString(width - 40, height - 100, f"Date: {fee.date}")

    # Student info
    p.drawString(40, height - 160, f"Student Name: {student.name}")
    p.drawString(40, height - 180, f"Grade: {student.grade}")
    p.drawString(40, height - 200, f"Email: {student.email}")

    # Fee table
    table_data = [
        ["Description", "Amount (₹)"],
        ["School Fee", f"{fee.amount}"],
        ["Status", fee.status],
    ]

    table = Table(table_data, colWidths=[300, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("FONT", (0,0), (-1,0), "Helvetica"),
        ("FONT", (0,1), (-1,-1), "Helvetica"),
    ]))

    table.wrapOn(p, width, height)
    table.drawOn(p, 40, height - 320)

    # QR Code
    qr_data = f"Invoice:{fee.invoice_no}|Student:{student.name}|Amount:{fee.amount}"
    qr = qrcode.make(qr_data)
    qr_path = os.path.join(settings.BASE_DIR, "static/images/qr_temp.png")
    qr.save(qr_path)

    p.drawImage(qr_path, width - 160, height - 360, width=120, height=120)

    # Signature
    sign_path = os.path.join(settings.BASE_DIR, "static/images/principal_sign.png")
    if os.path.exists(sign_path):
        p.drawImage(sign_path, 40, 120, width=120, height=50)
        p.drawString(40, 100, "Principal Signature")

    # Footer
    p.setFont("Helvetica", 9)
    p.drawCentredString(width / 2, 60, "This is a computer-generated invoice.")

    p.showPage()
    p.save()
    
    # Watermark
    p.saveState()
    p.setFont("Helvetica-Bold", 80)
    p.setFillColor(lightgrey)

    status_text = "PAID" if fee.status.lower() == "paid" else "UNPAID"

    p.translate(300, 400)
    p.rotate(45)
    p.drawCentredString(0, 0, status_text)
  
    p.restoreState()

    return response

# Result PDF Generation View
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .models import Result, Student

def generate_result_pdf(request, student_id):
    results = Result.objects.select_related("subject", "student").filter(student_id=student_id)

    if not results.exists():
        return HttpResponse("No results found for this student")

    student = results.first().student
    school = student.school

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Result_{student.name}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # ===== HEADER =====
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, height - 50, school.name)

    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, height - 80, "STUDENT REPORT CARD")

    p.line(40, height - 95, width - 40, height - 95)

    # ===== STUDENT INFO =====
    p.setFont("Helvetica", 11)
    p.drawString(40, height - 130, f"Student Name : {student.name}")
    p.drawString(40, height - 150, f"Grade        : {student.grade}")
    p.drawString(40, height - 170, f"Exam Date    : {results.first().exam_date}")

    # ===== TABLE DATA =====
    table_data = [["Subject", "Marks Obtained", "Total Marks"]]

    total_obtained = 0
    total_max = 0

    for r in results:
        table_data.append([
            r.subject.name,
            float(r.marks_obtained),
            float(r.total_marks)
        ])
        total_obtained += r.marks_obtained
        total_max += r.total_marks

    percentage = round((total_obtained / total_max) * 100, 2) if total_max else 0
    status = "PASS" if percentage >= 40 else "FAIL"

    table_data.append(["", "", ""])
    table_data.append(["TOTAL", float(total_obtained), float(total_max)])

    # ===== TABLE STYLE =====
    table = Table(table_data, colWidths=[240, 140, 140])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ("FONT", (0,-1), (-1,-1), "Helvetica-Bold"),
    ]))

    table.wrapOn(p, width, height)
    table.drawOn(p, 40, height - 420)

    # ===== SUMMARY =====
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, height - 450, f"Percentage : {percentage}%")

    p.setFillColor(colors.green if status == "PASS" else colors.red)
    p.drawString(40, height - 470, f"Result     : {status}")
    p.setFillColor(colors.black)

    # ===== SIGNATURES =====
    p.line(40, 120, 200, 120)
    p.line(width - 240, 120, width - 40, 120)

    p.setFont("Helvetica", 10)
    p.drawString(70, 100, "Class Teacher")
    p.drawString(width - 200, 100, "Principal")

    # ===== FOOTER =====
    p.setFont("Helvetica-Oblique", 9)
    p.drawCentredString(width / 2, 60, "This is a system-generated report card.")

    p.showPage()
    p.save()

    return response


from .forms import ResultForm
from django.contrib import messages

def add_result(request):
    form = ResultForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Result added successfully")
            return redirect("result_list")

    return render(request, "results/add_result.html", {"form": form})



from .models import Result
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def result_list(request):
    results = Result.objects.select_related("student", "subject").order_by("student__name")

    return render(request, "results/result_list.html", {
        "results": results
    })


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Result
from .forms import ResultForm

def edit_result(request, pk):
    result = get_object_or_404(Result, pk=pk)
    form = ResultForm(request.POST or None, instance=result)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Result updated successfully")
            return redirect("result_list")

    return render(request, "results/edit_result.html", {
        "form": form,
        "result": result
    })


def delete_result(request, pk):
    result = get_object_or_404(Result, pk=pk)
    result.delete()
    messages.success(request, "Result deleted successfully")
    return redirect("result_list")