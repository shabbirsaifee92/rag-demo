import unittest
from ..utils.query_classifier import QueryClassifier, QueryType, QueryComplexity
import spacy

class TestQueryClassifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the classifier once for all tests."""
        cls.classifier = QueryClassifier()

    def test_query_type_classification(self):
        """Test different types of query classification."""
        test_cases = [
            {
                'query': "What are the basic SOX compliance requirements?",
                'expected_type': QueryType.COMPLIANCE
            },
            {
                'query': "When was the last audit performed?",
                'expected_type': QueryType.TEMPORAL
            },
            {
                'query': "How do internal controls affect financial reporting?",
                'expected_type': QueryType.ANALYTICAL
            },
            {
                'query': "What is the process for documenting control changes?",
                'expected_type': QueryType.PROCEDURAL
            }
        ]

        for case in test_cases:
            result = self.classifier._determine_query_type(
                case['query'],
                self.classifier.nlp(case['query'])
            )
            self.assertEqual(
                result,
                case['expected_type'],
                f"Failed for query: {case['query']}"
            )

    def test_complexity_assessment(self):
        """Test complexity assessment of different queries."""
        test_cases = [
            {
                'query': "What is SOX?",
                'expected_complexity': QueryComplexity.SIMPLE
            },
            {
                'query': "How are internal controls documented and tested?",
                'expected_complexity': QueryComplexity.MODERATE
            },
            {
                'query': "Compare the effectiveness of preventive and detective controls in our current framework.",
                'expected_complexity': QueryComplexity.COMPLEX
            },
            {
                'query': "Analyze the implications of implementing a new control framework on our existing compliance strategy and risk assessment methodology.",
                'expected_complexity': QueryComplexity.EXPERT
            }
        ]

        for case in test_cases:
            result = self.classifier._assess_complexity(
                case['query'],
                self.classifier.nlp(case['query'])
            )
            self.assertEqual(
                result,
                case['expected_complexity'],
                f"Failed for query: {case['query']}"
            )

    def test_entity_extraction(self):
        """Test named entity extraction from queries."""
        query = "Review SOX compliance for Q2 2023 financial statements."
        doc = self.classifier.nlp(query)
        entities = self.classifier._extract_entities(doc)

        self.assertTrue(len(entities) > 0)
        self.assertTrue(any(entity['text'] == 'SOX' for entity in entities))
        self.assertTrue(any(entity['text'] == 'Q2 2023' for entity in entities))

    def test_temporal_context(self):
        """Test temporal context identification."""
        test_cases = [
            {
                'query': "What are the current control requirements?",
                'expected_temporal': True
            },
            {
                'query': "Show audit results from last quarter.",
                'expected_temporal': True
            },
            {
                'query': "List all controls.",
                'expected_temporal': False
            }
        ]

        for case in test_cases:
            doc = self.classifier.nlp(case['query'])
            result = self.classifier._identify_temporal_context(case['query'], doc)
            self.assertEqual(
                result['has_temporal_aspect'],
                case['expected_temporal'],
                f"Failed for query: {case['query']}"
            )

    def test_augmentation_suggestions(self):
        """Test query augmentation suggestions generation."""
        query = "Analyze control effectiveness"
        doc = self.classifier.nlp(query)
        query_type = self.classifier._determine_query_type(query, doc)
        complexity = self.classifier._assess_complexity(query, doc)
        entities = self.classifier._extract_entities(doc)

        suggestions = self.classifier._generate_augmentation_suggestions(
            query, query_type, complexity, entities
        )

        self.assertTrue(isinstance(suggestions, list))
        self.assertTrue(len(suggestions) > 0)

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        test_cases = [
            {
                'query_type': QueryType.FACTUAL,
                'complexity': QueryComplexity.SIMPLE,
                'entities': [{'text': 'SOX', 'type': 'ORG'}],
                'min_expected_confidence': 0.7
            },
            {
                'query_type': QueryType.ANALYTICAL,
                'complexity': QueryComplexity.COMPLEX,
                'entities': [],
                'max_expected_confidence': 0.7
            }
        ]

        for case in test_cases:
            confidence = self.classifier._calculate_confidence(
                case['query_type'],
                case['complexity'],
                case['entities']
            )

            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)

            if 'min_expected_confidence' in case:
                self.assertGreaterEqual(
                    confidence,
                    case['min_expected_confidence']
                )
            if 'max_expected_confidence' in case:
                self.assertLessEqual(
                    confidence,
                    case['max_expected_confidence']
                )

    def test_full_query_classification(self):
        """Test complete query classification pipeline."""
        query = "Analyze the impact of recent control changes on our SOX compliance status for Q3 2023."
        result = self.classifier.classify_query(query)

        self.assertIn('query_type', result)
        self.assertIn('complexity', result)
        self.assertIn('entities', result)
        self.assertIn('temporal_context', result)
        self.assertIn('augmentation_suggestions', result)
        self.assertIn('confidence_score', result)

        self.assertTrue(isinstance(result['entities'], list))
        self.assertTrue(isinstance(result['augmentation_suggestions'], list))
        self.assertTrue(0 <= result['confidence_score'] <= 1)

    def test_edge_cases(self):
        """Test edge cases and potential error conditions."""
        # Empty query
        empty_result = self.classifier.classify_query("")
        self.assertTrue(empty_result['confidence_score'] < 0.5)

        # Very long query
        long_query = "What is the impact of " + "control " * 100
        long_result = self.classifier.classify_query(long_query)
        self.assertTrue(isinstance(long_result['confidence_score'], float))

        # Special characters
        special_chars_query = "What is the impact of @#$%^&* on controls?"
        special_result = self.classifier.classify_query(special_chars_query)
        self.assertTrue(isinstance(special_result['confidence_score'], float))

if __name__ == '__main__':
    unittest.main()
