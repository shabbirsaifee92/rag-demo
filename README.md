# SOX Compliance RAG System

A production-grade Retrieval-Augmented Generation (RAG) application designed to handle company SOX (Sarbanes-Oxley Act) compliance documents and assist auditors by answering their queries.

## Architecture

### Frontend
- React-based web interface with Material-UI
- Document upload dashboard
- Interactive query interface with source citations
- Responsive design for various devices

### Backend
- FastAPI-based REST API
- Mistral LLM for natural language processing
- Weaviate vector database for efficient document retrieval
- Document processing pipeline with OCR capabilities

### Infrastructure
- Containerized with Docker
- Kubernetes deployment ready
- GPU support for ML operations
- Horizontal scaling capabilities

## Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (for production deployment)
- NVIDIA GPU with CUDA support (recommended)
- Node.js 18+ (for local development)
- Python 3.9+ (for local development)

## Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd sox-rag-demo
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Start the development environment:
```bash
docker-compose up
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Weaviate: http://localhost:8080

## Production Deployment

### Building Docker Images

1. Build backend image:
```bash
docker build -t sox-rag-backend:latest ./backend
```

2. Build frontend image:
```bash
docker build -t sox-rag-frontend:latest ./frontend
```

### Kubernetes Deployment

1. Apply Kubernetes configurations:
```bash
kubectl apply -f k8s/weaviate-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

2. Verify deployments:
```bash
kubectl get pods
kubectl get services
kubectl get ingress
```

## Features

### Document Processing
- Support for PDF and DOCX formats
- OCR for scanned documents
- Text extraction and preprocessing
- Efficient chunking for optimal retrieval

### Query System
- Natural language query processing
- Context-aware responses
- Source citations for transparency
- Confidence scoring

### Security
- Document encryption
- Access control
- Audit logging
- Secure API endpoints

## API Documentation

The API documentation is available at `http://localhost:8000/docs` when running locally.

### Key Endpoints

- `POST /documents/upload`: Upload SOX compliance documents
- `POST /query`: Query the document database
- `GET /health`: Health check endpoint

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)
