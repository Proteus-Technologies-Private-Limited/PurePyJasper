"""
JRXML parsing and processing functionality.
"""

import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from .exceptions import JRXMLParseError


@dataclass
class Field:
    """Represents a field definition in the report."""
    name: str
    class_name: str = "java.lang.String"
    description: Optional[str] = None


@dataclass 
class Variable:
    """Represents a variable definition in the report."""
    name: str
    class_name: str = "java.lang.String"
    calculation: str = "Nothing"
    expression: Optional[str] = None
    initial_value: Optional[str] = None
    reset_type: str = "Report"
    reset_group: Optional[str] = None


@dataclass
class Group:
    """Represents a group definition in the report."""
    name: str
    expression: str
    header_height: int = 0
    footer_height: int = 0
    variables: List[Variable] = field(default_factory=list)


@dataclass
class ReportElement:
    """Base class for report elements like text fields, static text, etc."""
    x: int
    y: int
    width: int
    height: int
    element_type: str
    content: Optional[str] = None
    expression: Optional[str] = None
    style: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Band:
    """Represents a report band (title, page header, detail, etc.)."""
    name: str
    height: int
    elements: List[ReportElement] = field(default_factory=list)


@dataclass
class ReportDefinition:
    """Complete report definition parsed from JRXML."""
    name: str
    page_width: int = 595
    page_height: int = 842
    column_width: int = 555
    left_margin: int = 20
    right_margin: int = 20
    top_margin: int = 20
    bottom_margin: int = 20
    query: Optional[str] = None
    fields: List[Field] = field(default_factory=list)
    variables: List[Variable] = field(default_factory=list)
    groups: List[Group] = field(default_factory=list)
    bands: Dict[str, Band] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)


