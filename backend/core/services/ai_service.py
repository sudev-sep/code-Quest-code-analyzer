from django.conf import settings
from core.services.embedding_service import search_similar_chunks
import time

def get_gemini_client():
    from google import genai
    return genai.Client(api_key=settings.GEMINI_API_KEY)

def answer_question(repo_id, question):
    print(f"\nSearching for: {question}")
    relevant_chunks = search_similar_chunks(repo_id, question, top_k=5)

    if not relevant_chunks:
        return {
            'answer': 'I could not find any relevant code for your question.',
            'sources': [],
            'chunks_used': 0
        }

    context = ""
    for i, chunk in enumerate(relevant_chunks):
        context += f"\n--- Chunk {i+1} from {chunk['file_path']} ---\n"
        context += chunk['content']
        context += "\n"

    prompt = f"""You are a helpful code assistant. A developer is asking a question about a codebase.
I have found the most relevant parts of the codebase for their question. Use ONLY this code to answer.

RELEVANT CODE:
{context}

DEVELOPER'S QUESTION:
{question}

Please answer clearly and helpfully. Mention specific file names and line numbers where relevant.
If the code doesn't contain enough information to answer, say so honestly.

IMPORTANT FORMATTING RULES:
- Use clean Markdown formatting.
- Break your response into logical paragraphs.
- Use headers (###) for major sections.
- Use bold text (**keyword**) to emphasize important terms, files, or variables.
- Use inline backticks (`code`) for file paths, variable names, and method names.
- Use bulleted lists (* item) or numbered lists (1. item) for step-by-step breakdowns or file lists. Ensure every list item is on a new line.
"""

    print("Sending to Gemini API...")
    client = get_gemini_client()

    # Retry on transient errors (like Gemini 503 overload)
    max_retries = 3
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            answer = response.text
            sources = list(set([chunk['file_path'] for chunk in relevant_chunks]))
            print("Gemini answered!")
            return {
                'answer': answer,
                'sources': sources,
                'chunks_used': len(relevant_chunks)
            }
        except Exception as e:
            last_error = e
            print(f"Gemini call failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s backoff

    raise last_error
