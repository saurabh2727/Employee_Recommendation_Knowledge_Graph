"""
Enhanced text processing utilities for employee recommendation system.
"""
import re
from typing import List, Set, Dict, Any
from fuzzywuzzy import fuzz, process
import spacy
from spacy.tokenizer import Tokenizer
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    """Enhanced text processing with fuzzy matching and NLP."""

    def __init__(self, tech_terms: List[str], degree_types: List[str]):
        """
        Initialize text processor with reference lists.

        Args:
            tech_terms: List of technical skills for matching
            degree_types: List of degree types for matching
        """
        self.tech_terms = [term.lower() for term in tech_terms]
        self.degree_types = [dtype.lower() for dtype in degree_types]

        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.tokenizer = Tokenizer(self.nlp.vocab)
            logger.info("SpaCy model loaded successfully")
        except OSError:
            logger.error("SpaCy model 'en_core_web_sm' not found. Please install it.")
            self.nlp = None
            self.tokenizer = None

    def clean_text(self, text: str) -> str:
        """
        Enhanced text cleaning with additional preprocessing.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text string
        """
        if not isinstance(text, str):
            text = str(text)

        # Basic cleaning
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')
        text = text.replace('/', ' ')
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = text.strip()

        return text

    def extract_skills_fuzzy(self, skills_list: List[str], threshold: int = 80) -> List[str]:
        """
        Extract skills using fuzzy string matching for better coverage.

        Args:
            skills_list: List of candidate skills
            threshold: Fuzzy matching threshold (0-100)

        Returns:
            List of matched skills
        """
        if not skills_list:
            return []

        matched_skills = set()

        for skill in skills_list:
            if not skill or not isinstance(skill, str):
                continue

            cleaned_skill = self.clean_text(skill)
            if not cleaned_skill:
                continue

            # Exact match first
            if cleaned_skill in self.tech_terms:
                matched_skills.add(cleaned_skill)
                continue

            # Fuzzy matching for partial matches
            matches = process.extractBests(
                cleaned_skill,
                self.tech_terms,
                scorer=fuzz.token_set_ratio,
                score_cutoff=threshold,
                limit=3
            )

            for match, score in matches:
                if score >= threshold:
                    matched_skills.add(match)
                    logger.debug(f"Fuzzy matched '{cleaned_skill}' -> '{match}' (score: {score})")

        return list(matched_skills)

    def extract_degree_types_enhanced(self, degree_text: str) -> List[str]:
        """
        Enhanced degree type extraction using NLP and fuzzy matching.

        Args:
            degree_text: Raw degree text

        Returns:
            List of standardized degree types
        """
        if not degree_text or not isinstance(degree_text, str):
            return []

        cleaned_text = self.clean_text(degree_text)
        if not cleaned_text:
            return []

        matched_types = set()

        # Tokenize if spaCy is available
        if self.nlp and self.tokenizer:
            try:
                doc = self.tokenizer(cleaned_text)
                tokens = [token.text for token in doc if token.text.strip()]
            except Exception as e:
                logger.warning(f"Tokenization failed, using simple split: {e}")
                tokens = cleaned_text.split()
        else:
            tokens = cleaned_text.split()

        # Check each token and n-grams
        for i, token in enumerate(tokens):
            if not token or len(token) < 3:
                continue

            # Exact match
            if token in self.degree_types:
                matched_types.add(token)
                continue

            # Fuzzy match for individual tokens
            matches = process.extractBests(
                token,
                self.degree_types,
                scorer=fuzz.ratio,
                score_cutoff=85,
                limit=2
            )

            for match, score in matches:
                matched_types.add(match)
                logger.debug(f"Degree fuzzy matched '{token}' -> '{match}' (score: {score})")

            # Check bigrams
            if i < len(tokens) - 1:
                bigram = f"{token} {tokens[i+1]}"
                bigram_matches = process.extractBests(
                    bigram,
                    self.degree_types,
                    scorer=fuzz.token_set_ratio,
                    score_cutoff=80,
                    limit=1
                )

                for match, score in bigram_matches:
                    matched_types.add(match)

        return list(matched_types)

    def standardize_degree_level(self, degree_level: str) -> str:
        """
        Enhanced degree level standardization with more variations.

        Args:
            degree_level: Raw degree level text

        Returns:
            Standardized degree level or None
        """
        if not degree_level or not isinstance(degree_level, str):
            return None

        level_lower = degree_level.lower().strip()

        # Extended matching patterns
        bachelor_patterns = ['bac', 'bachelor', 'undergraduate', 'ug', 'b.']
        master_patterns = ['mas', 'master', 'postgraduate', 'pg', 'm.']
        diploma_patterns = ['dip', 'diploma', 'certificate', 'cert']
        phd_patterns = ['phd', 'ph.d', 'doctorate', 'doctoral']

        for pattern in bachelor_patterns:
            if pattern in level_lower:
                return 'bachelor'

        for pattern in master_patterns:
            if pattern in level_lower:
                return 'master'

        for pattern in diploma_patterns:
            if pattern in level_lower:
                return 'diploma'

        for pattern in phd_patterns:
            if pattern in level_lower:
                return 'phd'

        return None

    def extract_university_enhanced(self, universities_dict: Dict[str, Any]) -> str:
        """
        Enhanced university extraction with ranking validation.

        Args:
            universities_dict: Dictionary of universities with metadata

        Returns:
            Top-ranked university name or None
        """
        if not universities_dict or not isinstance(universities_dict, dict):
            return None

        # Sort by ranking if available
        sorted_unis = []

        for uni_name, uni_data in universities_dict.items():
            if not isinstance(uni_data, dict):
                continue

            rank = uni_data.get('rank', '999')
            try:
                # Extract numeric part from rank (e.g., "351-400" -> 351)
                rank_num = int(re.search(r'\d+', str(rank)).group())
            except (AttributeError, ValueError):
                rank_num = 999

            sorted_unis.append((uni_name, rank_num))

        if not sorted_unis:
            return None

        # Return university with best (lowest) ranking
        sorted_unis.sort(key=lambda x: x[1])
        best_uni = sorted_unis[0][0]

        logger.debug(f"Selected university: {best_uni} (rank: {sorted_unis[0][1]})")
        return best_uni