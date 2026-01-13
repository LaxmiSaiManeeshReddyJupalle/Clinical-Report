"""
Test Suite for PII Scrubber Module

Tests HIPAA-compliant PII detection and redaction capabilities.
Uses synthetic clinical data to verify scrubbing effectiveness.

Run with: pytest tests/test_scrubber.py -v
"""

import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.scrubber import (
    PIIScrubber,
    HealthcarePIIScrubber,
    ScrubResult,
    create_scrubber,
    scrub_text
)


class TestPIIScrubber:
    """Test cases for base PIIScrubber class."""

    @pytest.fixture
    def scrubber(self):
        """Create a PIIScrubber instance for testing."""
        return PIIScrubber()

    def test_scrubber_initialization(self, scrubber):
        """Test that scrubber initializes correctly."""
        assert scrubber is not None
        assert len(scrubber.entities) > 0
        assert scrubber.score_threshold == 0.5

    def test_scrub_empty_text(self, scrubber):
        """Test scrubbing empty text returns empty result."""
        result = scrubber.scrub("")
        assert result.scrubbed_text == ""
        assert result.entities_found == 0

    def test_scrub_no_pii(self, scrubber):
        """Test text without PII returns unchanged."""
        text = "The patient was seen for routine follow-up."
        result = scrubber.scrub(text)
        assert result.entities_found == 0
        assert result.scrubbed_text == text

    def test_scrub_person_name(self, scrubber):
        """Test that person names are redacted."""
        text = "John Smith was admitted on Monday."
        result = scrubber.scrub(text)
        assert "John Smith" not in result.scrubbed_text
        assert "[REDACTED-PERSON]" in result.scrubbed_text or result.entities_found > 0

    def test_scrub_ssn(self, scrubber):
        """Test that SSNs are redacted."""
        text = "Patient SSN: 123-45-6789"
        result = scrubber.scrub(text)
        assert "123-45-6789" not in result.scrubbed_text
        assert result.entities_found > 0

    def test_scrub_phone_number(self, scrubber):
        """Test that phone numbers are redacted."""
        text = "Contact: (555) 123-4567"
        result = scrubber.scrub(text)
        assert "(555) 123-4567" not in result.scrubbed_text

    def test_scrub_email(self, scrubber):
        """Test that email addresses are redacted."""
        text = "Email: patient@example.com"
        result = scrubber.scrub(text)
        assert "patient@example.com" not in result.scrubbed_text

    def test_scrub_result_statistics(self, scrubber):
        """Test that scrub result includes correct statistics."""
        text = "John Smith, SSN 123-45-6789, phone (555) 123-4567"
        result = scrubber.scrub(text)

        assert isinstance(result, ScrubResult)
        assert result.original_length == len(text)
        assert result.scrubbed_length > 0
        assert result.entities_found >= 1
        assert isinstance(result.entity_types, dict)

    def test_batch_scrubbing(self, scrubber):
        """Test batch scrubbing of multiple texts."""
        texts = [
            "John Smith was admitted.",
            "Jane Doe has SSN 987-65-4321.",
            "No PII in this text."
        ]
        results = scrubber.scrub_batch(texts)

        assert len(results) == 3
        assert all(isinstance(r, ScrubResult) for r in results)

    def test_entity_report(self, scrubber):
        """Test entity report generation."""
        text = "Patient John Smith, SSN 123-45-6789"
        report = scrubber.get_entity_report(text)

        assert 'total_entities' in report
        assert 'unique_types' in report
        assert 'entity_breakdown' in report
        assert 'text_length' in report


class TestHealthcarePIIScrubber:
    """Test cases for Healthcare-specific scrubber."""

    @pytest.fixture
    def healthcare_scrubber(self):
        """Create a HealthcarePIIScrubber instance."""
        return HealthcarePIIScrubber()

    def test_healthcare_scrubber_initialization(self, healthcare_scrubber):
        """Test healthcare scrubber initializes with HIPAA entities."""
        assert healthcare_scrubber is not None
        assert "PERSON" in healthcare_scrubber.entities
        assert "US_SSN" in healthcare_scrubber.entities
        assert "PHI-" in healthcare_scrubber.redaction_format

    def test_hipaa_safe_harbor_compliance(self, healthcare_scrubber):
        """Test that HIPAA Safe Harbor identifiers are detected."""
        # Text containing multiple HIPAA identifiers
        text = """
        Patient: John Smith
        DOB: 01/15/1980
        SSN: 123-45-6789
        Phone: (555) 123-4567
        Email: john.smith@email.com
        Address: 123 Main St, Chicago, IL 60601
        """

        result = healthcare_scrubber.scrub(text)

        # Verify PII is redacted
        assert "John Smith" not in result.scrubbed_text
        assert "123-45-6789" not in result.scrubbed_text
        assert "(555) 123-4567" not in result.scrubbed_text
        assert "john.smith@email.com" not in result.scrubbed_text

    def test_clinical_document_scrubbing(self, healthcare_scrubber):
        """Test scrubbing of realistic clinical document."""
        clinical_text = """
        ADMISSION SUMMARY

        Patient: Susan Lewis
        Date of Birth: 07/08/1961
        SSN: 915-95-4233
        Phone: (555) 199-4476

        Chief Complaint: Patient presents with worsening depression.

        Assessment: 64-year-old female with history of Major Depressive Disorder.

        Plan: Admit to ATU for stabilization.

        Provider: Dr. James Peterson, MD
        """

        result = healthcare_scrubber.scrub(clinical_text)

        # Patient identifiers should be redacted
        assert "Susan Lewis" not in result.scrubbed_text
        assert "915-95-4233" not in result.scrubbed_text
        assert "(555) 199-4476" not in result.scrubbed_text

        # Clinical content should remain
        assert "ADMISSION SUMMARY" in result.scrubbed_text
        assert "Chief Complaint" in result.scrubbed_text
        assert "Major Depressive Disorder" in result.scrubbed_text

    def test_preserves_clinical_terminology(self, healthcare_scrubber):
        """Test that medical terminology is preserved."""
        text = """
        Diagnosis: Major Depressive Disorder, recurrent, moderate
        Medications: Sertraline 50mg daily, Trazodone 50mg at bedtime
        Mental Status: Alert and oriented x4, mood depressed, affect flat
        """

        result = healthcare_scrubber.scrub(text)

        # Medical terms should be preserved
        assert "Major Depressive Disorder" in result.scrubbed_text
        assert "Sertraline" in result.scrubbed_text
        assert "Trazodone" in result.scrubbed_text
        assert "Mental Status" in result.scrubbed_text


