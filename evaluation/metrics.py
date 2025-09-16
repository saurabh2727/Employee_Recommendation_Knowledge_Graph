"""
Evaluation metrics for employee substitution recommendation system.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
import json
import logging
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.model_selection import KFold
import networkx as nx

logger = logging.getLogger(__name__)

class RecommendationEvaluator:
    """Comprehensive evaluation framework for recommendation accuracy."""

    def __init__(self, similarity_model: Dict, candidate_data: pd.DataFrame):
        """
        Initialize evaluator with model and data.

        Args:
            similarity_model: Trained similarity model (SimRank results)
            candidate_data: DataFrame with candidate information
        """
        self.similarity_model = similarity_model
        self.candidate_data = candidate_data
        self.evaluation_results = {}

    def evaluate_substitution_accuracy(
        self,
        test_pairs: List[Tuple[str, List[str]]],
        k: int = 3
    ) -> Dict[str, float]:
        """
        Evaluate accuracy using known good substitution pairs.

        Args:
            test_pairs: List of (employee_id, [good_substitutes]) pairs
            k: Number of recommendations to evaluate

        Returns:
            Dictionary with accuracy metrics
        """
        logger.info(f"Evaluating substitution accuracy for {len(test_pairs)} test pairs")

        hits_at_k = []
        precision_at_k = []
        recall_at_k = []

        for employee_id, true_substitutes in test_pairs:
            # Get model recommendations
            recommendations = self._get_recommendations(employee_id, k)

            if not recommendations:
                logger.warning(f"No recommendations found for employee {employee_id}")
                hits_at_k.append(0)
                precision_at_k.append(0)
                recall_at_k.append(0)
                continue

            # Calculate metrics
            recommended_set = set(recommendations)
            true_set = set(true_substitutes)

            # Hit@K: At least one correct recommendation
            hit = len(recommended_set & true_set) > 0
            hits_at_k.append(int(hit))

            # Precision@K: Fraction of recommendations that are correct
            precision = len(recommended_set & true_set) / len(recommended_set)
            precision_at_k.append(precision)

            # Recall@K: Fraction of correct substitutes that were recommended
            recall = len(recommended_set & true_set) / len(true_set) if true_set else 0
            recall_at_k.append(recall)

        results = {
            f'hit_rate@{k}': np.mean(hits_at_k),
            f'precision@{k}': np.mean(precision_at_k),
            f'recall@{k}': np.mean(recall_at_k),
            f'f1_score@{k}': 2 * np.mean(precision_at_k) * np.mean(recall_at_k) /
                           (np.mean(precision_at_k) + np.mean(recall_at_k))
                           if (np.mean(precision_at_k) + np.mean(recall_at_k)) > 0 else 0
        }

        self.evaluation_results.update(results)
        return results

    def skill_overlap_analysis(self, employee_id: str, recommendations: List[str]) -> Dict[str, float]:
        """
        Analyze skill overlap between employee and recommendations.

        Args:
            employee_id: Target employee ID
            recommendations: List of recommended substitute IDs

        Returns:
            Skill overlap metrics
        """
        target_skills = self._get_employee_skills(employee_id)
        if not target_skills:
            return {'avg_skill_overlap': 0.0, 'max_skill_overlap': 0.0}

        overlaps = []
        for rec_id in recommendations:
            rec_skills = self._get_employee_skills(rec_id)
            if rec_skills:
                overlap = len(set(target_skills) & set(rec_skills)) / len(set(target_skills) | set(rec_skills))
                overlaps.append(overlap)

        return {
            'avg_skill_overlap': np.mean(overlaps) if overlaps else 0.0,
            'max_skill_overlap': np.max(overlaps) if overlaps else 0.0,
            'min_skill_overlap': np.min(overlaps) if overlaps else 0.0,
            'std_skill_overlap': np.std(overlaps) if overlaps else 0.0
        }

    def education_compatibility_analysis(
        self,
        employee_id: str,
        recommendations: List[str]
    ) -> Dict[str, float]:
        """
        Analyze education compatibility between employee and recommendations.

        Args:
            employee_id: Target employee ID
            recommendations: List of recommended substitute IDs

        Returns:
            Education compatibility metrics
        """
        target_edu = self._get_employee_education(employee_id)
        if not target_edu:
            return {'education_match_rate': 0.0}

        matches = []
        for rec_id in recommendations:
            rec_edu = self._get_employee_education(rec_id)
            if rec_edu:
                # Check degree level match
                level_match = target_edu.get('level') == rec_edu.get('level')
                # Check degree type similarity
                target_types = set(target_edu.get('types', []))
                rec_types = set(rec_edu.get('types', []))
                type_overlap = len(target_types & rec_types) / len(target_types | rec_types) if target_types | rec_types else 0

                # Combined education score
                edu_score = 0.6 * level_match + 0.4 * type_overlap
                matches.append(edu_score)

        return {
            'avg_education_match': np.mean(matches) if matches else 0.0,
            'education_match_rate': sum(1 for m in matches if m > 0.5) / len(matches) if matches else 0.0
        }

    def cross_validation_evaluation(self, n_splits: int = 5, k: int = 3) -> Dict[str, List[float]]:
        """
        Perform cross-validation evaluation by hiding employees and testing recommendations.

        Args:
            n_splits: Number of CV folds
            k: Number of recommendations to evaluate

        Returns:
            Cross-validation results
        """
        logger.info(f"Starting {n_splits}-fold cross-validation")

        employee_ids = list(self.similarity_model.keys())
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)

        cv_results = defaultdict(list)

        for fold, (train_idx, test_idx) in enumerate(kf.split(employee_ids)):
            logger.info(f"Processing fold {fold + 1}/{n_splits}")

            test_employees = [employee_ids[i] for i in test_idx]
            fold_metrics = self._evaluate_fold(test_employees, k)

            for metric, value in fold_metrics.items():
                cv_results[metric].append(value)

        # Calculate mean and std for each metric
        cv_summary = {}
        for metric, values in cv_results.items():
            cv_summary[f'{metric}_mean'] = np.mean(values)
            cv_summary[f'{metric}_std'] = np.std(values)

        self.evaluation_results['cross_validation'] = cv_summary
        return cv_results

    def similarity_score_distribution_analysis(self) -> Dict[str, any]:
        """
        Analyze the distribution of similarity scores in the model.

        Returns:
            Statistical summary of similarity scores
        """
        all_scores = []
        for employee_id, similarities in self.similarity_model.items():
            scores = [score for other_id, score in similarities.items() if other_id != employee_id]
            all_scores.extend(scores)

        if not all_scores:
            return {'error': 'No similarity scores found'}

        return {
            'mean_similarity': np.mean(all_scores),
            'median_similarity': np.median(all_scores),
            'std_similarity': np.std(all_scores),
            'min_similarity': np.min(all_scores),
            'max_similarity': np.max(all_scores),
            'score_count': len(all_scores),
            'percentiles': {
                '25th': np.percentile(all_scores, 25),
                '75th': np.percentile(all_scores, 75),
                '90th': np.percentile(all_scores, 90),
                '95th': np.percentile(all_scores, 95)
            }
        }

    def generate_test_pairs_from_clusters(self, min_cluster_size: int = 3) -> List[Tuple[str, List[str]]]:
        """
        Generate test pairs by clustering similar employees based on skills/education.

        Args:
            min_cluster_size: Minimum size for a valid cluster

        Returns:
            List of test pairs for evaluation
        """
        logger.info("Generating test pairs from employee clusters")

        # Group employees by similar profiles
        clusters = defaultdict(list)

        for _, row in self.candidate_data.iterrows():
            employee_id = str(row.get('Details', ''))
            if not employee_id:
                continue

            # Create profile signature
            skills = set(row.get('Skills', []) if isinstance(row.get('Skills'), list) else [])
            education = self._get_employee_education(employee_id)

            # Simple clustering key based on top skills and education level
            top_skills = sorted(list(skills))[:5]  # Top 5 skills
            edu_level = education.get('level', 'unknown') if education else 'unknown'

            cluster_key = f"{edu_level}_{'-'.join(top_skills)}"
            clusters[cluster_key].append(employee_id)

        # Generate test pairs from clusters
        test_pairs = []
        for cluster_key, members in clusters.items():
            if len(members) >= min_cluster_size:
                # For each member, others in cluster are potential good substitutes
                for employee in members:
                    substitutes = [m for m in members if m != employee]
                    test_pairs.append((employee, substitutes))

        logger.info(f"Generated {len(test_pairs)} test pairs from {len(clusters)} clusters")
        return test_pairs

    def _get_recommendations(self, employee_id: str, k: int) -> List[str]:
        """Get top-k recommendations for an employee."""
        if employee_id not in self.similarity_model:
            return []

        similarities = self.similarity_model[employee_id]
        # Sort by similarity score, exclude self
        sorted_sims = sorted(
            [(other_id, score) for other_id, score in similarities.items() if other_id != employee_id],
            key=lambda x: x[1],
            reverse=True
        )

        return [emp_id for emp_id, _ in sorted_sims[:k]]

    def _get_employee_skills(self, employee_id: str) -> List[str]:
        """Get skills for an employee."""
        employee_row = self.candidate_data[self.candidate_data['Details'] == int(employee_id)]
        if employee_row.empty:
            return []

        skills = employee_row.iloc[0].get('Skills', [])
        return skills if isinstance(skills, list) else []

    def _get_employee_education(self, employee_id: str) -> Optional[Dict]:
        """Get education information for an employee."""
        employee_row = self.candidate_data[self.candidate_data['Details'] == int(employee_id)]
        if employee_row.empty:
            return None

        row = employee_row.iloc[0]
        return {
            'level': row.get('Degree_level'),
            'types': row.get('Degree_type', []) if isinstance(row.get('Degree_type'), list) else [row.get('Degree_type')] if row.get('Degree_type') else [],
            'university': row.get('University')
        }

    def _evaluate_fold(self, test_employees: List[str], k: int) -> Dict[str, float]:
        """Evaluate a single fold in cross-validation."""
        hits = []
        precisions = []

        for employee_id in test_employees:
            recommendations = self._get_recommendations(employee_id, k)

            if not recommendations:
                hits.append(0)
                precisions.append(0)
                continue

            # Use skill overlap as ground truth for CV
            skill_metrics = self.skill_overlap_analysis(employee_id, recommendations)

            # Consider it a hit if average skill overlap > threshold
            hit = skill_metrics['avg_skill_overlap'] > 0.3
            hits.append(int(hit))

            # Use skill overlap as precision proxy
            precisions.append(skill_metrics['avg_skill_overlap'])

        return {
            'cv_hit_rate': np.mean(hits),
            'cv_skill_precision': np.mean(precisions)
        }

    def save_evaluation_results(self, filepath: str):
        """Save evaluation results to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.evaluation_results, f, indent=2)
        logger.info(f"Evaluation results saved to {filepath}")

    def plot_similarity_distribution(self, save_path: Optional[str] = None):
        """Plot similarity score distribution."""
        all_scores = []
        for similarities in self.similarity_model.values():
            all_scores.extend(similarities.values())

        plt.figure(figsize=(10, 6))
        plt.hist(all_scores, bins=50, alpha=0.7, edgecolor='black')
        plt.xlabel('Similarity Score')
        plt.ylabel('Frequency')
        plt.title('Distribution of Similarity Scores')
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def plot_evaluation_metrics(self, metrics: Dict[str, float], save_path: Optional[str] = None):
        """Plot evaluation metrics as bar chart."""
        plt.figure(figsize=(12, 6))

        metric_names = list(metrics.keys())
        metric_values = list(metrics.values())

        bars = plt.bar(metric_names, metric_values, alpha=0.7)
        plt.xlabel('Metrics')
        plt.ylabel('Score')
        plt.title('Model Evaluation Metrics')
        plt.xticks(rotation=45)

        # Add value labels on bars
        for bar, value in zip(bars, metric_values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.3f}', ha='center', va='bottom')

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()