from celery import shared_task
from .services.ai_service import answer_question as sync_answer_question


@shared_task(bind=True, max_retries=3)
def answer_question_task(self, repo_id, question):
    try:
        return sync_answer_question(repo_id, question)
    except Exception as exc:
        # Retry with exponential backoff: 1s, 2s, 4s
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
