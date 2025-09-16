from flask import Flask, request, jsonify, render_template
import pickle
import os
import logging
from heapq import nlargest
from typing import Union, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load enhanced model with proper error handling
enhanced_model_path = os.path.join(os.path.dirname(__file__), 'models', 'enhanced_kg_model.pkl')
legacy_model_path = os.path.join(os.path.dirname(__file__), 'models', 'sim_final.pkl')

try:
    # Try to load enhanced model first
    if os.path.exists(enhanced_model_path):
        with open(enhanced_model_path, 'rb') as f:
            model_data = pickle.load(f)
        model = model_data.get('similarity_matrix', {})
        employee_profiles = model_data.get('employee_profiles', {})
        logger.info(f"Enhanced model loaded successfully from {enhanced_model_path}")
    # Fallback to legacy model
    elif os.path.exists(legacy_model_path):
        model = pickle.load(open(legacy_model_path, 'rb'))
        employee_profiles = {}
        logger.info(f"Legacy model loaded from {legacy_model_path}")
    else:
        logger.error("No model file found. Please run 'python enhanced_kg_model.py' to generate the model.")
        model = None
        employee_profiles = {}
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    model = None
    employee_profiles = {}
#df    = pickle.load(open('C:/Users/saurabh/Desktop/model_KG/df_final.pkl','rb'))
#df = pd.read_pickle('C:/Users/saurabh/Desktop/model_KG/df_final.pkl')
#df = df.filter(['Details'])
#dataframe= pd.read_json("Filtered01.json")
#df = pd.read_json(dataframe['structuredLayout'].to_json(), orient="index")
#df['Details']=df.Details.astype(str)

def find_similarity_final(key: Union[str, int]) -> Union[List[str], str]:
    """
    Find similar candidates for a given candidate ID.

    Args:
        key: Candidate ID to find similarities for

    Returns:
        List of top 3 similar candidate IDs or error message
    """
    if model is None:
        logger.error("Model not loaded. Cannot compute similarity.")
        return "Model not available"

    key = str(key).strip()

    if not key:
        logger.warning("Empty key provided to find_similarity_final")
        return "Invalid candidate ID"

    try:
        if key in model:
            top_candidates = nlargest(4, model.get(key), key=model.get(key).__getitem__)
            # Return top 3 excluding self (first element)
            similar_candidates = top_candidates[1:] if len(top_candidates) > 1 else []
            logger.info(f"Found {len(similar_candidates)} similar candidates for ID {key}")
            return similar_candidates
        else:
            logger.warning(f"Candidate ID {key} not found in model")
            return f"Candidate ID {key} not found"
    except Exception as e:
        logger.error(f"Error computing similarity for key {key}: {str(e)}")
        return "Error computing similarity"



@app.route('/')
def home():
    """
    Home page with enhanced frontend interface.
    """
    if model is None:
        status = "Model Not Loaded"
        employee_count = 0
    else:
        status = "Online"
        employee_count = len(model)

    return render_template('index.html',
                         status=status,
                         employee_count=employee_count)

@app.route('/faq')
def faq():
    """
    FAQ page with comprehensive information about the system.
    """
    return render_template('faq.html')
    


