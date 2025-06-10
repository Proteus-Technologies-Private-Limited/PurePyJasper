"""
Exception classes for PyJasper library.
"""


class JasperError(Exception):
    """Base exception for all PyJasper errors."""
    pass


class JRXMLParseError(JasperError):
    """Raised when JRXML parsing fails."""
    pass


class DatabaseError(JasperError):
    """Raised when database operations fail."""
    pass


class RenderError(JasperError):
    """Raised when report rendering fails."""
    pass


class ExpressionError(JasperError):
    """Raised when expression evaluation fails."""
    pass


class ParameterError(JasperError):
    """Raised when parameter processing fails."""
    pass