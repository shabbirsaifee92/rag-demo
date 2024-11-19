from typing import List, Dict, Any, Optional
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from .document_processor import DocumentProcessor
from ..utils.query_classifier import QueryClassifier, QueryType, QueryComplexity
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI assistant specialized in SOX (Sarbanes-Oxley Act) compliance.
Your task is to provide accurate, clear, and concise answers to questions about SOX compliance documents.
Base your answers strictly on the provided context. If you're unsure or the information isn't in the context, say so.
Always cite your sources using the provided document references.

Consider the query type and complexity level provided, and adjust your response accordingly:
- For simple queries: Provide direct, concise answers
- For moderate queries: Include relevant context and basic explanations
- For complex queries: Provide detailed analysis and multiple perspectives
- For expert queries: Include comprehensive analysis, implications, and connections to broader compliance frameworks

Format your response in a clear, structured manner using markdown when appropriate."""

class QueryService:
    def __init__(self, doc_processor: DocumentProcessor):
        """Initialize the query service with document processor and LLM."""
        self.doc_processor = doc_processor
        self.query_classifier = QueryClassifier()

        # Initialize Mistral model and tokenizer
        self.model = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.1",
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.1"
        )

        # Set device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

    def _format_prompt(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        query_analysis: Dict[str, Any]
    ) -> str:
        """Format the prompt with system message, context, and query."""
        # Format context sections by type
        context_sections = {
            'text': [],
            'table': [],
            'annotation': []
        }

        for ctx in contexts:
            chunk_type = ctx.get('chunk_type', 'text')
            context_sections[chunk_type].append(
                f"Document: {ctx['source']}, Page: {ctx['page']}\n{ctx['content']}"
            )

        # Build context string with sections
        context_str = ""
        for section_type, contents in context_sections.items():
            if contents:
                context_str += f"\n{section_type.upper()} CONTENT:\n"
                context_str += "\n\n".join(contents)

        # Add query analysis for better context
        query_context = f"""
Query Type: {query_analysis['query_type']}
Complexity: {query_analysis['complexity']}
Temporal Context: {json.dumps(query_analysis['temporal_context'])}
"""

        prompt = f"""{SYSTEM_PROMPT}

QUERY ANALYSIS:
{query_context}

CONTEXT:
{context_str}

Question: {query}

Answer: Let me help you with that based on the SOX compliance documents provided."""

        return prompt

    def _format_references(
        self,
        contexts: List[Dict[str, Any]],
        query_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Format the reference sources for citation."""
        references = []
        for ctx in contexts:
            reference = {
                "document": ctx["source"],
                "page": ctx["page"],
                "excerpt": ctx["content"][:200] + "...",  # First 200 chars as preview
                "relevance_type": ctx.get("chunk_type", "text"),
                "confidence": self._calculate_reference_confidence(
                    ctx,
                    query_analysis
                )
            }
            references.append(reference)
        return references

    def _calculate_reference_confidence(
        self,
        context: Dict[str, Any],
        query_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for a reference based on context and query analysis."""
        base_confidence = 0.7

        # Adjust based on chunk type
        type_weights = {
            'text': 1.0,
            'table': 0.9,
            'annotation': 0.8
        }
        type_factor = type_weights.get(context.get('chunk_type', 'text'), 0.7)

        # Adjust based on query complexity
        complexity_weights = {
            'simple': 1.0,
            'moderate': 0.9,
            'complex': 0.8,
            'expert': 0.7
        }
        complexity_factor = complexity_weights.get(
            query_analysis['complexity'],
            0.7
        )

        # Calculate final confidence
        confidence = base_confidence * type_factor * complexity_factor

        return min(1.0, max(0.0, confidence))

    def generate_response(self, prompt: str) -> str:
        """Generate a response using the LLM."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                max_length=2048,
                temperature=0.7,
                top_p=0.95,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract the answer part after "Answer: "
        return response.split("Answer: ")[-1].strip()

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query and return the response with sources."""
        try:
            # Analyze query
            query_analysis = self.query_classifier.classify_query(query)
            logger.info(f"Query analysis: {json.dumps(query_analysis)}")

            # Determine number of contexts based on complexity
            num_contexts = {
                'simple': 3,
                'moderate': 5,
                'complex': 7,
                'expert': 10
            }.get(query_analysis['complexity'], 5)

            # Retrieve relevant documents
            relevant_docs = self.doc_processor.query_similar(
                query,
                limit=num_contexts
            )

            if not relevant_docs:
                return {
                    "answer": "I couldn't find any relevant information in the SOX compliance documents to answer your question.",
                    "sources": [],
                    "confidence": 0.0,
                    "query_analysis": query_analysis
                }

            # Format prompt with context
            prompt = self._format_prompt(query, relevant_docs, query_analysis)

            # Generate response
            response = self.generate_response(prompt)

            # Format sources for reference
            sources = self._format_references(relevant_docs, query_analysis)

            # Calculate overall confidence
            confidence = min(
                query_analysis['confidence_score'],
                sum(s['confidence'] for s in sources) / len(sources)
            )

            return {
                "answer": response,
                "sources": sources,
                "confidence": confidence,
                "query_analysis": query_analysis
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