class TestMockDocumentScrubbing:
    """Test scrubbing on actual mock documents."""

    @pytest.fixture
    def mock_data_path(self):
        """Get path to mock data directory."""
        return Path(__file__).parent.parent / "mock_data"

    @pytest.fixture
    def healthcare_scrubber(self):
        """Create healthcare scrubber."""
        return HealthcarePIIScrubber()

    def test_mock_data_exists(self, mock_data_path):
        """Verify mock data directory exists."""
        assert mock_data_path.exists(), "Mock data not found. Run mock_data_generator first."

    def test_scrub_mock_admission_summary(self, mock_data_path, healthcare_scrubber):
        """Test scrubbing a mock admission summary."""
        # Find an admission summary file
        admission_files = list(mock_data_path.glob("**/admission_summary.txt"))

        if not admission_files:
            pytest.skip("No mock admission summaries found")

        # Read and scrub the file
        content = admission_files[0].read_text()
        result = healthcare_scrubber.scrub(content)

        # Should find PII in admission summary
        assert result.entities_found > 0, "Expected to find PII in admission summary"

        # SSN pattern should be redacted
        import re
        ssn_pattern = r'\d{3}-\d{2}-\d{4}'
        assert not re.search(ssn_pattern, result.scrubbed_text), "SSN should be redacted"

    def test_scrub_mock_progress_note(self, mock_data_path, healthcare_scrubber):
        """Test scrubbing a mock progress note."""
        # Find a progress note file
        progress_files = list(mock_data_path.glob("**/progress_note_*.txt"))

        if not progress_files:
            pytest.skip("No mock progress notes found")

        content = progress_files[0].read_text()
        result = healthcare_scrubber.scrub(content)

        # Progress notes contain patient names
        assert result.entities_found > 0, "Expected to find PII in progress note"

    def test_scrub_all_mock_documents(self, mock_data_path, healthcare_scrubber):
        """Test scrubbing all mock documents."""
        all_docs = list(mock_data_path.glob("**/*.txt"))

        if not all_docs:
            pytest.skip("No mock documents found")

        total_entities = 0
        docs_with_pii = 0

        for doc_path in all_docs:
            content = doc_path.read_text()
            result = healthcare_scrubber.scrub(content)
            total_entities += result.entities_found
            if result.entities_found > 0:
                docs_with_pii += 1

        # All clinical docs should have some PII
        assert docs_with_pii > 0, "Expected some documents to contain PII"
        print(f"\nScrubbed {len(all_docs)} documents, found {total_entities} PII entities")


class TestFactoryFunctions:
    """Test factory and convenience functions."""

    def test_create_scrubber_default(self):
        """Test default scrubber creation (healthcare mode)."""
        scrubber = create_scrubber()
        assert isinstance(scrubber, HealthcarePIIScrubber)

    def test_create_scrubber_standard(self):
        """Test standard scrubber creation."""
        scrubber = create_scrubber(healthcare_mode=False)
        assert isinstance(scrubber, PIIScrubber)
        assert not isinstance(scrubber, HealthcarePIIScrubber)

    def test_scrub_text_convenience(self):
        """Test convenience scrub_text function."""
        text = "Patient John Smith, SSN 123-45-6789"
        result = scrub_text(text)

        assert isinstance(result, str)
        assert "John Smith" not in result
        assert "123-45-6789" not in result


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def scrubber(self):
        return PIIScrubber()

    def test_scrub_whitespace_only(self, scrubber):
        """Test scrubbing whitespace-only text."""
        result = scrubber.scrub("   \n\t  ")
        assert result.entities_found == 0

    def test_scrub_special_characters(self, scrubber):
        """Test scrubbing text with special characters."""
        text = "Patient: @#$%^&*() - no real PII here!"
        result = scrubber.scrub(text)
        # Should handle gracefully
        assert result is not None

    def test_scrub_unicode(self, scrubber):
        """Test scrubbing text with unicode characters."""
        text = "Patient José García was seen today."
        result = scrubber.scrub(text)
        # Should handle unicode names
        assert result is not None

    def test_scrub_very_long_text(self, scrubber):
        """Test scrubbing very long text."""
        # Create a long document
        long_text = "John Smith was seen. " * 1000
        result = scrubber.scrub(long_text)
        assert result is not None
        assert result.scrubbed_length > 0

    def test_custom_score_threshold(self):
        """Test custom confidence score threshold."""
        scrubber_low = PIIScrubber(score_threshold=0.3)
        scrubber_high = PIIScrubber(score_threshold=0.9)

        text = "Maybe John Smith was here?"

        result_low = scrubber_low.scrub(text)
        result_high = scrubber_high.scrub(text)

        # Lower threshold might catch more entities
        # This is just to verify different thresholds work
        assert result_low is not None
        assert result_high is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
