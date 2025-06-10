"""
Report rendering functionality for HTML and PDF outputs.
"""

from typing import Dict, List, Any, Optional
from io import BytesIO
import base64
from .parsers import ReportDefinition, ExpressionEvaluator
from .database import DataProcessor
from .exceptions import RenderError


class BaseRenderer:
    """Base class for all renderers."""
    
    def __init__(self, report_def: ReportDefinition):
        self.report_def = report_def
        self.data = []
        self.parameters = {}
        self.variables = {}
        self.current_page = 1
        self.total_pages = 1
    
    def set_data(self, data: List[Dict[str, Any]]):
        """Set the data for the report."""
        self.data = data
    
    def set_parameters(self, parameters: Dict[str, Any]):
        """Set parameters for the report."""
        self.parameters = parameters
    
    def render(self) -> bytes:
        """Render the report. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement render method")


class HTMLRenderer(BaseRenderer):
    """Renders reports to HTML format."""
    
    def __init__(self, report_def: ReportDefinition):
        super().__init__(report_def)
        self.css_styles = self._generate_css()
    
    def render(self) -> bytes:
        """Render the report to HTML."""
        try:
            html_content = self._generate_html()
            return html_content.encode('utf-8')
        except Exception as e:
            raise RenderError(f"HTML rendering failed: {e}")
    
    def _generate_html(self) -> str:
        """Generate the complete HTML document."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.report_def.name}</title>
    <style>{self.css_styles}</style>
</head>
<body>
    <div class="report-container">
        {self._render_title()}
        {self._render_page_header()}
        {self._render_content()}
        {self._render_page_footer()}
        {self._render_summary()}
    </div>