@app.route('/results', methods=['POST'])
def results():
    """
    API endpoint to get candidate recommendations.

    Expects form data with 'candidate_id' field.
    Returns JSON response with similar candidates or error message.
    """
    try:
        # Validate request method
        if request.method != 'POST':
            return jsonify({'error': 'Only POST method allowed'}), 405

        # Get candidate ID from form data
        candidate_id = request.form.get('candidate_id')

        if not candidate_id:
            logger.warning("No candidate_id provided in request")
            return jsonify({'error': 'candidate_id is required'}), 400

        # Validate candidate ID format
        try:
            # Try to convert to int to validate format
            candidate_id_int = int(candidate_id)
            if candidate_id_int <= 0:
                raise ValueError("Candidate ID must be positive")
        except ValueError as e:
            logger.warning(f"Invalid candidate ID format: {candidate_id}")
            return jsonify({'error': 'candidate_id must be a positive integer'}), 400

        # Generate recommendations
        logger.info(f"Processing recommendation request for candidate ID: {candidate_id}")
        recommended_candidates = find_similarity_final(candidate_id)

        # Handle different response types
        if isinstance(recommended_candidates, list):
            response = {
                'candidate_id': candidate_id,
                'similar_candidates': recommended_candidates,
                'count': len(recommended_candidates)
            }
            logger.info(f"Successfully returned {len(recommended_candidates)} recommendations")
            return jsonify(response), 200
        else:
            # Error message returned from find_similarity_final
            logger.warning(f"Recommendation failed for ID {candidate_id}: {recommended_candidates}")
            return jsonify({'error': recommended_candidates}), 404

    except Exception as e:
        logger.error(f"Unexpected error in results endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/employee/<employee_id>')
def get_employee_details(employee_id):
    """
    Get detailed information about a specific employee.
    """
    try:
        if employee_id in employee_profiles:
            profile = employee_profiles[employee_id]
            return jsonify({
                'employee_id': employee_id,
                'skills': profile.get('skills', [])[:10],  # Limit to top 10 skills
                'education': f"{profile.get('education_level', 'Unknown')} in {profile.get('education_field', 'Unknown')}",
                'experience': profile.get('experience_level', 'Unknown'),
                'university_tier': profile.get('university_tier', 'Unknown')
            })
        else:
            return jsonify({'error': 'Employee not found'}), 404
    except Exception as e:
        logger.error(f"Error fetching employee details for {employee_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/graph/<employee_id>')
def get_graph_data(employee_id):
    """
    Get knowledge graph data for visualization.
    """
    try:
        depth = int(request.args.get('depth', 2))

        if employee_id not in model:
            return jsonify({'error': 'Employee not found'}), 404

        # Build graph data for visualization
        graph_data = build_graph_visualization_data(employee_id, depth)

        return jsonify(graph_data)

    except Exception as e:
        logger.error(f"Error generating graph data for {employee_id}: {str(e)}")
        return jsonify({'error': 'Failed to generate graph data'}), 500

def build_graph_visualization_data(employee_id, depth=2):
    """
    Build graph data structure for D3.js/Cytoscape visualization.
    """
    nodes = []
    edges = []
    visited_employees = set()
    visited_skills = set()

    # Add main employee node
    main_profile = employee_profiles.get(employee_id, {})
    nodes.append({
        'data': {
            'id': employee_id,
            'label': f"Employee {employee_id}",
            'type': 'employee',
            'score': 100,
            'skills': main_profile.get('skills', [])[:5],
            'education': main_profile.get('education_level', 'Unknown'),
            'experience': main_profile.get('experience_level', 'Unknown')
        }
    })
    visited_employees.add(employee_id)

    # Get top similar employees
    if employee_id in model:
        similarities = model[employee_id]
        top_similar = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:8]

        for similar_emp, similarity in top_similar:
            if similar_emp != employee_id and similarity > 0.3:  # Threshold for visualization

                # Add similar employee node
                similar_profile = employee_profiles.get(similar_emp, {})
                nodes.append({
                    'data': {
                        'id': similar_emp,
                        'label': f"Employee {similar_emp}",
                        'type': 'employee',
                        'score': int(similarity * 100),
                        'skills': similar_profile.get('skills', [])[:3],
                        'education': similar_profile.get('education_level', 'Unknown'),
                        'experience': similar_profile.get('experience_level', 'Unknown')
                    }
                })
                visited_employees.add(similar_emp)

                # Add edge between employees
                edges.append({
                    'data': {
                        'id': f"{employee_id}-{similar_emp}",
                        'source': employee_id,
                        'target': similar_emp,
                        'similarity': similarity,
                        'type': 'similarity'
                    }
                })

    # Add skill nodes and connections
    all_employee_ids = list(visited_employees)
    for emp_id in all_employee_ids:
        profile = employee_profiles.get(emp_id, {})
        skills = profile.get('skills', [])[:5]  # Limit skills to prevent overcrowding

        for skill in skills:
            skill_id = f"skill_{skill.replace(' ', '_').lower()}"

            # Add skill node if not already added
            if skill_id not in visited_skills:
                nodes.append({
                    'data': {
                        'id': skill_id,
                        'label': skill.title(),
                        'type': 'skill',
                        'score': 75
                    }
                })
                visited_skills.add(skill_id)

            # Add edge from employee to skill
            edges.append({
                'data': {
                    'id': f"{emp_id}-{skill_id}",
                    'source': emp_id,
                    'target': skill_id,
                    'similarity': 0.8,
                    'type': 'has_skill'
                }
            })

    # Add education and experience nodes for main employee
    if main_profile:
        education = main_profile.get('education_level')
        experience = main_profile.get('experience_level')

        if education and education != 'unknown':
            edu_id = f"education_{education}"
            nodes.append({
                'data': {
                    'id': edu_id,
                    'label': education.title(),
                    'type': 'education',
                    'score': 60
                }
            })
            edges.append({
                'data': {
                    'id': f"{employee_id}-{edu_id}",
                    'source': employee_id,
                    'target': edu_id,
                    'similarity': 0.9,
                    'type': 'has_education'
                }
            })

        if experience and experience != 'unknown':
            exp_id = f"experience_{experience}"
            nodes.append({
                'data': {
                    'id': exp_id,
                    'label': f"{experience.title()} Level",
                    'type': 'experience',
                    'score': 50
                }
            })
            edges.append({
                'data': {
                    'id': f"{employee_id}-{exp_id}",
                    'source': employee_id,
                    'target': exp_id,
                    'similarity': 0.7,
                    'type': 'has_experience'
                }
            })

    return {
        'elements': nodes + edges,
        'stats': {
            'nodes': len(nodes),
            'edges': len(edges),
            'employees': len(visited_employees),
            'skills': len(visited_skills)
        }
    }

@app.route('/api/status')
def api_status():
    """
    API status endpoint for monitoring.
    """
    if model is None:
        status = "ERROR: Model not loaded"
        employee_count = 0
    else:
        status = "OK"
        employee_count = len(model)

    return jsonify({
        'service': 'Employee Recommendation API',
        'status': status,
        'model_type': 'Enhanced Knowledge Graph with Semantic Embeddings',
        'employee_count': employee_count,
        'endpoints': {
            'home': 'GET /',
            'recommendations': 'POST /results',
            'employee_details': 'GET /employee/<id>',
            'graph_data': 'GET /api/graph/<id>',
            'status': 'GET /api/status'
        }
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    if model is None:
        logger.error("Cannot start application: Model not loaded")
        exit(1)

    logger.info("Starting Employee Recommendation API server...")
    app.run(debug=True, host='0.0.0.0', port=5000)




