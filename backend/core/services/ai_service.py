from django.conf import settings
from core.services.embedding_service import search_similar_chunks


def get_gemini_client():
    from google import genai
    return genai.Client(api_key=settings.GEMINI_API_KEY)


# I renamed this to ask_gemini to match your views.py!
def answer_question(repo_id, question):
    """
    This is the full Q&A pipeline in 3 steps:
    Step 1 - Find relevant code chunks using semantic search
    Step 2 - Build a prompt with those chunks as context
    Step 3 - Ask Gemini to answer based only on that context
    """

    # STEP 1: Find the most relevant code chunks
    print(f"\nSearching for: {question}")
    relevant_chunks = search_similar_chunks(repo_id, question, top_k=5)

    if not relevant_chunks:
        return {
            'answer': 'I could not find any relevant code for your question.',
            'sources': []
        }

    # STEP 2: Build the context string
    context = ""
    for i, chunk in enumerate(relevant_chunks):
        context += f"\n--- Chunk {i+1} from {chunk['file_path']} ---\n"
        context += chunk['content']
        context += "\n"

    # STEP 3: Build the prompt and ask Gemini
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

    # Using the new client.models.generate_content syntax
    # gemini-2.5-flash is the recommended default for most text and coding tasks
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
    )

    answer = response.text

    # Collect the source files so we can show them to the user
    sources = list(set([chunk['file_path'] for chunk in relevant_chunks]))

    print("Gemini answered!")

    return {
        'answer': answer,
        'sources': sources,
        'chunks_used': len(relevant_chunks)
    }