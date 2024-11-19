import weaviate
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
import tempfile
import logging
from sentence_transformers import SentenceTransformer
from ..utils.document_preprocessor import DocumentPreprocessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, weaviate_url: Optional[str] = None):
        """Initialize the document processor with Weaviate client and embedding model."""
        self.client = weaviate.Client(
            url=weaviate_url or os.getenv("WEAVIATE_URL", "http://localhost:8080")
        )
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.doc_preprocessor = DocumentPreprocessor()
        self._setup_schema()

    def _setup_schema(self):
        """Set up the Weaviate schema for document chunks."""
        schema = {
            "classes": [{
                "class": "Document",
                "description": "A chunk of text from a SOX compliance document",
                "vectorizer": "none",  # We'll provide our own vectors
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "The text content of the document chunk"
                    },
                    {
                        "name": "source",
                        "dataType": ["string"],
                        "description": "The source document name"
                    },
                    {
                        "name": "page",
                        "dataType": ["int"],
                        "description": "The page number in the source document"
                    },
                    {
                        "name": "chunk_type",
                        "dataType": ["string"],
                        "description": "Type of content (text, table, annotation)"
                    },
                    {
                        "name": "metadata",
                        "dataType": ["object"],
                        "description": "Additional metadata about the chunk"
                    }
                ]
            }]
        }

        try:
            self.client.schema.create(schema)
        except weaviate.exceptions.UnexpectedStatusCodeException as e:
            if "already exists" not in str(e):
                raise
            logger.info("Schema already exists")

    def process_document(self, file_path: str, source_name: str) -> List[Dict[str, Any]]:
        """Process a document and split it into chunks."""
        try:
            chunks = self.doc_preprocessor.process_document(
                open(file_path, 'rb').read(),
                file_path
            )

            processed_chunks = []
            for chunk in chunks:
                processed_chunk = {
                    "content": chunk["content"],
                    "source": source_name,
                    "page": chunk["page"],
                    "chunk_type": chunk["type"],
                    "metadata": chunk["metadata"]
                }
                processed_chunks.append(processed_chunk)

            return processed_chunks
        except Exception as e:
            logger.error(f"Error processing document {source_name}: {str(e)}")
            raise

    def embed_and_store(self, chunks: List[Dict[str, Any]]):
        """Embed text chunks and store them in Weaviate."""
        batch = self.client.batch.configure(
            batch_size=50,
            dynamic=True,
            timeout_retries=3
        )

        try:
            with batch:
                for chunk in chunks:
                    # Generate embedding for the chunk
                    embedding = self.embedder.encode(chunk["content"]).tolist()

                    # Prepare metadata
                    metadata = chunk["metadata"]
                    metadata.update({
                        "embedding_model": "all-MiniLM-L6-v2",
                        "chunk_type": chunk["chunk_type"]
                    })

                    # Store in Weaviate
                    self.client.batch.add_data_object(
                        data_object={
                            "content": chunk["content"],
                            "source": chunk["source"],
                            "page": chunk["page"],
                            "chunk_type": chunk["chunk_type"],
                            "metadata": metadata
                        },
                        class_name="Document",
                        vector=embedding
                    )
        except Exception as e:
            logger.error(f"Error storing chunks in Weaviate: {str(e)}")
            raise

    def query_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Query similar documents based on the input query."""
        try:
            query_embedding = self.embedder.encode(query).tolist()

            result = (
                self.client.query
                .get("Document", [
                    "content",
                    "source",
                    "page",
                    "chunk_type",
                    "metadata"
                ])
                .with_near_vector({
                    "vector": query_embedding,
                    "certainty": 0.7
                })
                .with_limit(limit)
                .do()
            )

            return result.get("data", {}).get("Get", {}).get("Document", [])
        except Exception as e:
            logger.error(f"Error querying similar documents: {str(e)}")
            raise

    async def process_uploaded_file(self, file_content: bytes, filename: str):
        """Process an uploaded file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            # Process the document
            chunks = self.doc_preprocessor.process_document(file_content, filename)

            # Embed and store chunks
            self.embed_and_store(chunks)

            return len(chunks)
        except Exception as e:
            logger.error(f"Error processing uploaded file {filename}: {str(e)}")
            raise
        finally:
            os.unlink(tmp_path)

    def get_document_statistics(self) -> Dict[str, Any]:
        """Get statistics about processed documents."""
        try:
            result = (
                self.client.query
                .aggregate("Document")
                .with_meta_count()
                .with_fields("meta { count }")
                .do()
            )

            total_chunks = result["data"]["Aggregate"]["Document"][0]["meta"]["count"]

            # Get chunk type distribution
            type_distribution = (
                self.client.query
                .aggregate("Document")
                .with_group_by_filter("chunk_type")
                .with_fields("groupedBy { value } meta { count }")
                .do()
            )

            return {
                "total_chunks": total_chunks,
                "chunk_type_distribution": type_distribution["data"]["Aggregate"]["Document"]
            }
        except Exception as e:
            logger.error(f"Error getting document statistics: {str(e)}")
            raise
