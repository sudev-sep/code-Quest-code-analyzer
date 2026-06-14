import os
import google.generativeai as genai
from core.models import FileChunk, Repository

CHROMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'chromadb_store'
)

_chroma_client = None

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


def get_gemini_embedding(texts, task_type="retrieval_document"):
    """
    Convert a list of texts into embeddings using Gemini API.
    No model loaded into memory — it's just an API call!
    """
    embeddings = []
    for text in texts:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type=task_type
        )
        embeddings.append(result['embedding'])
    return embeddings


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _chroma_client


def get_collection(repo_id):
    return get_chroma_client().get_or_create_collection(
        name=f"repo_{repo_id}",
        metadata={"hnsw:space": "cosine"}
    )


def embed_repository(repo_id):
    repo = Repository.objects.get(id=repo_id)
    print(f"\nStarting embedding for: {repo.name}")

    chunks = FileChunk.objects.filter(repository=repo)
    total = chunks.count()

    if total == 0:
        print("No chunks found! Run parsing first.")
        return

    print(f"Found {total} chunks to embed...")

    # Delete old embeddings if re-running
    try:
        get_chroma_client().delete_collection(f"repo_{repo_id}")
    except Exception:
        pass

    collection = get_collection(repo_id)

    # Smaller batch size since each text is an API call
    BATCH_SIZE = 20
    chunk_list = list(chunks)

    for batch_start in range(0, total, BATCH_SIZE):
        batch = chunk_list[batch_start:batch_start + BATCH_SIZE]

        print(f"  Embedding chunks {batch_start + 1} to {min(batch_start + BATCH_SIZE, total)}...")

        texts = [chunk.content for chunk in batch]

        # API call instead of loading heavy model into memory
        embeddings = get_gemini_embedding(texts, task_type="retrieval_document")

        collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=[f"chunk_{chunk.id}" for chunk in batch],
            metadatas=[{
                "chunk_id": chunk.id,
                "file_path": chunk.file_path,
                "chunk_index": chunk.chunk_index,
                "repo_id": repo_id
            } for chunk in batch]
        )

    print(f"Done! All {total} chunks are now searchable.")
    return total


def search_similar_chunks(repo_id, query, top_k=5):
    collection = get_collection(repo_id)

    # Convert question to embedding using query task type
    query_embedding = get_gemini_embedding([query], task_type="retrieval_query")

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    chunks = []
    if results['documents'] and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            chunks.append({
                'content': doc,
                'file_path': results['metadatas'][0][i]['file_path'],
                'score': round(1 - results['distances'][0][i], 3)
            })

    return chunks


def delete_collection(repo_id):
    try:
        get_chroma_client().delete_collection(f"repo_{repo_id}")
        print(f"Deleted ChromaDB collection for repo {repo_id}")
    except Exception as e:
        print(f"Could not delete ChromaDB collection: {e}")
