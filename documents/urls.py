from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.my_documents, name='my_documents'),
    path('search', views.SearchResultsView.as_view(), name="search_results"),
]
