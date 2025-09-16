"""
Script to test the accuracy of the employee substitution recommendation model.
"""
import os
import sys
import pickle
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.metrics import RecommendationEvaluator
from utils.logging_config import setup_logging

# Setup logging
logger = setup_logging(log_level="INFO")

def load_model_and_data():
    """Load the trained model and candidate data."""
    try:
        # Try to load from models directory first
        model_path = os.path.join('models', 'sim_final.pkl')
        if not os.path.exists(model_path):
            model_path = 'sim_final.pkl'

        logger.info(f"Loading model from {model_path}")
        with open(model_path, 'rb') as f:
            similarity_model = pickle.load(f)

        # Load candidate data
        data_path = 'Filtered01.json'
        logger.info(f"Loading data from {data_path}")

        with open(data_path, 'r') as f:
            raw_data = json.load(f)

        # Process data similar to notebook
        dataframe = pd.DataFrame(raw_data)
        df = pd.json_normalize(dataframe['structuredLayout'])
        df['Skills'] = dataframe['skillsCluster']
        df['University'] = dataframe['universties'].apply(lambda x: list(x.keys())[0] if x else None)

        # Add degree information (simplified)
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

        logger.info(f"Loaded model with {len(similarity_model)} employees")
        logger.info(f"Loaded data with {len(df)} candidate records")

        return similarity_model, df

    except Exception as e:
        logger.error(f"Error loading model or data: {e}")
        raise

def create_manual_test_cases() -> List[Tuple[str, List[str]]]:
    """
    Create manual test cases based on domain knowledge.
    These represent known good substitution cases.
    """
    # Example test cases - in practice, these would come from HR or domain experts
    test_cases = [
        # Software developers with similar skills
        ('1315', ['751', '1884']),  # From your original example
        # Add more test cases as you identify them
    ]

    logger.info(f"Created {len(test_cases)} manual test cases")
    return test_cases

def run_comprehensive_evaluation():
    """Run comprehensive evaluation of the recommendation model."""
    logger.info("Starting comprehensive evaluation")

    # Load model and data
    similarity_model, candidate_data = load_model_and_data()

    # Initialize evaluator
    evaluator = RecommendationEvaluator(similarity_model, candidate_data)

    results = {}

    # 1. Manual test cases evaluation
    logger.info("1. Evaluating manual test cases")
    manual_test_cases = create_manual_test_cases()
    if manual_test_cases:
        manual_results = evaluator.evaluate_substitution_accuracy(manual_test_cases, k=3)
        results['manual_evaluation'] = manual_results
        logger.info(f"Manual evaluation results: {manual_results}")

    # 2. Automatic test cases from clustering
    logger.info("2. Generating and evaluating clustered test cases")
    clustered_test_cases = evaluator.generate_test_pairs_from_clusters(min_cluster_size=3)
    if clustered_test_cases:
        # Sample a subset for evaluation (to avoid overwhelming computation)
        sample_size = min(50, len(clustered_test_cases))
        sampled_cases = np.random.choice(len(clustered_test_cases), sample_size, replace=False)
        sampled_test_cases = [clustered_test_cases[i] for i in sampled_cases]

        cluster_results = evaluator.evaluate_substitution_accuracy(sampled_test_cases, k=3)
        results['cluster_evaluation'] = cluster_results
        logger.info(f"Cluster evaluation results: {cluster_results}")

    # 3. Cross-validation evaluation
    logger.info("3. Running cross-validation evaluation")
    cv_results = evaluator.cross_validation_evaluation(n_splits=3, k=3)
    results['cross_validation'] = cv_results
    logger.info(f"Cross-validation results: {cv_results}")

    # 4. Similarity score analysis
    logger.info("4. Analyzing similarity score distribution")
    score_analysis = evaluator.similarity_score_distribution_analysis()
    results['similarity_analysis'] = score_analysis
    logger.info(f"Similarity analysis: {score_analysis}")

    # 5. Detailed analysis for sample employees
    logger.info("5. Running detailed analysis for sample employees")
    sample_employees = list(similarity_model.keys())[:5]  # Analyze first 5 employees
    detailed_analysis = {}

    for emp_id in sample_employees:
        recommendations = evaluator._get_recommendations(emp_id, 3)
        if recommendations:
            skill_analysis = evaluator.skill_overlap_analysis(emp_id, recommendations)
            edu_analysis = evaluator.education_compatibility_analysis(emp_id, recommendations)

            detailed_analysis[emp_id] = {
                'recommendations': recommendations,
                'skill_analysis': skill_analysis,
                'education_analysis': edu_analysis
            }

    results['detailed_analysis'] = detailed_analysis
    logger.info("Detailed analysis completed")

    # Save results
    results_file = 'evaluation/evaluation_results.json'
    os.makedirs('evaluation', exist_ok=True)
    evaluator.evaluation_results = results
    evaluator.save_evaluation_results(results_file)

    return results, evaluator

