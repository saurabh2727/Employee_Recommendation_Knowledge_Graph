"""
Benchmarking script to compare the knowledge graph model against baseline methods.
"""
import os
import sys
import time
import json
import pickle
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.metrics import RecommendationEvaluator
from utils.logging_config import setup_logging

logger = setup_logging(log_level="INFO")

class BaselineModels:
    """Baseline recommendation models for comparison."""

    def __init__(self, candidate_data: pd.DataFrame):
        """Initialize with candidate data."""
        self.candidate_data = candidate_data
        self.models = {}

    def build_tfidf_baseline(self) -> Dict[str, Dict[str, float]]:
        """
        Build TF-IDF based similarity model using skills and education text.

        Returns:
            Similarity matrix as nested dictionary
        """
        logger.info("Building TF-IDF baseline model")

        # Prepare text features
        documents = []
        employee_ids = []

        for _, row in self.candidate_data.iterrows():
            emp_id = str(row.get('Details', ''))
            if not emp_id:
                continue

            # Combine skills and education into text
            skills = row.get('Skills', [])
            skills_text = ' '.join(skills) if isinstance(skills, list) else str(skills)

            education_text = ' '.join([
                str(row.get('Degree_level', '')),
                str(row.get('Degree_type', '')),
                str(row.get('University', ''))
            ])

            combined_text = f"{skills_text} {education_text}".strip()
            if combined_text:
                documents.append(combined_text)
                employee_ids.append(emp_id)

        if not documents:
            logger.error("No documents found for TF-IDF model")
            return {}

        # Build TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        tfidf_matrix = vectorizer.fit_transform(documents)

        # Calculate cosine similarities
        similarity_matrix = cosine_similarity(tfidf_matrix)

        # Convert to nested dictionary format
        similarity_dict = {}
        for i, emp_id in enumerate(employee_ids):
            similarity_dict[emp_id] = {}
            for j, other_id in enumerate(employee_ids):
                similarity_dict[emp_id][other_id] = float(similarity_matrix[i][j])

        logger.info(f"TF-IDF model built for {len(employee_ids)} employees")
        self.models['tfidf'] = similarity_dict
        return similarity_dict

    def build_skills_jaccard_baseline(self) -> Dict[str, Dict[str, float]]:
        """
        Build Jaccard similarity model based on skills overlap.

        Returns:
            Similarity matrix as nested dictionary
        """
        logger.info("Building Skills Jaccard baseline model")

        employee_skills = {}
        for _, row in self.candidate_data.iterrows():
            emp_id = str(row.get('Details', ''))
            if not emp_id:
                continue

            skills = row.get('Skills', [])
            if isinstance(skills, list):
                employee_skills[emp_id] = set(skills)
            else:
                employee_skills[emp_id] = set()

        # Calculate Jaccard similarities
        similarity_dict = {}
        employee_ids = list(employee_skills.keys())

        for emp_id in employee_ids:
            similarity_dict[emp_id] = {}
            emp_skills = employee_skills[emp_id]

            for other_id in employee_ids:
                other_skills = employee_skills[other_id]

                if len(emp_skills) == 0 and len(other_skills) == 0:
                    jaccard = 1.0 if emp_id == other_id else 0.0
                else:
                    intersection = len(emp_skills & other_skills)
                    union = len(emp_skills | other_skills)
                    jaccard = intersection / union if union > 0 else 0.0

                similarity_dict[emp_id][other_id] = jaccard

        logger.info(f"Jaccard model built for {len(employee_ids)} employees")
        self.models['jaccard'] = similarity_dict
        return similarity_dict

    def build_education_baseline(self) -> Dict[str, Dict[str, float]]:
        """
        Build education-only similarity model.

        Returns:
            Similarity matrix based on education similarity
        """
        logger.info("Building Education baseline model")

        employee_education = {}
        for _, row in self.candidate_data.iterrows():
            emp_id = str(row.get('Details', ''))
            if not emp_id:
                continue

            education_features = {
                'level': str(row.get('Degree_level', '')).lower(),
                'type': str(row.get('Degree_type', '')).lower(),
                'university': str(row.get('University', '')).lower()
            }
            employee_education[emp_id] = education_features

        # Calculate education similarities
        similarity_dict = {}
        employee_ids = list(employee_education.keys())

        for emp_id in employee_ids:
            similarity_dict[emp_id] = {}
            emp_edu = employee_education[emp_id]

            for other_id in employee_ids:
                other_edu = employee_education[other_id]

                # Calculate weighted education similarity
                level_match = 1.0 if emp_edu['level'] == other_edu['level'] else 0.0
                type_similarity = self._calculate_text_similarity(emp_edu['type'], other_edu['type'])
                uni_match = 1.0 if emp_edu['university'] == other_edu['university'] else 0.0

                # Weighted combination
                edu_similarity = 0.4 * level_match + 0.4 * type_similarity + 0.2 * uni_match
                similarity_dict[emp_id][other_id] = edu_similarity

        logger.info(f"Education model built for {len(employee_ids)} employees")
        self.models['education'] = similarity_dict
        return similarity_dict

    def build_random_baseline(self) -> Dict[str, Dict[str, float]]:
        """
        Build random baseline for comparison.

        Returns:
            Random similarity matrix
        """
        logger.info("Building Random baseline model")

        employee_ids = [str(row.get('Details', '')) for _, row in self.candidate_data.iterrows()
                       if str(row.get('Details', ''))]

        similarity_dict = {}
        for emp_id in employee_ids:
            similarity_dict[emp_id] = {}
            for other_id in employee_ids:
                if emp_id == other_id:
                    similarity_dict[emp_id][other_id] = 1.0
                else:
                    similarity_dict[emp_id][other_id] = np.random.random()

        logger.info(f"Random model built for {len(employee_ids)} employees")
        self.models['random'] = similarity_dict
        return similarity_dict

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity using character overlap."""
        if not text1 or not text2:
            return 0.0

        # Simple character-level similarity
        set1 = set(text1.lower())
        set2 = set(text2.lower())

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

class ModelBenchmark:
    """Benchmark different recommendation models."""

    def __init__(self, knowledge_graph_model: Dict, candidate_data: pd.DataFrame):
        """
        Initialize benchmark with knowledge graph model and data.

        Args:
            knowledge_graph_model: Your trained knowledge graph model
            candidate_data: Candidate information DataFrame
        """
        self.kg_model = knowledge_graph_model
        self.candidate_data = candidate_data
        self.baseline_models = BaselineModels(candidate_data)
        self.results = {}

    def run_benchmark(self, test_cases: List[Tuple[str, List[str]]] = None) -> Dict[str, Any]:
        """
        Run comprehensive benchmark comparing all models.

        Args:
            test_cases: Optional test cases for evaluation

        Returns:
            Benchmark results dictionary
        """
        logger.info("Starting model benchmark")

        # Build baseline models
        baselines = {
            'TF-IDF': self.baseline_models.build_tfidf_baseline(),
            'Skills Jaccard': self.baseline_models.build_skills_jaccard_baseline(),
            'Education Only': self.baseline_models.build_education_baseline(),
            'Random': self.baseline_models.build_random_baseline()
        }

        # Add knowledge graph model
        models = {
            'Knowledge Graph': self.kg_model,
            **baselines
        }

        # Generate test cases if not provided
        if test_cases is None:
            logger.info("Generating automatic test cases")
            evaluator = RecommendationEvaluator(self.kg_model, self.candidate_data)
            test_cases = evaluator.generate_test_pairs_from_clusters(min_cluster_size=3)
            # Sample for faster evaluation
            test_cases = test_cases[:30] if len(test_cases) > 30 else test_cases

        logger.info(f"Evaluating {len(models)} models on {len(test_cases)} test cases")

        # Evaluate each model
        for model_name, model in models.items():
            logger.info(f"Evaluating {model_name}")
            start_time = time.time()

            evaluator = RecommendationEvaluator(model, self.candidate_data)
            model_results = evaluator.evaluate_substitution_accuracy(test_cases, k=3)

            # Add timing information
            evaluation_time = time.time() - start_time
            model_results['evaluation_time'] = evaluation_time

            # Add model-specific metrics
            if model_name != 'Random':
                # Sample detailed analysis
                sample_emp_id = list(model.keys())[0]
                recommendations = evaluator._get_recommendations(sample_emp_id, 3)
                if recommendations:
                    skill_analysis = evaluator.skill_overlap_analysis(sample_emp_id, recommendations)
                    model_results.update(skill_analysis)

            self.results[model_name] = model_results

        # Calculate relative performance
        self._calculate_relative_performance()

        logger.info("Benchmark completed")
        return self.results

    def _calculate_relative_performance(self):
        """Calculate relative performance metrics."""
        # Use random baseline as reference
        if 'Random' not in self.results:
            return

        random_precision = self.results['Random'].get('precision@3', 0)

        for model_name, results in self.results.items():
            if model_name == 'Random':
                continue

            model_precision = results.get('precision@3', 0)
            improvement = model_precision - random_precision
            relative_improvement = (improvement / random_precision * 100) if random_precision > 0 else 0

            results['improvement_over_random'] = improvement
            results['relative_improvement_pct'] = relative_improvement

    def generate_benchmark_report(self) -> str:
        """Generate comprehensive benchmark report."""
        if not self.results:
            return "No benchmark results available"

        report = []
        report.append("=" * 80)
        report.append("MODEL BENCHMARK REPORT")
        report.append("=" * 80)
        report.append("")

        # Performance comparison table
        report.append("PERFORMANCE COMPARISON")
        report.append("-" * 50)
        report.append(f"{'Model':<20} {'Hit@3':<10} {'Precision@3':<12} {'F1@3':<10} {'Time(s)':<10}")
        report.append("-" * 62)

        # Sort models by precision
        sorted_models = sorted(
            self.results.items(),
            key=lambda x: x[1].get('precision@3', 0),
            reverse=True
        )

        for model_name, results in sorted_models:
            hit_rate = results.get('hit_rate@3', 0)
            precision = results.get('precision@3', 0)
            f1_score = results.get('f1_score@3', 0)
            eval_time = results.get('evaluation_time', 0)

            report.append(f"{model_name:<20} {hit_rate:<10.3f} {precision:<12.3f} {f1_score:<10.3f} {eval_time:<10.2f}")

        report.append("")

        # Relative performance
        report.append("RELATIVE PERFORMANCE (vs Random Baseline)")
        report.append("-" * 50)

        for model_name, results in sorted_models:
            if model_name == 'Random':
                continue

            improvement = results.get('improvement_over_random', 0)
            relative_pct = results.get('relative_improvement_pct', 0)

            status = "HIGH" if improvement > 0.1 else "MEDIUM" if improvement > 0.05 else "LOW"
            report.append(f"{status} {model_name}: +{improvement:.3f} ({relative_pct:+.1f}%)")

        report.append("")

        # Model rankings and insights
        report.append("MODEL INSIGHTS")
        report.append("-" * 50)

        best_model = sorted_models[0]
        worst_model = sorted_models[-1]

        report.append(f"Best Model: {best_model[0]} (Precision: {best_model[1].get('precision@3', 0):.3f})")
        report.append(f"Worst Model: {worst_model[0]} (Precision: {worst_model[1].get('precision@3', 0):.3f})")

        # Knowledge graph performance analysis
        kg_results = self.results.get('Knowledge Graph', {})
        kg_precision = kg_results.get('precision@3', 0)

        if kg_precision > 0.6:
            report.append("Knowledge Graph model shows strong performance")
        elif kg_precision > 0.4:
            report.append("Knowledge Graph model shows moderate performance")
        else:
            report.append("Knowledge Graph model needs improvement")

        # Recommendations
        report.append("")
        report.append("RECOMMENDATIONS")
        report.append("-" * 50)

        if kg_results.get('improvement_over_random', 0) < 0.1:
            report.append("• Consider feature engineering improvements for Knowledge Graph")

        tfidf_precision = self.results.get('TF-IDF', {}).get('precision@3', 0)
        if tfidf_precision > kg_precision:
            report.append("• TF-IDF baseline outperforms KG - consider hybrid approach")

        jaccard_precision = self.results.get('Skills Jaccard', {}).get('precision@3', 0)
        if jaccard_precision > kg_precision:
            report.append("• Skills-only matching is strong - ensure KG leverages this")

        report.append("• Collect more ground truth data for better evaluation")
        report.append("• Consider ensemble methods combining multiple approaches")

        return "\n".join(report)

    def save_benchmark_results(self, filepath: str):
        """Save benchmark results to file."""
        benchmark_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': self.results,
            'summary': {
                'best_model': max(self.results.items(), key=lambda x: x[1].get('precision@3', 0))[0],
                'kg_performance': self.results.get('Knowledge Graph', {}),
                'baseline_count': len(self.results) - 1
            }
        }

        with open(filepath, 'w') as f:
            json.dump(benchmark_data, f, indent=2)

        logger.info(f"Benchmark results saved to {filepath}")

def main():
    """Run benchmark comparison."""
    try:
        # Load knowledge graph model
        model_path = 'models/sim_final.pkl' if os.path.exists('models/sim_final.pkl') else 'sim_final.pkl'
        with open(model_path, 'rb') as f:
            kg_model = pickle.load(f)

        # Load candidate data
        with open('Filtered01.json', 'r') as f:
            raw_data = json.load(f)

        dataframe = pd.DataFrame(raw_data)
        df = pd.json_normalize(dataframe['structuredLayout'])
        df['Skills'] = dataframe['skillsCluster']
        df['University'] = dataframe['universties'].apply(lambda x: list(x.keys())[0] if x else None)

        # Add degree information
        degree_data = []
        for idx, degrees in enumerate(dataframe['degrees']):
            if degrees:
                for level, type_name in degrees:
                    degree_data.append({
                        'index': idx,
                        'Degree_level': level,
                        'Degree_type': type_name
                    })

        if degree_data:
            df_degrees = pd.DataFrame(degree_data)
            df_degrees = df_degrees.groupby('index').first().reset_index()
            df = df.merge(df_degrees, left_index=True, right_on='index', how='left')

        # Run benchmark
        benchmark = ModelBenchmark(kg_model, df)
        results = benchmark.run_benchmark()

        # Generate and save report
        report = benchmark.generate_benchmark_report()
        print(report)

        # Save results
        os.makedirs('evaluation', exist_ok=True)
        benchmark.save_benchmark_results('evaluation/benchmark_results.json')

        with open('evaluation/benchmark_report.txt', 'w') as f:
            f.write(report)

        print(f"\nBenchmark completed!")
        print(f"Results saved to evaluation/benchmark_results.json")
        print(f"📝 Report saved to evaluation/benchmark_report.txt")

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise

if __name__ == "__main__":
    main()