</body>
</html>"""
        return html
    
    def _generate_css(self) -> str:
        """Generate CSS styles based on JRXML definition only."""
        return f"""
        body {{
            font-family: 'Times New Roman', serif;
            margin: 0;
            padding: 0;
            background-color: white;
        }}
        
        .report-container {{
            max-width: {self.report_def.page_width}px;
            margin: 0 auto;
            background-color: white;
            padding: {self.report_def.top_margin}px {self.report_def.right_margin}px {self.report_def.bottom_margin}px {self.report_def.left_margin}px;
        }}
        
        .band {{
            width: 100%;
            position: relative;
        }}
        
        .element {{
            position: absolute;
            overflow: hidden;
        }}
        
        .static-text {{
            font-weight: normal;
        }}
        
        .text-field {{
            font-weight: normal;
        }}
        
        .bold {{ font-weight: bold; }}
        .italic {{ font-style: italic; }}
        .underline {{ text-decoration: underline; }}
        
        .align-left {{ text-align: left; }}
        .align-center {{ text-align: center; }}
        .align-right {{ text-align: right; }}
        .align-justify {{ text-align: justify; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th, td {{
            border: 1px solid black;
            padding: 4px;
            text-align: left;
            vertical-align: middle;
        }}
        
        th {{
            background-color: #d3d3d3;
            font-weight: bold;
        }}
        
        @media print {{
            body {{ background-color: white; padding: 0; }}
            .report-container {{ box-shadow: none; }}
        }}
        """
    
    def _render_title(self) -> str:
        """Render the title band."""
        if 'title' not in self.report_def.bands:
            return ""
        
        title_band = self.report_def.bands['title']
        html = f'<div class="band title-band" style="height: {title_band.height}px;">'
        
        for element in title_band.elements:
            html += self._render_element(element, {})
        
        html += '</div>'
        return html
    
    def _render_page_header(self) -> str:
        """Render the page header band."""
        if 'pageHeader' not in self.report_def.bands:
            return ""
        
        header_band = self.report_def.bands['pageHeader']
        html = f'<div class="band page-header" style="height: {header_band.height}px;">'
        
        for element in header_band.elements:
            html += self._render_element(element, {})
        
        html += '</div>'
        return html
    
    def _render_content(self) -> str:
        """Render the main content with grouping support."""
        if not self.data:
            return '<div class="no-data">No data available</div>'
        
        html = ""
        
        # Check if report has groups
        if self.report_def.groups:
            html += self._render_grouped_content()
        else:
            html += self._render_simple_content()
        
        return html
    
    def _render_grouped_content(self) -> str:
        """Render content with grouping based on JRXML structure."""
        html = ""
        processor = DataProcessor(self.data)
        
        # For now, handle single-level grouping
        # In a full implementation, you'd handle multiple group levels
        group = self.report_def.groups[0]
        
        # Extract field name from group expression
        import re
        field_match = re.search(r'\$F\{([^}]+)\}', group.expression)
        if not field_match:
            return self._render_simple_content()
        
        group_field = field_match.group(1)
        grouped_data = processor.group_by(group_field)
        
        for group_value, group_rows in grouped_data.items():
            # Render group header based on JRXML groupHeader band
            if 'groupHeader' in self.report_def.bands:
                group_header_band = self.report_def.bands['groupHeader']
                html += f'<div class="band" style="height: {group_header_band.height}px;">'
                
                evaluator = ExpressionEvaluator({group_field: group_value}, self.variables, self.parameters)
                for element in group_header_band.elements:
                    html += self._render_element(element, {group_field: group_value}, evaluator)
                html += '</div>'
            
            # Render detail rows for this group
            for row in group_rows:
                html += self._render_detail_row(row)
            
            # Calculate group totals
            group_processor = DataProcessor(group_rows)
            for variable in self.report_def.variables:
                if variable.calculation == 'Sum':
                    # Extract field from variable expression
                    var_field_match = re.search(r'\$F\{([^}]+)\}', variable.expression or '')
                    if var_field_match:
                        var_field = var_field_match.group(1)
                        total = group_processor.calculate_sum(var_field)
                        self.variables[variable.name] = total
            
            # Render group footer based on JRXML groupFooter band
            if 'groupFooter' in self.report_def.bands:
                group_footer_band = self.report_def.bands['groupFooter']
                html += f'<div class="band" style="height: {group_footer_band.height}px;">'
                
                evaluator = ExpressionEvaluator({}, self.variables, self.parameters)
                for element in group_footer_band.elements:
                    html += self._render_element(element, {}, evaluator)
                html += '</div>'
        
        return html
    
    def _render_simple_content(self) -> str:
        """Render content without grouping."""
        html = ""
        
        # Render column headers if present
        if 'columnHeader' in self.report_def.bands:
            html += self._render_column_header()
        
        # Render detail rows
        for row in self.data:
            html += self._render_detail_row(row)
        
        return html
    
    def _render_column_header(self) -> str:
        """Render column header band."""
        header_band = self.report_def.bands['columnHeader']
        html = f'<div class="band" style="height: {header_band.height}px;">'
        
        for element in header_band.elements:
            html += self._render_element(element, {})
        
        html += '</div>'
        return html
    
    def _render_detail_row(self, row_data: Dict[str, Any]) -> str:
        """Render a single detail row."""
        if 'detail' not in self.report_def.bands:
            return ""
        
        detail_band = self.report_def.bands['detail']
        html = f'<div class="band" style="height: {detail_band.height}px;">'
        
        evaluator = ExpressionEvaluator(row_data, self.variables, self.parameters)
        
        for element in detail_band.elements:
            html += self._render_element(element, row_data, evaluator)
        
        html += '</div>'
        return html
    
    def _render_element(self, element, row_data: Dict[str, Any] = None, evaluator: ExpressionEvaluator = None) -> str:
        """Render a single report element."""
        if not evaluator and row_data:
            evaluator = ExpressionEvaluator(row_data, self.variables, self.parameters)
        
        # Determine content
        content = ""
        if element.element_type == 'staticText' and element.content:
            content = element.content
        elif element.element_type == 'textField' and element.expression:
            if evaluator:
                content = str(evaluator.evaluate(element.expression))
            else:
                content = element.expression
        
        # Build style based on JRXML element properties
        style_parts = [
            f"left: {element.x}px",
            f"top: {element.y}px", 
            f"width: {element.width}px",
            f"height: {element.height}px",
            "border: 1px solid black",  # Add consistent border like PDF
            "box-sizing: border-box",
            "padding: 2px"
        ]
        
        # Add text styling only from JRXML
        if 'fontSize' in element.style:
            style_parts.append(f"font-size: {element.style['fontSize']}px")
        
        if 'fontName' in element.style:
            style_parts.append(f"font-family: {element.style['fontName']}")
        
        if element.style.get('isBold'):
            style_parts.append("font-weight: bold")
        
        if element.style.get('isItalic'):
            style_parts.append("font-style: italic")
        
        if element.style.get('isUnderline'):
            style_parts.append("text-decoration: underline")
        
        # Text alignment
        alignment = element.style.get('textAlignment', 'Left').lower()
        if alignment == 'center':
            style_parts.append("text-align: center")
        elif alignment == 'right':
            style_parts.append("text-align: right")
        elif alignment == 'justify':
            style_parts.append("text-align: justify")
        
        style = "; ".join(style_parts)
        
        # Format currency values
        if 'amount' in (element.expression or '').lower() or 'salary' in (element.expression or '').lower():
            try:
                if content and content != element.expression:
                    value = float(content)
                    content = f"${value:.2f}"
            except (ValueError, TypeError):
                pass
        
        css_class = f"element {element.element_type}"
        
        return f'<div class="{css_class}" style="{style}">{content}</div>'
    
    def _render_page_footer(self) -> str:
        """Render the page footer band."""
        if 'pageFooter' not in self.report_def.bands:
            return ""
        
        footer_band = self.report_def.bands['pageFooter']
        html = f'<div class="band page-footer" style="height: {footer_band.height}px;">'
        
        # Set page variables
        page_vars = {
            'PAGE_NUMBER': self.current_page,
            'PAGE_COUNT': self.total_pages
        }
        evaluator = ExpressionEvaluator({}, page_vars, self.parameters)
        
        for element in footer_band.elements:
            html += self._render_element(element, {}, evaluator)
        
        html += '</div>'
        return html
    
    def _render_summary(self) -> str:
        """Render the summary band."""
        if 'summary' not in self.report_def.bands:
            return ""
        
        summary_band = self.report_def.bands['summary']
        html = f'<div class="band summary-band" style="height: {summary_band.height}px;">'
        
        # Calculate summary variables
        processor = DataProcessor(self.data)
        for variable in self.report_def.variables:
            if variable.calculation == 'Sum':
                # Extract field from variable expression  
                import re
                field_match = re.search(r'\$F\{([^}]+)\}', variable.expression or '')
                if field_match:
                    field = field_match.group(1)
                    total = processor.calculate_sum(field)
                    self.variables[variable.name] = total
        
        evaluator = ExpressionEvaluator({}, self.variables, self.parameters)
        
        for element in summary_band.elements:
            html += self._render_element(element, {}, evaluator)
        
        html += '</div>'
        return html


class PDFRenderer(BaseRenderer):
    """Renders reports to PDF format."""
    
    def __init__(self, report_def: ReportDefinition):
        super().__init__(report_def)
    
    def render(self) -> bytes:
        """Render the report to PDF based on JRXML structure."""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus.flowables import Flowable
            from reportlab.graphics.shapes import Drawing, String, Rect
            
            buffer = BytesIO()
            
            # Calculate page size from report definition
            page_size = (self.report_def.page_width, self.report_def.page_height)
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=page_size,
                leftMargin=self.report_def.left_margin,
                rightMargin=self.report_def.right_margin,
                topMargin=self.report_def.top_margin,
                bottomMargin=self.report_def.bottom_margin
            )
            
            styles = getSampleStyleSheet()
            story = []
            
            # Render bands in order like HTML renderer
            # Title band
            if 'title' in self.report_def.bands:
                story.extend(self._render_pdf_title())
            
            # Page header band
            if 'pageHeader' in self.report_def.bands:
                story.extend(self._render_pdf_page_header())
            
            # Content (with grouping support)
            if self.data:
                story.extend(self._render_pdf_content())
            
            # Summary band
            if 'summary' in self.report_def.bands:
                story.extend(self._render_pdf_summary())
            
            # Page footer band
            if 'pageFooter' in self.report_def.bands:
                story.extend(self._render_pdf_page_footer())
            
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            raise RenderError(f"PDF rendering failed: {e}")
    
    def _extract_title_content(self) -> str:
        """Extract title content from title band."""
        title_band = self.report_def.bands.get('title')
        if not title_band:
            return ""
        
        for element in title_band.elements:
            if element.element_type == 'staticText' and element.content:
                return element.content
        
        return self.report_def.name
    
    def _prepare_table_data(self) -> List[List[str]]:
        """Prepare data for table rendering."""
        if not self.data or not self.report_def.fields:
            return []
        
        # Create header row based on columnHeader band if it exists
        if 'columnHeader' in self.report_def.bands:
            header_row = []
            column_header_band = self.report_def.bands['columnHeader']
            for element in column_header_band.elements:
                if element.element_type == 'staticText' and element.content:
                    header_row.append(element.content)
            if not header_row:  # Fallback to field names
                header_row = [field.name.replace('_', ' ').title() for field in self.report_def.fields]
        else:
            header_row = [field.name.replace('_', ' ').title() for field in self.report_def.fields]
        
        table_data = [header_row]
        
        # Add data rows
        for row in self.data:
            data_row = []
            for field in self.report_def.fields:
                value = row.get(field.name, '')
                
                # Format currency values
                if 'amount' in field.name.lower() or 'salary' in field.name.lower():
                    try:
                        amount_val = float(value) if value else 0.0
                        data_row.append(f'${amount_val:.2f}')
                    except (ValueError, TypeError):
                        data_row.append(str(value))
                else:
                    data_row.append(str(value))
            
            table_data.append(data_row)
        
        return table_data
    
    def _get_table_style(self):
        """Get table styling for PDF to match JRXML structure."""
        from reportlab.platypus import TableStyle
        from reportlab.lib import colors
        
        return TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ])
    
    def _render_pdf_title(self) -> list:
        """Render title band for PDF."""
        title_band = self.report_def.bands['title']
        elements = []
        
        for element in title_band.elements:
            if element.element_type == 'staticText' and element.content:
                from reportlab.lib.styles import ParagraphStyle
                from reportlab.platypus import Paragraph
                
                style = ParagraphStyle(
                    'Title',
                    fontSize=element.style.get('fontSize', 18),
                    alignment=1 if element.style.get('textAlignment', '').lower() == 'center' else 0,
                    fontName='Helvetica-Bold' if element.style.get('isBold') else 'Helvetica'
                )
                elements.append(Paragraph(element.content, style))
        
        return elements
    
    def _render_pdf_page_header(self) -> list:
        """Render page header band for PDF."""
        return []  # Implement if needed
    
    def _render_pdf_content(self) -> list:
        """Render main content for PDF."""
        elements = []
        
        # Check if report has groups
        if self.report_def.groups:
            elements.extend(self._render_pdf_grouped_content())
        else:
            elements.extend(self._render_pdf_simple_content())
        
        return elements
    
    def _render_pdf_grouped_content(self) -> list:
        """Render grouped content for PDF."""
        elements = []
        processor = DataProcessor(self.data)
        
        group = self.report_def.groups[0]
        import re
        field_match = re.search(r'\$F\{([^}]+)\}', group.expression)
        if not field_match:
            return self._render_pdf_simple_content()
        
        group_field = field_match.group(1)
        grouped_data = processor.group_by(group_field)
        
        for group_value, group_rows in grouped_data.items():
            # Add group header
            from reportlab.platypus import Paragraph
            from reportlab.lib.styles import ParagraphStyle
            
            group_style = ParagraphStyle(
                'GroupHeader',
                fontSize=12,
                fontName='Helvetica-Bold'
            )
            elements.append(Paragraph(f'{group_field.replace("_", " ").title()}: {group_value}', group_style))
            
            # Create table for group data
            table_data = self._prepare_group_table_data(group_rows)
            if table_data:
                from reportlab.platypus import Table
                table = Table(table_data)
                table.setStyle(self._get_table_style())
                elements.append(table)
        
        return elements
    
    def _render_pdf_simple_content(self) -> list:
        """Render simple content for PDF."""
        elements = []
        
        table_data = self._prepare_table_data()
        if table_data:
            from reportlab.platypus import Table
            table = Table(table_data)
            table.setStyle(self._get_table_style())
            elements.append(table)
        
        return elements
    
    def _prepare_group_table_data(self, group_rows: List[Dict[str, Any]]) -> List[List[str]]:
        """Prepare table data for a group."""
        if not group_rows or not self.report_def.fields:
            return []
        
        # Create header row
        header_row = [field.name.replace('_', ' ').title() for field in self.report_def.fields]
        table_data = [header_row]
        
        # Add data rows
        for row in group_rows:
            data_row = []
            for field in self.report_def.fields:
                value = row.get(field.name, '')
                
                # Format currency values
                if 'amount' in field.name.lower() or 'salary' in field.name.lower():
                    try:
                        amount_val = float(value) if value else 0.0
                        data_row.append(f'${amount_val:.2f}')
                    except (ValueError, TypeError):
                        data_row.append(str(value))
                else:
                    data_row.append(str(value))
            
            table_data.append(data_row)
        
        return table_data
    
    def _render_pdf_summary(self) -> list:
        """Render summary band for PDF."""
        elements = []
        
        # Calculate summary totals
        processor = DataProcessor(self.data)
        
        for variable in self.report_def.variables:
            if variable.calculation == 'Sum':
                import re
                field_match = re.search(r'\$F\{([^}]+)\}', variable.expression or '')
                if field_match:
                    field = field_match.group(1)
                    total = processor.calculate_sum(field)
                    
                    from reportlab.platypus import Paragraph
                    from reportlab.lib.styles import ParagraphStyle
                    
                    summary_style = ParagraphStyle(
                        'Summary',
                        fontSize=12,
                        fontName='Helvetica-Bold',
                        alignment=2  # Right align
                    )
                    elements.append(Paragraph(f"Total {field.replace('_', ' ').title()}: ${total:.2f}", summary_style))
        
        return elements
    
    def _render_pdf_page_footer(self) -> list:
        """Render page footer band for PDF."""
        return []  # Implement if needed
    
    def _extract_summary_content(self) -> str:
        """Extract summary content from summary band."""
        summary_band = self.report_def.bands.get('summary')
        if not summary_band:
            return ""
        
        # Calculate summary totals
        processor = DataProcessor(self.data)
        summary_text = ""
        
        for variable in self.report_def.variables:
            if variable.calculation == 'Sum':
                import re
                field_match = re.search(r'\$F\{([^}]+)\}', variable.expression or '')
                if field_match:
                    field = field_match.group(1)
                    total = processor.calculate_sum(field)
                    summary_text += f"Total {field.replace('_', ' ').title()}: ${total:.2f}"
        
        return summary_text