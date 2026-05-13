import os #handles files path and interacts with OS
import sys #used to manipulate path
import glob #used to serch files
import uuid #used to generate unique ids for each chunk
from typing import List #used to hint the type of variables

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient, models #used to interact with Qdrant
from fastembed import TextEmbedding, SparseTextEmbedding #used to generate embeddings
from groq import Groq #used to generate contextual descriptions
from src.config import settings #used to get settings
from rich.console import Console #used to print colorful output

console = Console()

class Ingestor:
    def __init__(self):
        self.qdrant = QdrantClient(url=settings.QDRANT_URL)
        self.groq = Groq(api_key=settings.GROQ_API_KEY)
        self.dense_model = TextEmbedding(model_name=settings.DENSE_MODEL)
        self.sparse_model = SparseTextEmbedding(model_name=settings.SPARSE_MODEL)
        self.collection_name = settings.QDRANT_COLLECTION

    def setup_collection(self):
        """Initialize Qdrant collection with hybrid indexing."""
        if not self.qdrant.collection_exists(self.collection_name):
            console.print(f"[bold green]Creating collection: {self.collection_name}...[/]")
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=384, # Size for BGE-small
                        distance=models.Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(),
                        modifier=models.Modifier.IDF
                    )
                }
            )

    def get_contextual_description(self, doc_text: str, chunk_text: str) -> str:
        """Anthropic's Contextual Retrieval: Generates a brief context for a chunk."""
        prompt = f"""<document>
{doc_text}
</document>
Here is the chunk we want to situate within the whole document:
<chunk>
{chunk_text}
</chunk>
Please give a short, succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""
        
        try:
            response = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=settings.CONTEXT_MODEL,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            console.print(f"[red]Error generating context: {e}[/]")
            return ""

    def process_file(self, file_path: str):
        console.print(f"[blue]Processing: {file_path}...[/]")
        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()

        # Simple chunking by paragraph for demonstration (could use LangChain/LlamaIndex)
        chunks = [c.strip() for c in full_text.split("\n\n") if c.strip()]
        
        points = []
        for i, chunk in enumerate(chunks):
            # 1. Generate Context
            context = self.get_contextual_description(full_text, chunk)
            enriched_text = f"{context}\n\n{chunk}" if context else chunk
            
            # 2. Generate Embeddings
            dense_vec = list(self.dense_model.embed([enriched_text]))[0]
            sparse_vec_obj = list(self.sparse_model.embed([enriched_text]))[0]
            
            # Convert SparseEmbedding to Qdrant SparseVector
            sparse_vec = models.SparseVector(
                indices=sparse_vec_obj.indices.tolist(),
                values=sparse_vec_obj.values.tolist()
            )

            points.append(models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{file_path}_{i}")),
                vector={
                    "dense": dense_vec.tolist(),
                    "sparse": sparse_vec
                },
                payload={
                    "text": chunk,
                    "enriched_text": enriched_text,
                    "source": file_path,
                    "context": context
                }
            ))
        
        if points:
            self.qdrant.upsert(collection_name=self.collection_name, points=points)
            console.print(f"[green]Successfully ingested {len(points)} chunks from {file_path}[/]")

    def run(self):
        self.setup_collection()
        files = glob.glob("knowledge/**/*.md", recursive=True)
        for f in files:
            self.process_file(f)

if __name__ == "__main__":
    if not settings.GROQ_API_KEY:
        console.print("[bold red]Please set GROQ_API_KEY in .env file![/]")
    else:
        Ingestor().run()
