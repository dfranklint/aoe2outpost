from django.urls import path
from .views import index, box_plots, line_charts, scatter_plots

urlpatterns = [
    path('', index, name='index'),
    path('box_plots/', box_plots, name='box_plots'),
    path('line_charts/', line_charts, name='line_charts'),
    path('scatter_plots/', scatter_plots, name='scatter_plots')


]
