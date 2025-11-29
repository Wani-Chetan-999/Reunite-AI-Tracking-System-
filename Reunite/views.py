from django.shortcuts import redirect, render

def index(request):
    return render(request, 'index.html')

def deptLogin(request):
    return redirect('police:login')