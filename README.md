# Employee Recommendation Knowledge Graph System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced employee recommendation system using semantic embeddings and knowledge graphs to identify suitable candidate substitutions based on skills, education, and experience. The system implements a multi-dimensional similarity approach with dense graph connections for comprehensive coverage.

## Features

- **Semantic Embeddings**: Uses SentenceTransformer models for intelligent skill matching
- **Dense Graph Construction**: Multi-dimensional similarity combining skills, education, experience, and text
- **Complete Coverage**: All employees receive recommendations (100% coverage)
- **REST API**: Flask-based API for real-time recommendations
- **Comprehensive Testing**: Evaluation framework with automated benchmarking
- **Production Ready**: Enhanced model with 80% precision on automated tests

## Architecture

The enhanced system implements a multi-layered approach:

1. **Semantic Skill Analysis**: SentenceTransformer embeddings for skill similarity (40% weight)
2. **Education Matching**: Degree level, field, and university tier comparison (25% weight)
3. **Experience Level**: Automated classification and similarity (20% weight)
4. **Text Similarity**: TF-IDF analysis of combined profile text (15% weight)

The system creates a dense similarity matrix ensuring all employees have meaningful connections.

## Prerequisites

- Python 3.8 or higher
- Required Python packages (see requirements.txt)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Employee_Recommendation_Knowledge_Graph
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Generate the enhanced model**:
   ```bash
   python enhanced_kg_model.py
   ```

## Usage

### Running the Application

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Access the API**:
   - Home page: `http://localhost:5000`
   - API endpoint: `POST http://localhost:5000/results`

### API Usage

**Request**:
```bash
curl -X POST http://localhost:5000/results \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "candidate_id=1315"
```

**Response**:
```json
{
  "candidate_id": "1315",
  "similar_candidates": ["751", "1884", "24"],
  "count": 3
}
```

### Model Training

The enhanced model uses semantic embeddings and can be generated with:

```bash
python enhanced_kg_model.py
```

This will:
1. Process resume data from `Filtered01.json`
2. Create semantic skill embeddings using SentenceTransformer
3. Build dense similarity matrix with multi-dimensional features
4. Save the enhanced model to `models/enhanced_kg_model.pkl`

## Testing

### Enhanced Model Evaluation

Test the enhanced semantic model:

```bash
python test_enhanced_model.py
```

### Benchmark Comparison

Compare against baseline methods:

```bash
python evaluation/benchmark.py
```

### Unit Tests

Run the test suite:

```bash
pytest tests/ -v
```

## Model Performance

The enhanced model demonstrates significant improvements:

### Performance Metrics
- **Coverage**: 100% (all employees get recommendations)
- **Mean Similarity**: 0.551 (vs 0.100 original)
- **Manual Test Precision**: 33.3%
- **Automated Test Precision**: 80.0%
- **Hit Rate@3**: 100%

### Comparison with Original
- Enhanced model: 80% precision on automated tests
- Original model: 0% precision on automated tests
- Complete coverage vs 56% original coverage
- Dense similarity matrix vs sparse original

## Configuration

Environment-based configuration:

```python
# config.py
class Config:
    MODEL_PATH = os.environ.get('MODEL_PATH', 'models/enhanced_kg_model.pkl')
    MAX_RECOMMENDATIONS = int(os.environ.get('MAX_RECOMMENDATIONS', '3'))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
```

## Project Structure

```
Employee_Recommendation_Knowledge_Graph/
├── app.py                      # Flask application
├── enhanced_kg_model.py        # Enhanced semantic model
├── test_enhanced_model.py      # Enhanced model evaluation
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── Filtered01.json            # Training data
├── evaluation/
│   ├── metrics.py             # Evaluation framework
│   ├── benchmark.py           # Baseline comparisons
│   └── test_accuracy.py       # Accuracy testing
├── utils/
│   ├── text_processing.py     # Text processing utilities
│   └── logging_config.py      # Logging configuration
├── tests/                     # Unit tests
└── models/                    # Trained models directory
```

## Production Deployment

For production deployment:

1. **Use Gunicorn**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

2. **Set production environment**:
   ```bash
   export FLASK_ENV=production
   export LOG_LEVEL=WARNING
   ```

## Performance Optimization

- **Caching**: Implement Redis for similarity score caching
- **Async Processing**: Use Celery for background similarity computation
- **Database**: Move from pickle to proper database storage
- **Weight Tuning**: Adjust similarity weights based on domain requirements

## Troubleshooting

**Common Issues**:

1. **Model file not found**:
   - Run `python enhanced_kg_model.py` to generate the enhanced model
   - Check MODEL_PATH configuration

2. **Memory issues with large datasets**:
   - Implement batch processing for similarity computation
   - Use streaming for large-scale deployments

3. **Low recommendation quality**:
   - Adjust similarity weights in enhanced_kg_model.py
   - Retrain with more comprehensive skill mappings

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Run tests: `pytest tests/ -v`
4. Commit changes: `git commit -am 'Add feature'`
5. Push to branch: `git push origin feature-name`
6. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:
- Create an issue on GitHub
- Check the troubleshooting section
- Review evaluation reports in the evaluation/ directory 
