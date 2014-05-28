# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
#from django.template.context import RequestContext


def home(request):
    """
    home page
    """
    return render_to_response('home.html')
