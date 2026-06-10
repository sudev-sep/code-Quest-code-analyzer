import os
from core.models import FileChunk, Repository

CHROMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'chromadb_store'
)

_embedding_model = None
_chroma_client = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        print("Loading embedding model...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model ready!")
    return _embedding_model


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _chroma_client


def get_collection(repo_id):
    """
    Each repo gets its own collection in ChromaDB.
    Think of a collection like a separate drawer in a filing cabinet.
    """
    return get_chroma_client().get_or_create_collection(
        name=f"repo_{repo_id}",
        metadata={"hnsw:space": "cosine"}  # cosine = best for text similarity
    )


def embed_repository(repo_id):
    repo = Repository.objects.get(id=repo_id)
    print(f"\nStarting embedding for: {repo.name}")

    # Get all chunks for this repo from the database
    chunks = FileChunk.objects.filter(repository=repo)
    total = chunks.count()

    if total == 0:
        print("No chunks found! Run parsing first.")
        return

    print(f"Found {total} chunks to embed...")

    # Get or create the ChromaDB collection for this repo
    collection = get_collection(repo_id)

    # Delete old embeddings if re-running
    try:
        get_chroma_client().delete_collection(f"repo_{repo_id}")
        collection = get_collection(repo_id)
    except Exception:
        pass

    # Process in batches of 50 — embedding all 260 at once would use too much memory
    BATCH_SIZE = 50
    chunk_list = list(chunks)

    for batch_start in range(0, total, BATCH_SIZE):
        batch = chunk_list[batch_start:batch_start + BATCH_SIZE]

        print(f"  Embedding chunks {batch_start + 1} to {min(batch_start + BATCH_SIZE, total)}...")

        # Extract the text content from each chunk
        texts = [chunk.content for chunk in batch]

        # THIS IS THE MAGIC LINE
        # model.encode() converts each chunk of text into a list of numbers
        # e.g. "payment logic" → [0.23, 0.87, 0.12, 0.45, ...]
        embeddings = get_embedding_model().encode(texts, show_progress_bar=False)

        # Save to ChromaDB
        # We need: the text, the numbers, and a unique ID for each chunk
        collection.add(
            documents=texts,
            embeddings=embeddings.tolist(),
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
    """
    Given a question, find the most relevant code chunks.

    How it works:
    1. Convert the question into numbers using the same model
    2. Find chunks whose numbers are closest to the question's numbers
    3. Return those chunks
    """
    collection = get_collection(repo_id)

    # Convert the question to numbers
    query_embedding = get_embedding_model().encode([query]).tolist()

    # Search ChromaDB for the closest matches
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    # Format nicely for use in our views
    chunks = []
    if results['documents'] and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            chunks.append({
                'content': doc,
                'file_path': results['metadatas'][0][i]['file_path'],
                'score': round(1 - results['distances'][0][i], 3)  # convert distance to similarity score
            })

    return chunks



def delete_collection(repo_id):
    """
    Deletes the ChromaDB collection for a repo when the repo is deleted.
    """
    try:
        get_chroma_client().delete_collection(f"repo_{repo_id}")
        print(f"Deleted ChromaDB collection for repo {repo_id}")
    except Exception as e:
        print(f"Could not delete ChromaDB collection: {e}")