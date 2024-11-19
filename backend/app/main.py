from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel, Field
import uvicorn
import os
from .services.document_processor import DocumentProcessor
from .services.query_service import QueryService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SOX Compliance RAG API",
    description="API for SOX compliance document processing and querying",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response Models
class Source(BaseModel):
    document: str
    page: int
    excerpt: str
    relevance_type: str = Field(..., description="Type of content (text, table, annotation)")
    confidence: float = Field(..., ge=0.0, le=1.0)

class TemporalContext(BaseModel):
    has_temporal_aspect: bool
    temporal_type: Optional[str]
    temporal_references: List[dict]

class QueryAnalysis(BaseModel):
    query_type: str
    complexity: str
    entities: List[dict]
    temporal_context: TemporalContext
    augmentation_suggestions: List[str]
    confidence_score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence: float
    query_analysis: QueryAnalysis

class UploadResponse(BaseModel):
    message: str
    processed_chunks: int
    statistics: dict

class QueryRequest(BaseModel):
    query: str
    include_analysis: bool = Field(
        default=False,
        description="Include detailed query analysis in response"
    )

# Dependencies
def get_document_processor():
    return DocumentProcessor(
        weaviate_url=os.getenv("WEAVIATE_URL", "http://localhost:8080")
    )

def get_query_service(doc_processor: DocumentProcessor = Depends(get_document_processor)):
    return QueryService(doc_processor)

@app.get("/")
async def root():
    return {"message": "SOX Compliance RAG API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/documents/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    doc_processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Upload SOX compliance documents for processing and indexing.
    Handles PDF, DOCX, and image files with OCR capabilities.
    """
    try:
        total_chunks = 0
        for file in files:
            content = await file.read()
            chunks_processed = await doc_processor.process_uploaded_file(
                content,
                file.filename
            )
            total_chunks += chunks_processed

        # Get updated statistics
        statistics = doc_processor.get_document_statistics()

        return UploadResponse(
            message=f"Successfully processed {len(files)} documents",
            processed_chunks=total_chunks,
            statistics=statistics
        )
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing documents: {str(e)}"
        )

@app.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    query_service: QueryService = Depends(get_query_service)
):
    """
    Query the SOX compliance documents with advanced analysis and context handling.
    """
    try:
        result = await query_service.process_query(request.query)
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@app.get("/statistics")
async def get_statistics(
    doc_processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Get statistics about processed documents and system usage.
    """
    try:
        return doc_processor.get_document_statistics()
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting statistics: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
