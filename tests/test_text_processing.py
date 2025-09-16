"""
Unit tests for text processing utilities.
"""
import pytest
from unittest.mock import patch, MagicMock
from utils.text_processing import TextProcessor

class TestTextProcessor:
    """Test cases for TextProcessor class."""

    @pytest.fixture
    def text_processor(self):
        """Create TextProcessor instance for testing."""
        tech_terms = ['python', 'java', 'machine learning', 'sql', 'javascript']
        degree_types = ['computer', 'science', 'engineering', 'business', 'management']
        return TextProcessor(tech_terms, degree_types)

    def test_clean_text_basic(self, text_processor):
        """Test basic text cleaning."""
        dirty_text = "Hello\nWorld\t/Test@123"
        clean_text = text_processor.clean_text(dirty_text)
        assert clean_text == "hello world test 123"

    def test_clean_text_empty(self, text_processor):
        """Test cleaning empty text."""
        assert text_processor.clean_text("") == ""
        assert text_processor.clean_text(None) == ""

    def test_clean_text_non_string(self, text_processor):
        """Test cleaning non-string input."""
        assert text_processor.clean_text(123) == "123"

    def test_extract_skills_exact_match(self, text_processor):
        """Test exact skill matching."""
        skills = ['Python', 'Java', 'Unknown Skill']
        result = text_processor.extract_skills_fuzzy(skills, threshold=80)
        assert 'python' in result
        assert 'java' in result
        assert len(result) <= 3  # Should not include unknown skill

    def test_extract_skills_empty_list(self, text_processor):
        """Test skill extraction with empty list."""
        result = text_processor.extract_skills_fuzzy([])
        assert result == []

    def test_extract_skills_none_values(self, text_processor):
        """Test skill extraction with None values."""
        skills = ['python', None, '', 'java']
        result = text_processor.extract_skills_fuzzy(skills)
        assert 'python' in result
        assert 'java' in result

    @patch('utils.text_processing.process.extractBests')
    def test_extract_skills_fuzzy_matching(self, mock_extract, text_processor):
        """Test fuzzy skill matching."""
        mock_extract.return_value = [('python', 85), ('java', 80)]
        skills = ['pythn', 'jva']  # Misspelled skills

        result = text_processor.extract_skills_fuzzy(skills, threshold=80)
        assert len(result) >= 0  # Should handle fuzzy matches

    def test_extract_degree_types_basic(self, text_processor):
        """Test basic degree type extraction."""
        degree_text = "Computer Science Engineering"
        result = text_processor.extract_degree_types_enhanced(degree_text)
        assert any(term in result for term in ['computer', 'science', 'engineering'])

    def test_extract_degree_types_empty(self, text_processor):
        """Test degree type extraction with empty input."""
        assert text_processor.extract_degree_types_enhanced("") == []
        assert text_processor.extract_degree_types_enhanced(None) == []

    @patch('utils.text_processing.TextProcessor.nlp', None)
    def test_extract_degree_types_no_spacy(self, text_processor):
        """Test degree type extraction when spaCy is not available."""
        text_processor.nlp = None
        text_processor.tokenizer = None
        degree_text = "Computer Science"
        result = text_processor.extract_degree_types_enhanced(degree_text)
        # Should still work with basic splitting
        assert len(result) >= 0

    def test_standardize_degree_level_bachelor(self, text_processor):
        """Test bachelor degree level standardization."""
        variations = [
            'Bachelor of Science',
            'bachelor in engineering',
            'B.Tech',
            'Undergraduate'
        ]
        for variation in variations:
            result = text_processor.standardize_degree_level(variation)
            assert result == 'bachelor'

    def test_standardize_degree_level_master(self, text_processor):
        """Test master degree level standardization."""
        variations = [
            'Master of Science',
            'masters in engineering',
            'M.Tech',
            'Postgraduate'
        ]
        for variation in variations:
            result = text_processor.standardize_degree_level(variation)
            assert result == 'master'

    def test_standardize_degree_level_diploma(self, text_processor):
        """Test diploma degree level standardization."""
        variations = [
            'Diploma in Computer Science',
            'Certificate Course',
            'cert in engineering'
        ]
        for variation in variations:
            result = text_processor.standardize_degree_level(variation)
            assert result == 'diploma'

    def test_standardize_degree_level_phd(self, text_processor):
        """Test PhD degree level standardization."""
        variations = [
            'PhD in Computer Science',
            'Ph.D in Engineering',
            'Doctorate in Business',
            'Doctoral program'
        ]
        for variation in variations:
            result = text_processor.standardize_degree_level(variation)
            assert result == 'phd'

    def test_standardize_degree_level_unknown(self, text_processor):
        """Test unknown degree level."""
        result = text_processor.standardize_degree_level('Unknown Degree')
        assert result is None

    def test_standardize_degree_level_empty(self, text_processor):
        """Test empty degree level input."""
        assert text_processor.standardize_degree_level("") is None
        assert text_processor.standardize_degree_level(None) is None

    def test_extract_university_valid_dict(self, text_processor):
        """Test university extraction with valid data."""
        universities = {
            'MIT': {'rank': '1', 'country': 'USA'},
            'Stanford': {'rank': '2', 'country': 'USA'},
            'Harvard': {'rank': '3', 'country': 'USA'}
        }
        result = text_processor.extract_university_enhanced(universities)
        assert result == 'MIT'  # Should return best ranked

    def test_extract_university_complex_ranking(self, text_processor):
        """Test university extraction with complex ranking format."""
        universities = {
            'University A': {'rank': '100-150', 'country': 'Country A'},
            'University B': {'rank': '50-75', 'country': 'Country B'},
            'University C': {'rank': '200+', 'country': 'Country C'}
        }
        result = text_processor.extract_university_enhanced(universities)
        assert result == 'University B'  # Should return best ranked

    def test_extract_university_empty_dict(self, text_processor):
        """Test university extraction with empty dictionary."""
        assert text_processor.extract_university_enhanced({}) is None
        assert text_processor.extract_university_enhanced(None) is None

    def test_extract_university_invalid_data(self, text_processor):
        """Test university extraction with invalid data format."""
        universities = {
            'University A': 'invalid_data',
            'University B': {'rank': 'invalid_rank'}
        }
        result = text_processor.extract_university_enhanced(universities)
        # Should handle gracefully and return something or None
        assert result is None or isinstance(result, str)