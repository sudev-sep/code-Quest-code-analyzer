from urllib import request

from celery.result import AsyncResult
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Repository, FileChunk
from .services.clone_service import clone_repository
from .tasks import answer_question_task
from core.services.embedding_service import delete_collection, search_similar_chunks



class RepositoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        github_url = request.data.get('github_url')

        if not github_url:
            return Response({'error': 'github_url is required'}, status=400)
        repo_name = github_url.rstrip('/').split('/')[-1]

        repo = Repository.objects.create(
            github_url=github_url,
            name=repo_name,
            user=request.user
        )

        clone_repository(repo.id)

        repo.refresh_from_db()

        return Response({
            'id': repo.id,
            'name': repo.name,
            'status': repo.status,
            'message': f'Repository "{repo.name}" has been cloned successfully!'
        })

    def get(self, request):
        try:
            repos = Repository.objects.filter(user=request.user).values(
                'id', 'name', 'status', 'github_url', 'created_at'
            )
            return Response(list(repos))
        except Exception as e:
            return Response({'error': str(e)}, status=500)
       

class ChunkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, repo_id):
        chunks = FileChunk.objects.filter(
            repository_id=repo_id
        ).values('id', 'file_path', 'chunk_index', 'content')[:20] 

        total = FileChunk.objects.filter(repository_id=repo_id).count()

        return Response({
            'total_chunks': total,
            'showing': len(chunks),
            'chunks': list(chunks)
        })
    

class SearchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, repo_id):
        from core.services.embedding_service import search_similar_chunks

        query = request.data.get('query')

        if not query:
            return Response({'error': 'query is required'}, status=400)

        results = search_similar_chunks(repo_id, query, top_k=5)

        return Response({
            'query': query,
            'results': results
        })
    
class QuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, repo_id):
        question = request.data.get('question')

        if not question:
            return Response({'error': 'question is required'}, status=400)

        try:
            repo = Repository.objects.get(id=repo_id)
        except Repository.DoesNotExist:
            return Response({'error': 'Repository not found'}, status=404)

        if repo.status != 'ready':
            return Response({
                'error': f'Repository is not ready yet. Current status: {repo.status}'
            }, status=400)

        # Dispatch to Celery — returns immediately, freeing the gunicorn worker
        task = answer_question_task.delay(repo_id, question)
        return Response({
            'task_id': task.id,
            'status': 'processing',
            'message': 'Your question is being processed. Poll the GET endpoint with this task_id for results.'
        }, status=202)

    def get(self, request, repo_id):
        # Poll for task results by task_id query param
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({'error': 'task_id is required'}, status=400)

        task_result = AsyncResult(task_id)
        if task_result.state == 'PENDING':
            return Response({'status': 'processing'}, status=202)
        elif task_result.state == 'SUCCESS':
            return Response({
                'status': 'completed',
                'result': task_result.result
            })
        elif task_result.state == 'FAILURE':
            return Response({
                'status': 'failed',
                'error': str(task_result.info)
            }, status=500)
        else:
            # RETRY, STARTED, etc.
            return Response({'status': task_result.state.lower()}, status=202)
        

class RepositoryDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, repo_id):
        try:
            repo = Repository.objects.get(id=repo_id)
            delete_collection(repo_id)
            repo.delete()
            return Response({'message': f'Repository "{repo.name}" has been deleted successfully!'})
        except Repository.DoesNotExist:
            return Response({'error': 'Repository not found'}, status=404)
        


class RegisterView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        from django.contrib.auth.models import User
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        if not username or not password or not email:
            return Response({'error': 'Username, email, and password are required'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=400)

        user = User.objects.create_user(username=username, password=password, email=email)
        return Response({'message': f'User "{user.username}" has been registered successfully!'})
    


    class TokenObtainPairView(APIView):
        permission_classes = [AllowAny]

        def post(self, request):
            from rest_framework_simplejwt.tokens import RefreshToken
            from django.contrib.auth import authenticate

            username = request.data.get('username')
            password = request.data.get('password')

            user = authenticate(username=username, password=password)

            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            else:
                return Response({'error': 'Invalid credentials'}, status=401)