def generate_evaluation_report(results: Dict, evaluator: RecommendationEvaluator):
    """Generate a comprehensive evaluation report."""
    logger.info("Generating evaluation report")

    report = []
    report.append("=" * 80)
    report.append("EMPLOYEE SUBSTITUTION RECOMMENDATION MODEL - ACCURACY EVALUATION")
    report.append("=" * 80)
    report.append("")

    # Overall Summary
    report.append("EXECUTIVE SUMMARY")
    report.append("-" * 40)

    if 'manual_evaluation' in results:
        manual = results['manual_evaluation']
        report.append(f"Manual Test Cases:")
        report.append(f"  • Hit Rate@3: {manual.get('hit_rate@3', 0):.2%}")
        report.append(f"  • Precision@3: {manual.get('precision@3', 0):.2%}")
        report.append(f"  • F1-Score@3: {manual.get('f1_score@3', 0):.3f}")
        report.append("")

    if 'cluster_evaluation' in results:
        cluster = results['cluster_evaluation']
        report.append(f"Automated Cluster Test Cases:")
        report.append(f"  • Hit Rate@3: {cluster.get('hit_rate@3', 0):.2%}")
        report.append(f"  • Precision@3: {cluster.get('precision@3', 0):.2%}")
        report.append(f"  • F1-Score@3: {cluster.get('f1_score@3', 0):.3f}")
        report.append("")

    if 'cross_validation' in results:
        cv = results['cross_validation']
        report.append(f"Cross-Validation Results:")
        cv_hit_mean = np.mean([v for k, v in cv.items() if k == 'cv_hit_rate'])
        cv_precision_mean = np.mean([v for k, v in cv.items() if k == 'cv_skill_precision'])
        report.append(f"  • Average Hit Rate: {cv_hit_mean:.2%}")
        report.append(f"  • Average Skill Precision: {cv_precision_mean:.2%}")
        report.append("")

    # Detailed Analysis
    report.append("DETAILED ANALYSIS")
    report.append("-" * 40)

    if 'similarity_analysis' in results:
        sim = results['similarity_analysis']
        report.append(f"Similarity Score Distribution:")
        report.append(f"  • Mean Similarity: {sim.get('mean_similarity', 0):.3f}")
        report.append(f"  • Median Similarity: {sim.get('median_similarity', 0):.3f}")
        report.append(f"  • Standard Deviation: {sim.get('std_similarity', 0):.3f}")
        report.append(f"  • 95th Percentile: {sim.get('percentiles', {}).get('95th', 0):.3f}")
        report.append("")

    # Sample Employee Analysis
    if 'detailed_analysis' in results:
        report.append("SAMPLE EMPLOYEE ANALYSIS")
        report.append("-" * 40)

        for emp_id, analysis in results['detailed_analysis'].items():
            report.append(f"Employee {emp_id}:")
            report.append(f"  • Recommendations: {analysis['recommendations']}")

            skill_analysis = analysis['skill_analysis']
            report.append(f"  • Avg Skill Overlap: {skill_analysis.get('avg_skill_overlap', 0):.2%}")
            report.append(f"  • Max Skill Overlap: {skill_analysis.get('max_skill_overlap', 0):.2%}")

            edu_analysis = analysis['education_analysis']
            report.append(f"  • Education Match Rate: {edu_analysis.get('education_match_rate', 0):.2%}")
            report.append("")

    # Recommendations for Improvement
    report.append("RECOMMENDATIONS FOR IMPROVEMENT")
    report.append("-" * 40)

    sim_mean = results.get('similarity_analysis', {}).get('mean_similarity', 0)
    if sim_mean < 0.3:
        report.append("• Consider improving feature engineering to increase similarity scores")

    manual_precision = results.get('manual_evaluation', {}).get('precision@3', 0)
    if manual_precision < 0.5:
        report.append("• Model precision is below 50% - consider retraining with better features")

    report.append("• Collect more ground truth data for better evaluation")
    report.append("• Consider implementing collaborative filtering as a baseline comparison")
    report.append("• Add business rules for role-specific requirements")
    report.append("")

    # Save report
    report_text = "\n".join(report)
    with open('evaluation/evaluation_report.txt', 'w') as f:
        f.write(report_text)

    logger.info("Evaluation report saved to evaluation/evaluation_report.txt")
    print(report_text)

if __name__ == "__main__":
    try:
        results, evaluator = run_comprehensive_evaluation()
        generate_evaluation_report(results, evaluator)

        # Generate plots if matplotlib is available
        try:
            evaluator.plot_similarity_distribution('evaluation/similarity_distribution.png')

            if 'manual_evaluation' in results:
                evaluator.plot_evaluation_metrics(
                    results['manual_evaluation'],
                    'evaluation/manual_evaluation_metrics.png'
                )

            logger.info("Evaluation plots saved to evaluation/ directory")
        except Exception as e:
            logger.warning(f"Could not generate plots: {e}")

        print("\nEvaluation completed successfully!")
        print("Check evaluation/ directory for detailed results and plots")

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)