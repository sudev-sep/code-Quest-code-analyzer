from urllib import request

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Repository,FileChunk
from .services.clone_service import clone_repository
from .services.ai_service import answer_question
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
        from .services.ai_service import answer_question

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

        try:
            result = answer_question(repo_id, question)
            return Response({
                'question': question,
                'answer': result['answer'],
                'sources': result['sources'],
                'chunks_used': result['chunks_used']
            })
        except Exception as e:
            return Response({
                'error': 'AI service is temporarily unavailable. Please try again in a moment.',
                'detail': str(e)
            }, status=503)
        

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