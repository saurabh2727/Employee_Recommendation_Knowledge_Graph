"""
Unit tests for the Flask application.
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from app import app, find_similarity_final

@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_model():
    """Create mock model for testing."""
    return {
        '123': {'456': 0.9, '789': 0.8, '321': 0.7, '123': 1.0},
        '456': {'123': 0.9, '789': 0.6, '456': 1.0}
    }

class TestFlaskApp:
    """Test cases for Flask application."""

    def test_home_route(self, client):
        """Test home page route."""
        response = client.get('/')
        assert response.status_code == 200

    def test_results_get_method_not_allowed(self, client):
        """Test that GET method is not allowed for results endpoint."""
        response = client.get('/results')
        assert response.status_code == 405
        data = json.loads(response.data)
        assert 'error' in data

    def test_results_missing_candidate_id(self, client):
        """Test results endpoint with missing candidate_id."""
        response = client.post('/results', data={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'candidate_id is required'

    def test_results_invalid_candidate_id_format(self, client):
        """Test results endpoint with invalid candidate_id format."""
        response = client.post('/results', data={'candidate_id': 'abc'})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'positive integer' in data['error']

    def test_results_negative_candidate_id(self, client):
        """Test results endpoint with negative candidate_id."""
        response = client.post('/results', data={'candidate_id': '-1'})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'positive integer' in data['error']

    @patch('app.model')
    def test_results_success(self, mock_model_patch, client):
        """Test successful recommendation request."""
        mock_model_patch.__contains__ = lambda self, key: key == '123'
        mock_model_patch.get = lambda key: {'456': 0.9, '789': 0.8, '321': 0.7, '123': 1.0}

        response = client.post('/results', data={'candidate_id': '123'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['candidate_id'] == '123'
        assert 'similar_candidates' in data
        assert 'count' in data
        assert len(data['similar_candidates']) <= 3

    @patch('app.model')
    def test_results_candidate_not_found(self, mock_model_patch, client):
        """Test request for non-existent candidate."""
        mock_model_patch.__contains__ = lambda self, key: False

        response = client.post('/results', data={'candidate_id': '999'})
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['error']

    @patch('app.model', None)
    def test_results_model_not_loaded(self, client):
        """Test behavior when model is not loaded."""
        response = client.post('/results', data={'candidate_id': '123'})
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'Model not available' in data['error']

class TestSimilarityFunction:
    """Test cases for similarity function."""

    def test_find_similarity_model_none(self):
        """Test similarity function when model is None."""
        with patch('app.model', None):
            result = find_similarity_final('123')
            assert result == "Model not available"

    def test_find_similarity_empty_key(self):
        """Test similarity function with empty key."""
        with patch('app.model', {}):
            result = find_similarity_final('')
            assert result == "Invalid candidate ID"

    def test_find_similarity_key_not_found(self):
        """Test similarity function with non-existent key."""
        mock_model = {'456': {'789': 0.8}}
        with patch('app.model', mock_model):
            result = find_similarity_final('123')
            assert 'not found' in result

    def test_find_similarity_success(self):
        """Test successful similarity computation."""
        mock_model = {
            '123': {'456': 0.9, '789': 0.8, '321': 0.7, '123': 1.0}
        }
        with patch('app.model', mock_model):
            result = find_similarity_final('123')
            assert isinstance(result, list)
            assert len(result) <= 3
            assert '123' not in result  # Should not include self

    def test_find_similarity_exception_handling(self):
        """Test similarity function exception handling."""
        mock_model = MagicMock()
        mock_model.__contains__ = lambda key: True
        mock_model.get.side_effect = Exception("Test exception")

        with patch('app.model', mock_model):
            result = find_similarity_final('123')
            assert "Error computing similarity" in result

    def test_find_similarity_string_conversion(self):
        """Test that integer keys are converted to strings."""
        mock_model = {
            '123': {'456': 0.9, '789': 0.8, '123': 1.0}
        }
        with patch('app.model', mock_model):
            result = find_similarity_final(123)  # Pass as integer
            assert isinstance(result, list)