from typing import Dict, List, Tuple
import re
from enum import Enum
import spacy
from transformers import pipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    FACTUAL = "factual"  # Simple fact-based queries
    ANALYTICAL = "analytical"  # Requires analysis of multiple sources
    COMPLIANCE = "compliance"  # Specific compliance-related queries
    PROCEDURAL = "procedural"  # Process or procedure-related queries
    TEMPORAL = "temporal"  # Time-based or historical queries

class QueryComplexity(Enum):
    SIMPLE = "simple"  # Single-fact queries
    MODERATE = "moderate"  # Multi-fact queries
    COMPLEX = "complex"  # Analysis and synthesis required
    EXPERT = "expert"  # Deep domain expertise required

class QueryClassifier:
    def __init__(self):
        """Initialize the query classifier with NLP models and patterns."""
        # Load spaCy model for NLP tasks
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

        # Zero-shot classifier for query type
        self.zero_shot = pipeline("zero-shot-classification")

        # Initialize pattern matchers
        self._init_patterns()

    def _init_patterns(self):
        """Initialize regex patterns for query classification."""
        self.patterns = {
            'compliance_keywords': [
                r'compliance', r'regulation', r'requirement', r'audit',
                r'control', r'policy', r'procedure', r'sox', r'sarbanes',
                r'oxley', r'internal control', r'framework'
            ],
            'temporal_indicators': [
                r'when', r'date', r'period', r'timeline', r'history',
                r'past', r'future', r'schedule', r'deadline'
            ],
            'complexity_indicators': {
                'complex': [
                    r'compare', r'analyze', r'evaluate', r'assess',
                    r'implications', r'impact', r'relationship'
                ],
                'expert': [
                    r'strategic', r'optimization', r'integration',
                    r'architecture', r'framework', r'methodology'
                ]
            }
        }

    def classify_query(self, query: str) -> Dict[str, any]:
        """
        Classify the query by type, complexity, and extract key characteristics.

        Args:
            query: The input query string

        Returns:
            Dictionary containing query classification details
        """
        # Process query with spaCy
        doc = self.nlp(query)

        # Determine query type
        query_type = self._determine_query_type(query, doc)

        # Assess complexity
        complexity = self._assess_complexity(query, doc)

        # Extract key entities and concepts
        entities = self._extract_entities(doc)

        # Identify temporal aspects
        temporal_context = self._identify_temporal_context(query, doc)

        # Generate query augmentation suggestions
        augmentation = self._generate_augmentation_suggestions(
            query, query_type, complexity, entities
        )

        return {
            'query_type': query_type.value,
            'complexity': complexity.value,
            'entities': entities,
            'temporal_context': temporal_context,
            'augmentation_suggestions': augmentation,
            'confidence_score': self._calculate_confidence(
                query_type, complexity, entities
            )
        }

    def _determine_query_type(self, query: str, doc) -> QueryType:
        """Determine the type of query using multiple classification approaches."""
        # Use zero-shot classification for query type
        candidate_labels = [qt.value for qt in QueryType]
        result = self.zero_shot(
            query,
            candidate_labels,
            hypothesis_template="This is a {} question."
        )

        # Get the highest scoring label
        primary_type = QueryType(result['labels'][0])

        # Check for compliance-specific patterns
        if any(re.search(pattern, query.lower())
              for pattern in self.patterns['compliance_keywords']):
            return QueryType.COMPLIANCE

        # Check for temporal patterns
        if any(re.search(pattern, query.lower())
              for pattern in self.patterns['temporal_indicators']):
            return QueryType.TEMPORAL

        return primary_type

    def _assess_complexity(self, query: str, doc) -> QueryComplexity:
        """Assess the complexity of the query."""
        # Count relevant features
        num_entities = len([ent for ent in doc.ents])
        num_clauses = len([token for token in doc if token.dep_ == 'mark'])
        word_count = len([token for token in doc if not token.is_punct])

        # Check for complexity indicators
        complex_indicators = sum(1 for pattern in self.patterns['complexity_indicators']['complex']
                               if re.search(pattern, query.lower()))
        expert_indicators = sum(1 for pattern in self.patterns['complexity_indicators']['expert']
                               if re.search(pattern, query.lower()))

        # Determine complexity based on multiple factors
        if expert_indicators > 0 or (complex_indicators >= 2 and num_clauses >= 3):
            return QueryComplexity.EXPERT
        elif complex_indicators > 0 or (num_entities >= 3 and num_clauses >= 2):
            return QueryComplexity.COMPLEX
        elif num_entities >= 2 or num_clauses >= 1 or word_count > 15:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE

    def _extract_entities(self, doc) -> List[Dict[str, str]]:
        """Extract and categorize named entities from the query."""
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'type': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
        return entities

    def _identify_temporal_context(self, query: str, doc) -> Dict[str, any]:
        """Identify temporal aspects of the query."""
        temporal_context = {
            'has_temporal_aspect': False,
            'temporal_type': None,
            'temporal_references': []
        }

        # Check for temporal indicators
        for pattern in self.patterns['temporal_indicators']:
            matches = re.finditer(pattern, query.lower())
            for match in matches:
                temporal_context['has_temporal_aspect'] = True
                temporal_context['temporal_references'].append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })

        # Extract temporal entities from spaCy
        temporal_ents = [ent for ent in doc.ents if ent.label_ in ['DATE', 'TIME']]
        for ent in temporal_ents:
            temporal_context['has_temporal_aspect'] = True
            temporal_context['temporal_references'].append({
                'text': ent.text,
                'type': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })

        return temporal_context

    def _generate_augmentation_suggestions(
        self,
        query: str,
        query_type: QueryType,
        complexity: QueryComplexity,
        entities: List[Dict[str, str]]
    ) -> List[str]:
        """Generate suggestions for query augmentation."""
        suggestions = []

        # Add context-specific augmentations
        if query_type == QueryType.COMPLIANCE:
            suggestions.append("Include relevant regulatory framework references")

        if complexity in [QueryComplexity.COMPLEX, QueryComplexity.EXPERT]:
            suggestions.append("Break down into sub-queries for detailed analysis")

        if not entities:
            suggestions.append("Add specific entity references for better context")

        return suggestions

    def _calculate_confidence(
        self,
        query_type: QueryType,
        complexity: QueryComplexity,
        entities: List[Dict[str, str]]
    ) -> float:
        """Calculate confidence score for the classification."""
        base_confidence = 0.7  # Base confidence score

        # Adjust based on entities present
        entity_factor = min(len(entities) * 0.1, 0.2)

        # Adjust based on complexity
        complexity_factor = {
            QueryComplexity.SIMPLE: 0.1,
            QueryComplexity.MODERATE: 0.05,
            QueryComplexity.COMPLEX: -0.05,
            QueryComplexity.EXPERT: -0.1
        }[complexity]

        # Calculate final confidence
        confidence = base_confidence + entity_factor + complexity_factor

        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
