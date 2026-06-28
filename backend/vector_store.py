import os
import re
import uuid
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
import pypdf
import docx2txt
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Setup directories
CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
COLLECTION_NAME = "company_knowledge"

class FlexibleEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Real-life RAG operations require a valid Gemini API key.")
        
        try:
            genai.configure(api_key=self.api_key)
            # Test call to check if key is valid
            genai.embed_content(
                model="models/embedding-001",
                content="test",
                task_type="retrieval_document"
            )
            print("Successfully initialized Gemini API Embeddings.")
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini embeddings: {e}. Ensure your API key is valid.")

    def __call__(self, input: Documents) -> Embeddings:
        try:
            response = genai.embed_content(
                model="models/embedding-001",
                content=input,
                task_type="retrieval_document"
            )
            embeddings = response.get('embedding', [])
            if embeddings and not isinstance(embeddings[0], list):
                return [embeddings]
            return embeddings
        except Exception as e:
            raise RuntimeError(f"Gemini API embedding request failed: {e}")

def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_DIR)

def get_collection():
    client = get_chroma_client()
    ef = FlexibleEmbeddingFunction()
    return client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=ef)

def extract_text_from_file(filepath):
    _, ext = os.path.splitext(filepath.lower())
    if ext == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    elif ext == ".pdf":
        text = ""
        with open(filepath, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    elif ext == ".docx":
        return docx2txt.process(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def chunk_text(text, chunk_size=300, chunk_overlap=30):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_len = len(sentence.split())
        if current_length + sentence_len > chunk_size:
            chunks.append(" ".join(current_chunk))
            overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk[-1:]
            current_chunk = overlap_sentences + [sentence]
            current_length = sum(len(s.split()) for s in current_chunk)
        else:
            current_chunk.append(sentence)
            current_length += sentence_len
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    chunks = [c.strip() for c in chunks if c.strip()]
    return chunks

def index_document(filepath, filename):
    try:
        text = extract_text_from_file(filepath)
        chunks = chunk_text(text)
        if not chunks:
            return 0
            
        collection = get_collection()
        
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"filename": filename, "source": filepath} for _ in chunks]
        
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        return len(chunks)
    except Exception as e:
        print(f"Error indexing document {filename}: {e}")
        raise e

# -------------------------------------------------------------
# Hybrid Search & Reranking Engine
# -------------------------------------------------------------

def query_knowledge_base(query, n_results=4):
    """
    Performs hybrid search: combining ChromaDB vector search and local keyword search,
    followed by local TF-IDF Cosine similarity reranking.
    """
    try:
        collection = get_collection()
        total_chunks = collection.count()
        if total_chunks == 0:
            return []
            
        # 1. Vector Search Retrieval
        vector_hits = []
        try:
            results = collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, total_chunks)
            )
            docs = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            for doc, meta in zip(docs, metadatas):
                vector_hits.append({
                    "content": doc,
                    "source": meta.get("filename", "Unknown Document"),
                    "retrieval_method": "Vector Search"
                })
        except Exception as e:
            print(f"Vector search failure: {e}")
            
        # 2. Local Keyword Search Retrieval
        keyword_hits = []
        try:
            # Query all database elements
            all_chunks = collection.get(include=["documents", "metadatas"])
            all_docs = all_chunks.get("documents", [])
            all_metas = all_chunks.get("metadatas", [])
            
            # Simple keyword matching: split query into terms
            query_terms = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
            
            if query_terms:
                for doc, meta in zip(all_docs, all_metas):
                    doc_lower = doc.lower()
                    matches = sum(1 for term in query_terms if term in doc_lower)
                    if matches > 0:
                        keyword_hits.append({
                            "content": doc,
                            "source": meta.get("filename", "Unknown Document"),
                            "retrieval_method": "Keyword Matching",
                            "matches": matches
                        })
                # Sort keyword hits by term matches count
                keyword_hits = sorted(keyword_hits, key=lambda x: x["matches"], reverse=True)[:n_results * 2]
        except Exception as e:
            print(f"Keyword search failure: {e}")
            
        # 3. Combine and Deduplicate hits
        seen_content = set()
        combined_hits = []
        for hit in vector_hits + keyword_hits:
            content_hash = hit["content"].strip()
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                combined_hits.append(hit)
                
        if not combined_hits:
            return []
            
        # 4. Local TF-IDF Reranking
        # We fit TF-IDF vectorizer on the retrieved documents + query and rank them by cosine similarity
        contents = [hit["content"] for hit in combined_hits]
        documents_list = contents + [query]
        
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(documents_list)
        
        # Calculate cosine similarity between each chunk and the query (which is the last element in matrix)
        query_vector = tfidf_matrix[-1]
        chunk_vectors = tfidf_matrix[:-1]
        
        similarities = cosine_similarity(chunk_vectors, query_vector).flatten()
        
        # Attach scores to hits
        for i, hit in enumerate(combined_hits):
            # Normalize to 0-100% confidence
            score = float(similarities[i])
            hit["confidence"] = min(int(score * 100 + 30), 99) if score > 0 else 30  # add base baseline confidence if matches
            
        # Sort by confidence score
        reranked_hits = sorted(combined_hits, key=lambda x: x["confidence"], reverse=True)
        
        # Return top N results
        return reranked_hits[:n_results]
        
    except Exception as e:
        print(f"Hybrid RAG error: {e}")
        return []

def get_kb_stats():
    try:
        collection = get_collection()
        count = collection.count()
        filenames = set()
        if count > 0:
            all_data = collection.get(include=["metadatas"])
            metadatas = all_data.get("metadatas", [])
            for meta in metadatas:
                if meta and "filename" in meta:
                    filenames.add(meta["filename"])
                    
        return {
            "total_chunks": count,
            "unique_documents": list(filenames),
            "document_count": len(filenames)
        }
    except Exception as e:
        print(f"Error getting KB stats: {e}")
        return {
            "total_chunks": 0,
            "unique_documents": [],
            "document_count": 0
        }

def delete_document_from_kb(filename: str):
    """Deletes all chunks associated with a specific filename from ChromaDB vector store."""
    try:
        collection = get_collection()
        collection.delete(where={"filename": filename})
        return True
    except Exception as e:
        print(f"Error deleting document {filename} from ChromaDB: {e}")
        return False
