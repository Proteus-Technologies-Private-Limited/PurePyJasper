"""
Core JasperReport class that ties everything together.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging

from .parsers import JRXMLParser, ReportDefinition, ExpressionEvaluator
from .database import DatabaseEngine, DataProcessor
from .renderers import HTMLRenderer, PDFRenderer
from .charts import ChartRenderer, ImageHandler, FormattingUtils
from .exceptions import JasperError, JRXMLParseError, DatabaseError, RenderError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JasperReport:
    """Main class for generating JasperReports."""
    
    def __init__(self, jrxml_path: Optional[str] = None, jrxml_content: Optional[str] = None):
        """
        Initialize JasperReport.
        
        Args:
            jrxml_path: Path to JRXML file
            jrxml_content: JRXML content as string
        """
        if not jrxml_path and not jrxml_content:
            raise JasperError("Either jrxml_path or jrxml_content must be provided")
        
        self.jrxml_path = jrxml_path
        self.jrxml_content = jrxml_content
        self.report_def: Optional[ReportDefinition] = None
        self.data: List[Dict[str, Any]] = []
        self.parameters: Dict[str, Any] = {}
        self.database_engine: Optional[DatabaseEngine] = None
        
        # Parse JRXML
        self._parse_jrxml()
    
    def _parse_jrxml(self):
        """Parse the JRXML content."""
        try:
            parser = JRXMLParser()
            
            if self.jrxml_content:
                content = self.jrxml_content
            else:
                with open(self.jrxml_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            self.report_def = parser.parse(content)
            logger.info(f"Successfully parsed JRXML: {self.report_def.name}")
            
        except Exception as e:
            raise JRXMLParseError(f"Failed to parse JRXML: {e}")
    
    def set_database_connection(self, connection_string: str):
        """
        Set database connection for the report.
        
        Args:
            connection_string: Database connection string
        """
        try:
            self.database_engine = DatabaseEngine(connection_string)
            logger.info(f"Database connection configured: {self.database_engine.db_type}")
        except Exception as e:
            raise DatabaseError(f"Failed to configure database: {e}")
    
    def set_parameters(self, parameters: Dict[str, Any]):
        """
        Set report parameters.
        
        Args:
            parameters: Dictionary of parameter values
        """
        self.parameters = parameters.copy()
        logger.info(f"Parameters set: {list(parameters.keys())}")
    
    def set_data(self, data: List[Dict[str, Any]]):
        """
        Set data directly (bypassing database query).
        
        Args:
            data: List of dictionaries containing report data
        """
        self.data = data.copy()
        logger.info(f"Data set directly: {len(data)} rows")
    
    def execute_query(self) -> List[Dict[str, Any]]:
        """
        Execute the report query and return data.
        
        Returns:
            List of dictionaries containing query results
        """
        if not self.database_engine:
            raise DatabaseError("Database connection not configured")
        
        if not self.report_def.query:
            raise JasperError("No query defined in report")
        
        try:
            logger.info("Executing report query...")
            self.data = self.database_engine.execute_query(self.report_def.query, self.parameters)
            logger.info(f"Query executed successfully: {len(self.data)} rows returned")
            return self.data
        
        except Exception as e:
            raise DatabaseError(f"Query execution failed: {e}")
    
    def generate_html(self) -> bytes:
        """
        Generate HTML report.
        
        Returns:
            HTML report as bytes
        """
        if not self.data and self.report_def.query:
            self.execute_query()
        
        try:
            renderer = HTMLRenderer(self.report_def)
            renderer.set_data(self.data)
            renderer.set_parameters(self.parameters)
            
            logger.info("Generating HTML report...")
            result = renderer.render()
            logger.info("HTML report generated successfully")
            return result
            
        except Exception as e:
            raise RenderError(f"HTML generation failed: {e}")
    
    def generate_pdf(self) -> bytes:
        """
        Generate PDF report.
        
        Returns:
            PDF report as bytes
        """
        if not self.data and self.report_def.query:
            self.execute_query()
        
        try:
            renderer = PDFRenderer(self.report_def)
            renderer.set_data(self.data)
            renderer.set_parameters(self.parameters)
            
            logger.info("Generating PDF report...")
            result = renderer.render()
            logger.info("PDF report generated successfully")
            return result
            
        except Exception as e:
            raise RenderError(f"PDF generation failed: {e}")
    
    def save_report(self, output_path: str, format: str = 'html'):
        """
        Save report to file.
        
        Args:
            output_path: Path to save the report
            format: Output format ('html' or 'pdf')
        """
        format = format.lower()
        
        if format == 'html':
            content = self.generate_html()
        elif format == 'pdf':
            content = self.generate_pdf()
        else:
            raise JasperError(f"Unsupported format: {format}")
        
        try:
            with open(output_path, 'wb') as f:
                f.write(content)
            logger.info(f"Report saved to: {output_path}")
        except Exception as e:
            raise JasperError(f"Failed to save report: {e}")
    
    def get_report_info(self) -> Dict[str, Any]:
        """
        Get report information.
        
        Returns:
            Dictionary containing report metadata
        """
        if not self.report_def:
            return {}
        
        return {
            'name': self.report_def.name,
            'page_width': self.report_def.page_width,
            'page_height': self.report_def.page_height,
            'fields': [{'name': f.name, 'type': f.class_name} for f in self.report_def.fields],
            'variables': [{'name': v.name, 'type': v.class_name, 'calculation': v.calculation} 
                         for v in self.report_def.variables],
            'groups': [{'name': g.name, 'expression': g.expression} for g in self.report_def.groups],
            'parameters': self.report_def.parameters,
            'has_query': bool(self.report_def.query),
            'bands': list(self.report_def.bands.keys())
        }
    
    def validate_report(self) -> Dict[str, Any]:
        """
        Validate the report definition.
        
        Returns:
            Dictionary containing validation results
        """
        issues = []
        warnings = []
        
        # Check for required elements
        if not self.report_def.fields:
            warnings.append("No fields defined in report")
        
        if not self.report_def.query and not self.data:
            issues.append("No query defined and no data provided")
        
        # Check band consistency
        if 'detail' not in self.report_def.bands:
            warnings.append("No detail band defined")
        
        # Check field usage in expressions
        for band in self.report_def.bands.values():
            for element in band.elements:
                if element.expression:
                    # Simple check for field references
                    import re
                    field_refs = re.findall(r'\$F\{([^}]+)\}', element.expression)
                    for field_ref in field_refs:
                        if not any(f.name == field_ref for f in self.report_def.fields):
                            issues.append(f"Referenced field '{field_ref}' not defined")
        
        # Test database connection if configured
        db_status = "Not configured"
        if self.database_engine:
            if self.database_engine.test_connection():
                db_status = "Connected"
            else:
                db_status = "Connection failed"
                issues.append("Database connection test failed")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'database_status': db_status,
            'total_fields': len(self.report_def.fields),
            'total_variables': len(self.report_def.variables),
            'total_groups': len(self.report_def.groups),
            'total_bands': len(self.report_def.bands)
        }
    
    def preview_data(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get a preview of the report data.
        
        Args:
            limit: Maximum number of rows to return
            
        Returns:
            List of dictionaries containing preview data
        """
        if not self.data:
            if self.database_engine and self.report_def.query:
                try:
                    # Execute query with limit
                    query = self.report_def.query
                    if 'LIMIT' not in query.upper():
                        if self.database_engine.db_type == 'sqlite':
                            query += f" LIMIT {limit}"
                        elif self.database_engine.db_type == 'mysql':
                            query += f" LIMIT {limit}"
                        elif self.database_engine.db_type == 'postgresql':
                            query += f" LIMIT {limit}"
                    
                    preview_data = self.database_engine.execute_query(query, self.parameters)
                    return preview_data[:limit]
                except Exception as e:
                    logger.warning(f"Failed to preview data: {e}")
                    return []
            else:
                return []
        
        return self.data[:limit]
    
    def get_database_schema(self) -> Dict[str, Any]:
        """
        Get database schema information.
        
        Returns:
            Dictionary containing schema information
        """
        if not self.database_engine:
            return {'error': 'Database not configured'}
        
        try:
            tables = self.database_engine.get_tables()
            schema_info = {
                'database_type': self.database_engine.db_type,
                'tables': []
            }
            
            for table in tables:
                try:
                    columns = self.database_engine.get_table_schema(table)
                    schema_info['tables'].append({
                        'name': table,
                        'columns': columns
                    })
                except Exception as e:
                    logger.warning(f"Failed to get schema for table {table}: {e}")
            
            return schema_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def add_chart(self, chart_type: str, data_source: str, config: Dict[str, Any]) -> str:
        """
        Add a chart to the report (returns chart as base64 image).
        
        Args:
            chart_type: Type of chart ('bar', 'line', 'pie', etc.)
            data_source: Data source for the chart ('current' for report data)
            config: Chart configuration
            
        Returns:
            Base64 encoded chart image
        """
        chart_renderer = ChartRenderer()
        
        if data_source == 'current':
            chart_data = self.data
        else:
            # Could support other data sources in the future
            chart_data = self.data
        
        return chart_renderer.create_chart(chart_type, chart_data, config)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.database_engine:
            self.database_engine.disconnect()


