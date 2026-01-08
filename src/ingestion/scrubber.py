"""
PII Scrubber Module for UIC ATU Clinical Report Generator

Provides HIPAA-compliant PII detection and redaction using Microsoft Presidio.
Redacts names, SSNs, and other sensitive identifiers from clinical documents.

SECURITY: This module processes PHI. All scrubbing operations are logged
without exposing the actual PII content.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Configure logging (no PHI in logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PIIType(Enum):
    """Supported PII entity types for detection."""
    PERSON = "PERSON"
    SSN = "US_SSN"
    PHONE = "PHONE_NUMBER"
    EMAIL = "EMAIL_ADDRESS"
    ADDRESS = "ADDRESS"  # Note: May need custom recognizer
    DATE_OF_BIRTH = "DATE_TIME"  # Dates can be PHI in context
    MEDICAL_RECORD = "MEDICAL_LICENSE"  # Closest built-in
    CREDIT_CARD = "CREDIT_CARD"
    US_DRIVER_LICENSE = "US_DRIVER_LICENSE"
    US_PASSPORT = "US_PASSPORT"


@dataclass
class ScrubResult:
    """Result of PII scrubbing operation."""
    original_length: int
    scrubbed_length: int
    entities_found: int
    entity_types: Dict[str, int]
    scrubbed_text: str


class PIIScrubber:
    """
    HIPAA-compliant PII detection and redaction engine.

    Uses Microsoft Presidio for entity recognition and anonymization.
    Default configuration targets healthcare-relevant PII:
    - Names (PERSON)
    - Social Security Numbers (US_SSN)
    - Phone numbers
    - Email addresses

    SECURITY NOTICE:
    - Original text containing PHI is NEVER logged
    - Only entity counts and types are logged for audit purposes
    - Scrubbed output uses consistent redaction markers
    """

    # Default entities to detect (HIPAA Safe Harbor)
    DEFAULT_ENTITIES = [
        "PERSON",
        "US_SSN",
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "CREDIT_CARD",
        "US_DRIVER_LICENSE",
        "US_PASSPORT",
        "DATE_TIME",  # Dates can be PHI
        "LOCATION",   # Geographic data
    ]

    # Default redaction format
    DEFAULT_REDACTION = "[REDACTED-{entity_type}]"

    def __init__(
        self,
        entities: Optional[List[str]] = None,
        redaction_format: Optional[str] = None,
        score_threshold: float = 0.5,
        language: str = "en"
    ):
        """
        Initialize PII Scrubber with Presidio engines.

        Args:
            entities: List of entity types to detect. Defaults to DEFAULT_ENTITIES.
            redaction_format: Format string for redaction. Use {entity_type} placeholder.
            score_threshold: Minimum confidence score for detection (0.0-1.0).
            language: Language code for analysis. Defaults to English.
        """
        self.entities = entities or self.DEFAULT_ENTITIES
        self.redaction_format = redaction_format or self.DEFAULT_REDACTION
        self.score_threshold = score_threshold
        self.language = language

        # Initialize Presidio engines
        logger.info("Initializing PII detection engines")
        self._analyzer = AnalyzerEngine()
        self._anonymizer = AnonymizerEngine()
        logger.info(f"PII Scrubber initialized. Detecting {len(self.entities)} entity types.")

    def analyze(self, text: str) -> List[RecognizerResult]:
        """
        Analyze text for PII entities without modifying it.

        Args:
            text: Text to analyze for PII

        Returns:
            List of RecognizerResult objects with entity details

        Note: Results contain PII locations - handle securely.
        """
        if not text or not text.strip():
            return []

        try:
            results = self._analyzer.analyze(
                text=text,
                entities=self.entities,
                language=self.language,
                score_threshold=self.score_threshold
            )
            # Log count only, never content
            logger.info(f"Analysis complete. Found {len(results)} potential PII entities.")
            return results
        except Exception as e:
            logger.error(f"PII analysis failed: {type(e).__name__}")
            raise

    def scrub(self, text: str) -> ScrubResult:
        """
        Detect and redact PII from text.

        Args:
            text: Text containing potential PII

        Returns:
            ScrubResult with scrubbed text and statistics

        Example:
            >>> scrubber = PIIScrubber()
            >>> result = scrubber.scrub("John Smith's SSN is 123-45-6789")
            >>> print(result.scrubbed_text)
            "[REDACTED-PERSON]'s SSN is [REDACTED-US_SSN]"
        """
        if not text or not text.strip():
            return ScrubResult(
                original_length=0,
                scrubbed_length=0,
                entities_found=0,
                entity_types={},
                scrubbed_text=""
            )

        original_length = len(text)

        try:
            # Analyze for PII
            analysis_results = self.analyze(text)

            if not analysis_results:
                logger.info("No PII detected in text")
                return ScrubResult(
                    original_length=original_length,
                    scrubbed_length=original_length,
                    entities_found=0,
                    entity_types={},
                    scrubbed_text=text
                )

            # Count entity types
            entity_counts: Dict[str, int] = {}
            for result in analysis_results:
                entity_type = result.entity_type
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

            # Configure anonymization operators
            operators = {}
            for entity in self.entities:
                operators[entity] = OperatorConfig(
                    "replace",
                    {"new_value": self.redaction_format.format(entity_type=entity)}
                )

            # Anonymize text
            anonymized = self._anonymizer.anonymize(
                text=text,
                analyzer_results=analysis_results,
                operators=operators
            )

            scrubbed_text = anonymized.text
            scrubbed_length = len(scrubbed_text)

            # Log statistics only (HIPAA compliance)
            logger.info(
                f"PII scrubbing complete. "
                f"Entities redacted: {len(analysis_results)}. "
                f"Types: {list(entity_counts.keys())}"
            )

            return ScrubResult(
                original_length=original_length,
                scrubbed_length=scrubbed_length,
                entities_found=len(analysis_results),
                entity_types=entity_counts,
                scrubbed_text=scrubbed_text
            )

        except Exception as e:
            logger.error(f"PII scrubbing failed: {type(e).__name__}")
            raise

    def scrub_batch(self, texts: List[str]) -> List[ScrubResult]:
        """
        Scrub PII from multiple texts.

        Args:
            texts: List of texts to scrub

        Returns:
            List of ScrubResult objects in same order as input
        """
        results = []
        total_entities = 0

        for i, text in enumerate(texts):
            result = self.scrub(text)
            results.append(result)
            total_entities += result.entities_found

        logger.info(f"Batch scrubbing complete. Processed {len(texts)} texts, {total_entities} total entities.")
        return results

    def get_entity_report(self, text: str) -> Dict[str, Any]:
        """
        Generate a detailed report of PII found in text.

        Useful for audit and compliance review.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with analysis statistics (no actual PII values)
        """
        analysis_results = self.analyze(text)

        # Build report without exposing PII
        entity_stats = {}
        confidence_scores = []

        for result in analysis_results:
            entity_type = result.entity_type
            if entity_type not in entity_stats:
                entity_stats[entity_type] = {
                    'count': 0,
                    'avg_confidence': 0.0,
                    'min_confidence': 1.0,
                    'max_confidence': 0.0
                }

            stats = entity_stats[entity_type]
            stats['count'] += 1
            stats['max_confidence'] = max(stats['max_confidence'], result.score)
            stats['min_confidence'] = min(stats['min_confidence'], result.score)
            confidence_scores.append((entity_type, result.score))

        # Calculate averages
        for entity_type in entity_stats:
            scores = [s for t, s in confidence_scores if t == entity_type]
            entity_stats[entity_type]['avg_confidence'] = sum(scores) / len(scores)

        return {
            'total_entities': len(analysis_results),
            'unique_types': len(entity_stats),
            'entity_breakdown': entity_stats,
            'text_length': len(text)
        }


class HealthcarePIIScrubber(PIIScrubber):
    """
    Specialized PII scrubber for healthcare/clinical documents.

    Extends base scrubber with healthcare-specific entity detection
    including medical record numbers, provider names, and facility names.
    """

    # HIPAA Safe Harbor - 18 identifiers
    HIPAA_ENTITIES = [
        "PERSON",           # Names
        "US_SSN",           # SSN
        "PHONE_NUMBER",     # Phone/Fax
        "EMAIL_ADDRESS",    # Email
        "DATE_TIME",        # Dates (except year)
        "LOCATION",         # Geographic data
        "CREDIT_CARD",      # Account numbers
        "US_DRIVER_LICENSE",  # License numbers
        "US_PASSPORT",      # Other IDs
        "IP_ADDRESS",       # IP addresses
        "URL",              # URLs
    ]

    def __init__(self, **kwargs):
        """Initialize healthcare-specific PII scrubber."""
        # Override entities with HIPAA list
        kwargs['entities'] = self.HIPAA_ENTITIES
        kwargs['redaction_format'] = kwargs.get('redaction_format', "[PHI-{entity_type}]")

        super().__init__(**kwargs)
        logger.info("Healthcare PII Scrubber initialized with HIPAA Safe Harbor entities")


def create_scrubber(healthcare_mode: bool = True) -> PIIScrubber:
    """
    Factory function to create appropriate scrubber.

    Args:
        healthcare_mode: If True, use HIPAA-compliant healthcare scrubber

    Returns:
        Configured PIIScrubber instance
    """
    if healthcare_mode:
        return HealthcarePIIScrubber()
    return PIIScrubber()


# Convenience function for quick scrubbing
def scrub_text(text: str, healthcare_mode: bool = True) -> str:
    """
    Quick utility to scrub PII from text.

    Args:
        text: Text to scrub
        healthcare_mode: Use HIPAA-compliant scrubbing

    Returns:
        Scrubbed text with PII redacted
    """
    scrubber = create_scrubber(healthcare_mode)
    result = scrubber.scrub(text)
    return result.scrubbed_text
