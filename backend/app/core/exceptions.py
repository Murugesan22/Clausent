class ClausentBaseException(Exception):
    """Base exception for all Clausent domain errors."""
    def __init__(self, message: str, stage: str = "general", details: dict = None):
        super().__init__(message)
        self.message = message
        self.stage = stage
        self.details = details or {}

class DocumentValidationError(ClausentBaseException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, stage="document_validation", details=details)

class ExtractionError(ClausentBaseException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, stage="text_extraction", details=details)

class LanguageDetectionError(ClausentBaseException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, stage="language_detection", details=details)

class TranslationError(ClausentBaseException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, stage="translation", details=details)

class SegmentationError(ClausentBaseException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, stage="clause_segmentation", details=details)

class ClassificationError(ClausentBaseException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, stage="clause_classification", details=details)

class RiskAssessmentError(ClausentBaseException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, stage="risk_assessment", details=details)

class ExplanationError(ClausentBaseException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, stage="explanation_generation", details=details)

class ReportGenerationError(ClausentBaseException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, stage="report_generation", details=details)
