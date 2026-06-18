import time  # Added to track exactly where the delay is happening
from django.conf import settings
from core.services.embedding_service import search_similar_chunks

def get_gemini_client():
    from google import genai
    return genai.Client(api_key=settings.GEMINI_API_KEY)

def answer_question(repo_id, question):
    """
    This is the full Q&A pipeline in 3 steps with strict duration logging.
    """
    start_time = time.time()
    
    # STEP 1: Find the most relevant code chunks (Reduced top_k from 5 to 3)
    print(f"\n[DEBUG] 1. Starting vector database search for: {question}")
    db_start = time.time()
    relevant_chunks = search_similar_chunks(repo_id, question, top_k=3) 
    print(f"[DEBUG] -> Vector search finished in {time.time() - db_start:.2f} seconds.")

    if not relevant_chunks:
        return {
            'answer': 'I could not find any relevant code for your question.',
            'sources': [],
            'chunks_used': 0 
        }

    # Build the context block
    context = ""
    for i, chunk in enumerate(relevant_chunks):
        context += f"\n--- Chunk {i+1} from {chunk['file_path']} ---\n"
        context += chunk['content']
        context += "\n"

    # Track how massive the context actually is
    print(f"[DEBUG] 2. Context built. Total context length in characters: {len(context)}")

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

    print("[DEBUG] 3. Sending payload to Gemini API...")
    gemini_start = time.time()
    
    client = get_gemini_client()
    response = client.models.generate_content(
        model='gemini-3.5-flash', 
        contents=prompt,
    )

    print(f"[DEBUG] -> Gemini API responded in {time.time() - gemini_start:.2f} seconds.")

    answer = response.text
    sources = list(set([chunk['file_path'] for chunk in relevant_chunks]))
    
    total_duration = time.time() - start_time
    print(f"[DEBUG] Q&A Pipeline complete! Total backend execution time: {total_duration:.2f} seconds.\n")

    return {
        'answer': answer,
        'sources': sources,
        'chunks_used': len(relevant_chunks)
    }