class JRXMLParser:
    """Parser for JRXML files."""
    
    def __init__(self):
        self.namespace = {'jr': 'http://jasperreports.sourceforge.net/jasperreports'}
    
    def parse(self, jrxml_content: str) -> ReportDefinition:
        """Parse JRXML content and return a ReportDefinition."""
        try:
            root = ET.fromstring(jrxml_content)
            
            # Update namespace if different
            if root.tag.startswith('{'):
                ns_url = root.tag[1:root.tag.index('}')]
                self.namespace = {'jr': ns_url}
            
            # Extract basic report properties
            report_def = ReportDefinition(
                name=root.get('name', 'Report'),
                page_width=int(root.get('pageWidth', 595)),
                page_height=int(root.get('pageHeight', 842)),
                column_width=int(root.get('columnWidth', 555)),
                left_margin=int(root.get('leftMargin', 20)),
                right_margin=int(root.get('rightMargin', 20)),
                top_margin=int(root.get('topMargin', 20)),
                bottom_margin=int(root.get('bottomMargin', 20))
            )
            
            # Parse query
            report_def.query = self._parse_query(root)
            
            # Parse fields
            report_def.fields = self._parse_fields(root)
            
            # Parse variables
            report_def.variables = self._parse_variables(root)
            
            # Parse groups
            report_def.groups = self._parse_groups(root)
            
            # Parse bands
            report_def.bands = self._parse_bands(root)
            
            # Parse parameters
            report_def.parameters = self._parse_parameters(root)
            
            return report_def
            
        except ET.ParseError as e:
            raise JRXMLParseError(f"Invalid XML: {e}")
        except Exception as e:
            raise JRXMLParseError(f"Failed to parse JRXML: {e}")
    
    def _parse_query(self, root: ET.Element) -> Optional[str]:
        """Parse the query string from JRXML."""
        query_elem = root.find('.//jr:queryString', self.namespace)
        if query_elem is None:
            query_elem = root.find('.//queryString')
        
        if query_elem is not None and query_elem.text:
            query = query_elem.text.strip()
            # Remove CDATA wrapper if present
            if query.startswith('<![CDATA[') and query.endswith(']]>'):
                query = query[9:-3]
            return query.strip()
        return None
    
    def _parse_fields(self, root: ET.Element) -> List[Field]:
        """Parse field definitions from JRXML."""
        fields = []
        field_elements = root.findall('.//jr:field', self.namespace)
        if not field_elements:
            field_elements = root.findall('.//field')
        
        for field_elem in field_elements:
            name = field_elem.get('name')
            if name:
                field = Field(
                    name=name,
                    class_name=field_elem.get('class', 'java.lang.String')
                )
                
                # Check for description
                desc_elem = field_elem.find('jr:fieldDescription', self.namespace)
                if desc_elem is None:
                    desc_elem = field_elem.find('fieldDescription')
                if desc_elem is not None and desc_elem.text:
                    field.description = desc_elem.text.strip()
                
                fields.append(field)
        
        return fields
    
    def _parse_variables(self, root: ET.Element) -> List[Variable]:
        """Parse variable definitions from JRXML."""
        variables = []
        var_elements = root.findall('.//jr:variable', self.namespace)
        if not var_elements:
            var_elements = root.findall('.//variable')
        
        for var_elem in var_elements:
            name = var_elem.get('name')
            if name:
                variable = Variable(
                    name=name,
                    class_name=var_elem.get('class', 'java.lang.String'),
                    calculation=var_elem.get('calculation', 'Nothing'),
                    reset_type=var_elem.get('resetType', 'Report'),
                    reset_group=var_elem.get('resetGroup')
                )
                
                # Parse variable expression
                expr_elem = var_elem.find('jr:variableExpression', self.namespace)
                if expr_elem is None:
                    expr_elem = var_elem.find('variableExpression')
                if expr_elem is not None and expr_elem.text:
                    variable.expression = expr_elem.text.strip()
                
                # Parse initial value
                init_elem = var_elem.find('jr:initialValueExpression', self.namespace)
                if init_elem is None:
                    init_elem = var_elem.find('initialValueExpression')
                if init_elem is not None and init_elem.text:
                    variable.initial_value = init_elem.text.strip()
                
                variables.append(variable)
        
        return variables
    
    def _parse_groups(self, root: ET.Element) -> List[Group]:
        """Parse group definitions from JRXML."""
        groups = []
        group_elements = root.findall('.//jr:group', self.namespace)
        if not group_elements:
            group_elements = root.findall('.//group')
        
        for group_elem in group_elements:
            name = group_elem.get('name')
            if name:
                # Parse group expression
                expr_elem = group_elem.find('jr:groupExpression', self.namespace)
                if expr_elem is None:
                    expr_elem = group_elem.find('groupExpression')
                
                expression = ""
                if expr_elem is not None and expr_elem.text:
                    expression = expr_elem.text.strip()
                
                group = Group(name=name, expression=expression)
                
                # Parse header height
                header_elem = group_elem.find('jr:groupHeader/jr:band', self.namespace)
                if header_elem is None:
                    header_elem = group_elem.find('groupHeader/band')
                if header_elem is not None:
                    group.header_height = int(header_elem.get('height', 0))
                
                # Parse footer height
                footer_elem = group_elem.find('jr:groupFooter/jr:band', self.namespace)
                if footer_elem is None:
                    footer_elem = group_elem.find('groupFooter/band')
                if footer_elem is not None:
                    group.footer_height = int(footer_elem.get('height', 0))
                
                groups.append(group)
        
        return groups
    
    def _parse_bands(self, root: ET.Element) -> Dict[str, Band]:
        """Parse all bands from JRXML."""
        bands = {}
        
        band_types = [
            'title', 'pageHeader', 'columnHeader', 'detail', 
            'columnFooter', 'pageFooter', 'lastPageFooter', 'summary'
        ]
        
        for band_type in band_types:
            band_elem = root.find(f'.//jr:{band_type}/jr:band', self.namespace)
            if band_elem is None:
                band_elem = root.find(f'.//{band_type}/band')
            
            if band_elem is not None:
                height = int(band_elem.get('height', 0))
                band = Band(name=band_type, height=height)
                band.elements = self._parse_band_elements(band_elem)
                bands[band_type] = band
        
        return bands
    
    def _parse_band_elements(self, band_elem: ET.Element) -> List[ReportElement]:
        """Parse elements within a band."""
        elements = []
        
        # Parse static text elements
        static_texts = band_elem.findall('.//jr:staticText', self.namespace)
        if not static_texts:
            static_texts = band_elem.findall('.//staticText')
        
        for static_elem in static_texts:
            element = self._parse_element(static_elem, 'staticText')
            if element:
                # Get text content
                text_elem = static_elem.find('jr:text', self.namespace)
                if text_elem is None:
                    text_elem = static_elem.find('text')
                if text_elem is not None and text_elem.text:
                    element.content = text_elem.text.strip()
                elements.append(element)
        
        # Parse text field elements
        text_fields = band_elem.findall('.//jr:textField', self.namespace)
        if not text_fields:
            text_fields = band_elem.findall('.//textField')
        
        for field_elem in text_fields:
            element = self._parse_element(field_elem, 'textField')
            if element:
                # Get expression
                expr_elem = field_elem.find('jr:textFieldExpression', self.namespace)
                if expr_elem is None:
                    expr_elem = field_elem.find('textFieldExpression')
                if expr_elem is not None and expr_elem.text:
                    element.expression = expr_elem.text.strip()
                elements.append(element)
        
        return elements
    
    def _parse_element(self, elem: ET.Element, element_type: str) -> Optional[ReportElement]:
        """Parse a report element (static text or text field)."""
        report_elem = elem.find('jr:reportElement', self.namespace)
        if report_elem is None:
            report_elem = elem.find('reportElement')
        
        if report_elem is not None:
            return ReportElement(
                x=int(report_elem.get('x', 0)),
                y=int(report_elem.get('y', 0)),
                width=int(report_elem.get('width', 0)),
                height=int(report_elem.get('height', 0)),
                element_type=element_type,
                style=self._parse_style(elem)
            )
        return None
    
    def _parse_style(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse style information from an element."""
        style = {}
        
        # Parse text element style
        text_elem = elem.find('jr:textElement', self.namespace)
        if text_elem is None:
            text_elem = elem.find('textElement')
        
        if text_elem is not None:
            style['textAlignment'] = text_elem.get('textAlignment', 'Left')
            style['verticalAlignment'] = text_elem.get('verticalAlignment', 'Top')
            
            # Parse font
            font_elem = text_elem.find('jr:font', self.namespace)
            if font_elem is None:
                font_elem = text_elem.find('font')
            
            if font_elem is not None:
                style['fontSize'] = int(font_elem.get('size', 10))
                style['fontName'] = font_elem.get('fontName', 'SansSerif')
                style['isBold'] = font_elem.get('isBold', 'false').lower() == 'true'
                style['isItalic'] = font_elem.get('isItalic', 'false').lower() == 'true'
                style['isUnderline'] = font_elem.get('isUnderline', 'false').lower() == 'true'
        
        return style
    
    def _parse_parameters(self, root: ET.Element) -> Dict[str, Any]:
        """Parse parameter definitions from JRXML."""
        parameters = {}
        param_elements = root.findall('.//jr:parameter', self.namespace)
        if not param_elements:
            param_elements = root.findall('.//parameter')
        
        for param_elem in param_elements:
            name = param_elem.get('name')
            if name:
                param_class = param_elem.get('class', 'java.lang.String')
                
                # Get default value
                default_elem = param_elem.find('jr:defaultValueExpression', self.namespace)
                if default_elem is None:
                    default_elem = param_elem.find('defaultValueExpression')
                
                default_value = None
                if default_elem is not None and default_elem.text:
                    default_value = default_elem.text.strip()
                
                parameters[name] = {
                    'class': param_class,
                    'defaultValue': default_value
                }
        
        return parameters


class ExpressionEvaluator:
    """Evaluates JasperReports expressions."""
    
    def __init__(self, data: Dict[str, Any], variables: Dict[str, Any] = None, parameters: Dict[str, Any] = None):
        self.data = data or {}
        self.variables = variables or {}
        self.parameters = parameters or {}
    
    def evaluate(self, expression: str) -> Any:
        """Evaluate a JasperReports expression."""
        if not expression:
            return ""
        
        # Handle CDATA
        if expression.startswith('<![CDATA[') and expression.endswith(']]>'):
            expression = expression[9:-3]
        
        # Replace field references $F{fieldName}
        expression = re.sub(r'\$F\{([^}]+)\}', 
                          lambda m: f"self.data.get('{m.group(1)}', '')", 
                          expression)
        
        # Replace variable references $V{variableName}
        expression = re.sub(r'\$V\{([^}]+)\}', 
                          lambda m: f"self.variables.get('{m.group(1)}', '')", 
                          expression)
        
        # Replace parameter references $P{parameterName}
        expression = re.sub(r'\$P\{([^}]+)\}', 
                          lambda m: f"self.parameters.get('{m.group(1)}', '')", 
                          expression)
        
        # Handle string concatenation
        expression = expression.replace(' + ', ' + str(')
        if ' + str(' in expression:
            expression = expression.replace(' + str(', ') + str(') + ')'
        
        try:
            # Simple evaluation for basic expressions
            if expression.startswith('"') and expression.endswith('"'):
                return expression[1:-1]  # String literal
            
            # For now, return the expression as is for complex cases
            # In a full implementation, you'd want a proper expression parser
            return str(eval(expression))
        except:
            return str(expression)