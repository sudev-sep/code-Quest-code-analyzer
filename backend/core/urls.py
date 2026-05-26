from django.urls import path
from .views import RepositoryView, ChunkView, SearchView, QuestionView
urlpatterns = [
    path('repositories/', RepositoryView.as_view()),
    path('repositories/<int:repo_id>/chunks/', ChunkView.as_view()),
    path('repositories/<int:repo_id>/search/', SearchView.as_view()),
    path('repositories/<int:repo_id>/ask/', QuestionView.as_view()),

]