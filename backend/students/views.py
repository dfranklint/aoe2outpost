from django.shortcuts import render
from django.http import JsonResponse

def index(request):
    students = []
    return JsonResponse(students, safe=False)