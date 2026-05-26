import os
import shutil
import git
from core.models import Repository

REPOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'repos')

def clone_repository(repo_id):
    repo = Repository.objects.get(id=repo_id)

    try:
        repo.status = 'cloning'
        repo.save()

        os.makedirs(REPOS_DIR, exist_ok=True)

        repo_folder = os.path.join(REPOS_DIR, str(repo_id))

        if os.path.exists(repo_folder):
            shutil.rmtree(repo_folder)

        print(f"Cloning {repo.github_url} ...")
        git.Repo.clone_from(repo.github_url, repo_folder)
        print("Cloning done!")

        repo.local_path = repo_folder
        repo.status = 'indexing'
        repo.save()


         # Step 1: Parse all files into chunks
        from core.services.parser_services import parse_repository
        parse_repository(repo_id)

        # Step 2: Convert chunks into embeddings and store in ChromaDB
        from core.services.embedding_service import embed_repository
        embed_repository(repo_id)

        # All done!
        repo.status = 'ready'
        repo.save()

        # All done!
        repo.status = 'ready'
        repo.save()


        repo.status = 'ready'
        repo.save()

        return True


    except Exception as e:
        repo.status = 'failed'
        repo.error_message = str(e)
        repo.save()
        print(f"Failed: {e}")
        return False