class ReportBuilder:
    """Helper class for building reports programmatically."""
    
    def __init__(self, name: str = "Generated Report"):
        """
        Initialize report builder.
        
        Args:
            name: Name of the report
        """
        self.name = name
        self.fields = []
        self.query = ""
        self.page_width = 595
        self.page_height = 842
        self.margins = {'left': 20, 'right': 20, 'top': 20, 'bottom': 20}
        self.title = ""
        self.column_headers = []
    
    def add_field(self, name: str, field_type: str = "java.lang.String"):
        """Add a field to the report."""
        self.fields.append({'name': name, 'type': field_type})
        return self
    
    def set_query(self, query: str):
        """Set the SQL query for the report."""
        self.query = query
        return self
    
    def set_title(self, title: str):
        """Set the report title."""
        self.title = title
        return self
    
    def set_page_size(self, width: int, height: int):
        """Set page dimensions."""
        self.page_width = width
        self.page_height = height
        return self
    
    def set_margins(self, left: int, right: int, top: int, bottom: int):
        """Set page margins."""
        self.margins = {'left': left, 'right': right, 'top': top, 'bottom': bottom}
        return self
    
    def add_column_header(self, text: str, width: int):
        """Add a column header."""
        self.column_headers.append({'text': text, 'width': width})
        return self
    
    def build_jrxml(self) -> str:
        """Build JRXML content from the configured options."""
        jrxml = f'''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://jasperreports.sourceforge.net/jasperreports
              http://jasperreports.sourceforge.net/xsd/jasperreport.xsd"
              name="{self.name}" pageWidth="{self.page_width}" pageHeight="{self.page_height}"
              columnWidth="{self.page_width - self.margins['left'] - self.margins['right']}"
              leftMargin="{self.margins['left']}" rightMargin="{self.margins['right']}"
              topMargin="{self.margins['top']}" bottomMargin="{self.margins['bottom']}">

'''
        
        # Add query
        if self.query:
            jrxml += f'''    <queryString>
        <![CDATA[{self.query}]]>
    </queryString>

'''
        
        # Add fields
        for field in self.fields:
            jrxml += f'    <field name="{field["name"]}" class="{field["type"]}"/>\n'
        
        if self.fields:
            jrxml += '\n'
        
        # Add title band
        if self.title:
            jrxml += f'''    <title>
        <band height="60">
            <staticText>
                <reportElement x="0" y="20" width="{self.page_width - self.margins['left'] - self.margins['right']}" height="30"/>
                <textElement textAlignment="Center">
                    <font size="18" isBold="true"/>
                </textElement>
                <text><![CDATA[{self.title}]]></text>
            </staticText>
        </band>
    </title>

'''
        
        # Add column headers
        if self.column_headers:
            jrxml += '''    <columnHeader>
        <band height="25">
'''
            x_pos = 0
            for header in self.column_headers:
                jrxml += f'''            <staticText>
                <reportElement x="{x_pos}" y="5" width="{header['width']}" height="15"/>
                <textElement>
                    <font isBold="true"/>
                </textElement>
                <text><![CDATA[{header['text']}]]></text>
            </staticText>
'''
                x_pos += header['width']
            
            jrxml += '''        </band>
    </columnHeader>

'''
        
        # Add detail band
        if self.fields:
            jrxml += '''    <detail>
        <band height="20">
'''
            x_pos = 0
            field_width = (self.page_width - self.margins['left'] - self.margins['right']) // len(self.fields)
            
            for field in self.fields:
                jrxml += f'''            <textField>
                <reportElement x="{x_pos}" y="0" width="{field_width}" height="20"/>
                <textElement/>
                <textFieldExpression><![CDATA[$F{{{field['name']}}}]]></textFieldExpression>
            </textField>
'''
                x_pos += field_width
            
            jrxml += '''        </band>
    </detail>

'''
        
        jrxml += '</jasperReport>'
        return jrxml
    
    def build(self) -> JasperReport:
        """Build and return a JasperReport instance."""
        jrxml_content = self.build_jrxml()
        return JasperReport(jrxml_content=jrxml_content)