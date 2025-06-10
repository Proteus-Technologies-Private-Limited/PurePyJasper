"""
PyJasper - A comprehensive Python library for JasperReports functionality.

This library provides full JasperReports compatibility including:
- JRXML parsing and processing
- SQL query execution with multiple database support
- HTML and PDF report rendering
- Parameter handling and expressions
- Group processing and aggregations
- Charts, images, and advanced formatting
"""

from .core import JasperReport
from .renderers import HTMLRenderer, PDFRenderer
from .parsers import JRXMLParser
from .database import DatabaseEngine
from .exceptions import (
    JasperError,
    JRXMLParseError,
    DatabaseError,
    RenderError
)

__version__ = "1.0.0"
__author__ = "PyJasper Team"

__all__ = [
    'JasperReport',
    'HTMLRenderer', 
    'PDFRenderer',
    'JRXMLParser',
    'DatabaseEngine',
    'JasperError',
    'JRXMLParseError', 
    'DatabaseError',
    'RenderError'
]