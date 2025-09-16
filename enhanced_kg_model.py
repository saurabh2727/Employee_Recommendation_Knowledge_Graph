"""
Enhanced Knowledge Graph Model with Semantic Embeddings and Dense Connections.

This redesigned approach addresses the key issues:
1. Uses semantic embeddings for skill similarity
2. Creates dense graph connections
3. Implements weighted multi-dimensional similarity
4. Ensures all employees get recommendations
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
import networkx as nx
import re
from typing import Dict, List, Tuple, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sentence_transformers import SentenceTransformer
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticSkillEmbedder:
    """Create semantic embeddings for skills using pre-trained models."""

    def __init__(self):
        """Initialize with sentence transformer model."""
        try:
            # Use a lightweight pre-trained model for semantic embeddings
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded SentenceTransformer model successfully")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer: {e}")
            logger.info("Falling back to TF-IDF embeddings")
            self.model = None
            self.vectorizer = TfidfVectorizer(max_features=200, stop_words='english')

    def create_skill_embeddings(self, all_skills: List[str]) -> Dict[str, np.ndarray]:
        """Create embeddings for all unique skills."""
        unique_skills = list(set(all_skills))
        logger.info(f"Creating embeddings for {len(unique_skills)} unique skills")

        if self.model:
            # Use SentenceTransformer for semantic embeddings
            embeddings = self.model.encode(unique_skills)
            return {skill: emb for skill, emb in zip(unique_skills, embeddings)}
        else:
            # Fallback to TF-IDF
            skill_matrix = self.vectorizer.fit_transform(unique_skills)
            return {skill: emb.toarray().flatten()
                   for skill, emb in zip(unique_skills, skill_matrix)}

class EnhancedKnowledgeGraph:
    """Enhanced Knowledge Graph with semantic embeddings and dense connections."""

    def __init__(self):
        """Initialize the enhanced knowledge graph."""
        self.skill_embedder = SemanticSkillEmbedder()
        self.skill_embeddings = {}
        self.employee_profiles = {}
        self.similarity_matrix = {}

    def process_employee_data(self, data_file: str) -> pd.DataFrame:
        """Process employee data with enhanced feature extraction."""
        logger.info(f"Processing employee data from {data_file}")

        with open(data_file, 'r') as f:
            raw_data = json.load(f)

        employees = []
        all_skills = []

        for idx, record in enumerate(raw_data):
            # Extract basic info
            details = record.get('structuredLayout', {})
            emp_id = str(details.get('Details', ''))

            if not emp_id:
                continue

            # Enhanced skill extraction
            raw_skills = record.get('skillsCluster', [])

            # Clean and expand skills
            cleaned_skills = self._clean_and_expand_skills(raw_skills)

            if not cleaned_skills:  # Skip employees with no skills
                continue

            all_skills.extend(cleaned_skills)

            # Enhanced education processing
            education = self._process_education_enhanced(record.get('degrees', []),
                                                       record.get('universties', {}))

            # Experience level estimation
            experience_level = self._estimate_experience_level(details.get('Experience', ''))

            employee_profile = {
                'emp_id': emp_id,
                'skills': cleaned_skills,
                'education_level': education.get('level', 'unknown'),
                'education_field': education.get('field', 'unknown'),
                'university_tier': education.get('university_tier', 'unknown'),
                'experience_level': experience_level,
                'raw_text': self._create_text_representation(details, cleaned_skills, education)
            }

            employees.append(employee_profile)
            self.employee_profiles[emp_id] = employee_profile

        logger.info(f"Processed {len(employees)} employees with valid skill data")

        # Create skill embeddings
        self.skill_embeddings = self.skill_embedder.create_skill_embeddings(all_skills)

        return pd.DataFrame(employees)

    def _clean_and_expand_skills(self, raw_skills: List[str]) -> List[str]:
        """Clean skills and add semantic variations."""
        if not raw_skills:
            return []

        cleaned = []

        # Skill expansion mapping for better coverage
        skill_expansions = {
            'python': ['python', 'python programming', 'python development'],
            'javascript': ['javascript', 'js', 'javascript programming'],
            'machine learning': ['machine learning', 'ml', 'artificial intelligence', 'ai'],
            'data science': ['data science', 'data analysis', 'analytics'],
            'web development': ['web development', 'web programming', 'frontend', 'backend'],
            'sql': ['sql', 'database', 'mysql', 'postgresql'],
            'java': ['java', 'java programming', 'java development'],
            'react': ['react', 'reactjs', 'react.js'],
            'node': ['node', 'nodejs', 'node.js'],
            'aws': ['aws', 'amazon web services', 'cloud computing']
        }

        for skill in raw_skills:
            if not skill or len(skill.strip()) < 2:
                continue

            skill_clean = skill.lower().strip()
            cleaned.append(skill_clean)

            # Add expansions if available
            for base_skill, expansions in skill_expansions.items():
                if base_skill in skill_clean:
                    cleaned.extend(expansions)

        return list(set(cleaned))  # Remove duplicates

    def _process_education_enhanced(self, degrees: List, universities: Dict) -> Dict:
        """Enhanced education processing with tier classification."""
        education = {'level': 'unknown', 'field': 'unknown', 'university_tier': 'unknown'}

        # Process degree level
        if degrees:
            for level, field in degrees:
                level_str = str(level).lower()
                if 'phd' in level_str or 'doctorate' in level_str:
                    education['level'] = 'phd'
                elif 'master' in level_str or 'mba' in level_str:
                    education['level'] = 'master'
                elif 'bachelor' in level_str:
                    education['level'] = 'bachelor'
                elif 'diploma' in level_str:
                    education['level'] = 'diploma'

                # Process field
                field_str = str(field).lower()
                education['field'] = self._standardize_education_field(field_str)
                break

        # Process university tier
        if universities:
            uni_name = list(universities.keys())[0]
            uni_data = universities[uni_name]

            # Simple tier classification based on ranking
            if isinstance(uni_data, dict) and 'rank' in uni_data:
                rank_str = str(uni_data['rank'])
                try:
                    rank_num = int(re.search(r'\d+', rank_str).group())
                    if rank_num <= 50:
                        education['university_tier'] = 'tier1'
                    elif rank_num <= 200:
                        education['university_tier'] = 'tier2'
                    else:
                        education['university_tier'] = 'tier3'
                except:
                    education['university_tier'] = 'unknown'

        return education

    def _standardize_education_field(self, field: str) -> str:
        """Standardize education field to common categories."""
        field_mapping = {
            'computer': 'computer_science',
            'engineering': 'engineering',
            'business': 'business',
            'science': 'science',
            'management': 'management',
            'data': 'data_science',
            'mathematics': 'mathematics',
            'economics': 'economics',
            'design': 'design'
        }

        for key, value in field_mapping.items():
            if key in field:
                return value
        return 'other'

    def _estimate_experience_level(self, experience_text: str) -> str:
        """Estimate experience level from text."""
        if not experience_text:
            return 'unknown'

        exp_text = experience_text.lower()

        # Simple heuristics for experience level
        if any(word in exp_text for word in ['senior', 'lead', 'principal', 'architect', 'manager']):
            return 'senior'
        elif any(word in exp_text for word in ['junior', 'entry', 'intern', 'trainee', 'graduate']):
            return 'junior'
        else:
            return 'mid'

    def _create_text_representation(self, details: Dict, skills: List[str], education: Dict) -> str:
        """Create comprehensive text representation for TF-IDF fallback."""
        text_parts = []

        # Add skills
        text_parts.extend(skills)

        # Add education info
        text_parts.append(education.get('level', ''))
        text_parts.append(education.get('field', ''))

        # Add experience if available
        if 'Experience' in details:
            exp_words = str(details['Experience']).lower().split()[:50]  # First 50 words
            text_parts.extend(exp_words)

        return ' '.join(filter(None, text_parts))

    def build_dense_similarity_matrix(self, employees_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Build dense similarity matrix using multiple dimensions."""
        logger.info("Building dense similarity matrix...")

        emp_ids = employees_df['emp_id'].tolist()
        n_employees = len(emp_ids)

        # Initialize similarity matrix
        similarity_matrix = {emp_id: {} for emp_id in emp_ids}

        # Calculate multi-dimensional similarities
        for i, emp1_id in enumerate(emp_ids):
            for j, emp2_id in enumerate(emp_ids):
                if i == j:
                    similarity_matrix[emp1_id][emp2_id] = 1.0
                else:
                    similarity = self._calculate_multi_dimensional_similarity(
                        self.employee_profiles[emp1_id],
                        self.employee_profiles[emp2_id]
                    )
                    similarity_matrix[emp1_id][emp2_id] = similarity

        logger.info(f"Built similarity matrix for {n_employees} employees")
        return similarity_matrix

    def _calculate_multi_dimensional_similarity(self, emp1: Dict, emp2: Dict) -> float:
        """Calculate similarity across multiple dimensions."""

        # 1. Semantic skill similarity (40% weight)
        skill_sim = self._calculate_semantic_skill_similarity(emp1['skills'], emp2['skills'])

        # 2. Education similarity (25% weight)
        edu_sim = self._calculate_education_similarity(emp1, emp2)

        # 3. Experience level similarity (20% weight)
        exp_sim = self._calculate_experience_similarity(emp1['experience_level'], emp2['experience_level'])

        # 4. Text similarity fallback (15% weight)
        text_sim = self._calculate_text_similarity(emp1['raw_text'], emp2['raw_text'])

        # Weighted combination
        total_similarity = (
            0.40 * skill_sim +
            0.25 * edu_sim +
            0.20 * exp_sim +
            0.15 * text_sim
        )

        return total_similarity

    def _calculate_semantic_skill_similarity(self, skills1: List[str], skills2: List[str]) -> float:
        """Calculate semantic similarity between skill sets."""
        if not skills1 or not skills2:
            return 0.0

        # Get embeddings for skills
        emb1 = [self.skill_embeddings.get(skill, np.zeros(384)) for skill in skills1
                if skill in self.skill_embeddings]
        emb2 = [self.skill_embeddings.get(skill, np.zeros(384)) for skill in skills2
                if skill in self.skill_embeddings]

        if not emb1 or not emb2:
            # Fallback to Jaccard similarity
            set1, set2 = set(skills1), set(skills2)
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            return intersection / union if union > 0 else 0.0

        # Calculate average embeddings
        avg_emb1 = np.mean(emb1, axis=0)
        avg_emb2 = np.mean(emb2, axis=0)

        # Cosine similarity
        similarity = np.dot(avg_emb1, avg_emb2) / (np.linalg.norm(avg_emb1) * np.linalg.norm(avg_emb2))

        # Ensure similarity is between 0 and 1
        return max(0.0, min(1.0, (similarity + 1) / 2))

    def _calculate_education_similarity(self, emp1: Dict, emp2: Dict) -> float:
        """Calculate education similarity."""
        level_sim = 1.0 if emp1['education_level'] == emp2['education_level'] else 0.0
        field_sim = 1.0 if emp1['education_field'] == emp2['education_field'] else 0.0
        tier_sim = 1.0 if emp1['university_tier'] == emp2['university_tier'] else 0.0

        return 0.5 * level_sim + 0.3 * field_sim + 0.2 * tier_sim

    def _calculate_experience_similarity(self, exp1: str, exp2: str) -> float:
        """Calculate experience level similarity."""
        if exp1 == exp2:
            return 1.0
        elif (exp1 in ['junior', 'mid'] and exp2 in ['junior', 'mid']) or \
             (exp1 in ['mid', 'senior'] and exp2 in ['mid', 'senior']):
            return 0.7
        else:
            return 0.3

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using TF-IDF."""
        if not text1 or not text2:
            return 0.0

        try:
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return max(0.0, similarity)
        except:
            return 0.0

    def get_recommendations(self, employee_id: str, k: int = 3, min_similarity: float = 0.1) -> List[Tuple[str, float]]:
        """Get top-k recommendations for an employee."""
        if employee_id not in self.similarity_matrix:
            return []

        similarities = self.similarity_matrix[employee_id]

        # Filter by minimum similarity and exclude self
        candidates = [(emp_id, sim) for emp_id, sim in similarities.items()
                     if emp_id != employee_id and sim >= min_similarity]

        # Sort by similarity descending
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates[:k]

def main():
    """Main function to build and test enhanced knowledge graph."""
    logger.info("Building Enhanced Knowledge Graph with Semantic Embeddings...")

    # Initialize enhanced knowledge graph
    kg = EnhancedKnowledgeGraph()

    # Process employee data
    employees_df = kg.process_employee_data('Filtered01.json')

    # Build dense similarity matrix
    similarity_matrix = kg.build_dense_similarity_matrix(employees_df)
    kg.similarity_matrix = similarity_matrix

    # Save enhanced model
    os.makedirs('models', exist_ok=True)

    with open('models/enhanced_kg_model.pkl', 'wb') as f:
        pickle.dump({
            'similarity_matrix': similarity_matrix,
            'employee_profiles': kg.employee_profiles,
            'skill_embeddings': kg.skill_embeddings
        }, f)

    logger.info("Enhanced model saved to models/enhanced_kg_model.pkl")

    # Test the model
    logger.info("\nTesting Enhanced Model:")
    logger.info("=" * 50)

    # Test coverage
    total_employees = len(employees_df)
    employees_with_recs = 0

    for emp_id in employees_df['emp_id'][:5]:  # Test first 5
        recommendations = kg.get_recommendations(emp_id, k=3, min_similarity=0.1)

        if recommendations:
            employees_with_recs += 1

        logger.info(f"\nEmployee {emp_id}:")
        logger.info(f"  Skills: {kg.employee_profiles[emp_id]['skills'][:5]}...")
        logger.info(f"  Education: {kg.employee_profiles[emp_id]['education_level']} in {kg.employee_profiles[emp_id]['education_field']}")
        logger.info(f"  Recommendations: {[(emp, f'{sim:.3f}') for emp, sim in recommendations]}")

    # Calculate overall statistics
    all_similarities = []
    non_zero_count = 0

    for emp_sims in similarity_matrix.values():
        for other_emp, sim in emp_sims.items():
            all_similarities.append(sim)
            if sim > 0.1:  # Count meaningful similarities
                non_zero_count += 1

    logger.info(f"\nModel Statistics:")
    logger.info(f"  Total employees: {total_employees}")
    logger.info(f"  Mean similarity: {np.mean(all_similarities):.3f}")
    logger.info(f"  Similarities > 0.1: {non_zero_count} ({non_zero_count/len(all_similarities)*100:.1f}%)")
    logger.info(f"  Coverage: All employees should have recommendations with min_similarity=0.1")

    print("Enhanced Knowledge Graph model built successfully!")
    print("Model saved to models/enhanced_kg_model.pkl")
    print("Ready for evaluation testing")

if __name__ == "__main__":
    main()