"""
Subreport and cross-reference support for PyJasper.
"""

from typing import Dict, List, Any, Optional
import os
from pathlib import Path

from .core import JasperReport
from .parsers import ReportDefinition
from .exceptions import JasperError


class SubreportManager:
    """Manages subreports and their execution."""
    
    def __init__(self, main_report: JasperReport):
        """
        Initialize subreport manager.
        
        Args:
            main_report: The main report instance
        """
        self.main_report = main_report
        self.subreports: Dict[str, JasperReport] = {}
        self.subreport_data: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_subreport(self, name: str, jrxml_path: str = None, jrxml_content: str = None):
        """
        Add a subreport.
        
        Args:
            name: Name identifier for the subreport
            jrxml_path: Path to subreport JRXML file
            jrxml_content: JRXML content as string
        """
        try:
            subreport = JasperReport(jrxml_path=jrxml_path, jrxml_content=jrxml_content)
            self.subreports[name] = subreport
        except Exception as e:
            raise JasperError(f"Failed to add subreport '{name}': {e}")
    
    def set_subreport_data(self, name: str, data: List[Dict[str, Any]]):
        """
        Set data for a specific subreport.
        
        Args:
            name: Subreport name
            data: Data for the subreport
        """
        self.subreport_data[name] = data
    
    def execute_subreport(self, name: str, parameters: Dict[str, Any] = None) -> bytes:
        """
        Execute a subreport and return HTML content.
        
        Args:
            name: Subreport name
            parameters: Parameters to pass to subreport
            
        Returns:
            HTML content of the subreport
        """
        if name not in self.subreports:
            raise JasperError(f"Subreport '{name}' not found")
        
        subreport = self.subreports[name]
        
        # Set parameters if provided
        if parameters:
            subreport.set_parameters(parameters)
        
        # Set data if available
        if name in self.subreport_data:
            subreport.set_data(self.subreport_data[name])
        elif subreport.database_engine and subreport.report_def.query:
            subreport.execute_query()
        
        return subreport.generate_html()
    
    def get_subreport_names(self) -> List[str]:
        """Get list of available subreport names."""
        return list(self.subreports.keys())


class CrossReferenceManager:
    """Manages cross-references between report elements."""
    
    def __init__(self):
        """Initialize cross-reference manager."""
        self.references: Dict[str, Dict[str, Any]] = {}
        self.bookmarks: Dict[str, str] = {}
    
    def add_bookmark(self, name: str, title: str, page: int = 1):
        """
        Add a bookmark for cross-referencing.
        
        Args:
            name: Unique bookmark name
            title: Display title for the bookmark
            page: Page number where bookmark is located
        """
        self.bookmarks[name] = {
            'title': title,
            'page': page,
            'anchor': f"bookmark_{name}"
        }
    
    def add_cross_reference(self, ref_id: str, target_bookmark: str, ref_type: str = 'link'):
        """
        Add a cross-reference to a bookmark.
        
        Args:
            ref_id: Unique reference ID
            target_bookmark: Name of target bookmark
            ref_type: Type of reference ('link', 'page', 'text')
        """
        if target_bookmark not in self.bookmarks:
            raise JasperError(f"Target bookmark '{target_bookmark}' not found")
        
        self.references[ref_id] = {
            'target': target_bookmark,
            'type': ref_type,
            'bookmark_info': self.bookmarks[target_bookmark]
        }
    
    def generate_reference_html(self, ref_id: str) -> str:
        """
        Generate HTML for a cross-reference.
        
        Args:
            ref_id: Reference ID
            
        Returns:
            HTML string for the reference
        """
        if ref_id not in self.references:
            return f"[Invalid Reference: {ref_id}]"
        
        ref = self.references[ref_id]
        bookmark = ref['bookmark_info']
        
        if ref['type'] == 'link':
            return f'<a href="#{bookmark["anchor"]}">{bookmark["title"]}</a>'
        elif ref['type'] == 'page':
            return f'<a href="#{bookmark["anchor"]}">Page {bookmark["page"]}</a>'
        elif ref['type'] == 'text':
            return bookmark['title']
        else:
            return f'<a href="#{bookmark["anchor"]}">{bookmark["title"]}</a>'
    
    def generate_bookmark_html(self, bookmark_name: str) -> str:
        """
        Generate HTML anchor for a bookmark.
        
        Args:
            bookmark_name: Name of the bookmark
            
        Returns:
            HTML anchor string
        """
        if bookmark_name not in self.bookmarks:
            return ""
        
        bookmark = self.bookmarks[bookmark_name]
        return f'<a name="{bookmark["anchor"]}"></a>'
    
    def get_bookmarks(self) -> Dict[str, Dict[str, Any]]:
        """Get all bookmarks."""
        return self.bookmarks.copy()
    
    def get_references(self) -> Dict[str, Dict[str, Any]]:
        """Get all cross-references."""
        return self.references.copy()


class TemplateManager:
    """Manages report templates for reuse."""
    
    def __init__(self, template_dir: str = "templates"):
        """
        Initialize template manager.
        
        Args:
            template_dir: Directory containing report templates
        """
        self.template_dir = Path(template_dir)
        self.templates: Dict[str, str] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load templates from the template directory."""
        if not self.template_dir.exists():
            return
        
        for template_file in self.template_dir.glob("*.jrxml"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.templates[template_file.stem] = content
            except Exception as e:
                print(f"Warning: Failed to load template {template_file}: {e}")
    
    def get_template(self, name: str) -> str:
        """
        Get template content by name.
        
        Args:
            name: Template name (without .jrxml extension)
            
        Returns:
            JRXML content of the template
        """
        if name not in self.templates:
            raise JasperError(f"Template '{name}' not found")
        
        return self.templates[name]
    
    def create_report_from_template(self, template_name: str, replacements: Dict[str, str] = None) -> JasperReport:
        """
        Create a report from a template with replacements.
        
        Args:
            template_name: Name of the template
            replacements: Dictionary of string replacements to make in template
            
        Returns:
            JasperReport instance
        """
        template_content = self.get_template(template_name)
        
        # Apply replacements
        if replacements:
            for old_value, new_value in replacements.items():
                template_content = template_content.replace(old_value, new_value)
        
        return JasperReport(jrxml_content=template_content)
    
    def save_template(self, name: str, jrxml_content: str):
        """
        Save a new template.
        
        Args:
            name: Template name
            jrxml_content: JRXML content to save
        """
        self.template_dir.mkdir(exist_ok=True)
        template_path = self.template_dir / f"{name}.jrxml"
        
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(jrxml_content)
            
            self.templates[name] = jrxml_content
        except Exception as e:
            raise JasperError(f"Failed to save template '{name}': {e}")
    
    def list_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def delete_template(self, name: str):
        """
        Delete a template.
        
        Args:
            name: Template name to delete
        """
        if name in self.templates:
            del self.templates[name]
        
        template_path = self.template_dir / f"{name}.jrxml"
        if template_path.exists():
            try:
                template_path.unlink()
            except Exception as e:
                raise JasperError(f"Failed to delete template file: {e}")


class ReportComposer:
    """Composes complex reports with multiple sections and subreports."""
    
    def __init__(self, main_report: JasperReport):
        """
        Initialize report composer.
        
        Args:
            main_report: Main report instance
        """
        self.main_report = main_report
        self.subreport_manager = SubreportManager(main_report)
        self.cross_ref_manager = CrossReferenceManager()
        self.sections: List[Dict[str, Any]] = []
    
    def add_section(self, section_type: str, content: Any, title: str = None):
        """
        Add a section to the composed report.
        
        Args:
            section_type: Type of section ('main', 'subreport', 'chart', 'text')
            content: Content for the section
            title: Optional section title
        """
        section = {
            'type': section_type,
            'content': content,
            'title': title
        }
        self.sections.append(section)
    
    def add_subreport_section(self, subreport_name: str, title: str = None, parameters: Dict[str, Any] = None):
        """
        Add a subreport as a section.
        
        Args:
            subreport_name: Name of the subreport
            title: Section title
            parameters: Parameters for the subreport
        """
        self.add_section('subreport', {
            'name': subreport_name,
            'parameters': parameters or {}
        }, title)
    
    def add_chart_section(self, chart_type: str, chart_config: Dict[str, Any], title: str = None):
        """
        Add a chart as a section.
        
        Args:
            chart_type: Type of chart
            chart_config: Chart configuration
            title: Section title
        """
        self.add_section('chart', {
            'type': chart_type,
            'config': chart_config
        }, title)
    
    def add_text_section(self, text: str, title: str = None):
        """
        Add a text section.
        
        Args:
            text: Text content
            title: Section title
        """
        self.add_section('text', text, title)
    
    def compose_html(self) -> str:
        """
        Compose all sections into a single HTML report.
        
        Returns:
            Complete HTML report
        """
        html_parts = []
        
        # Start HTML document
        html_parts.append("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Composed Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .section { margin-bottom: 30px; page-break-inside: avoid; }
        .section-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #333; }
        .main-report { border: 1px solid #ddd; padding: 10px; }
        .subreport { border: 1px solid #ccc; padding: 10px; background-color: #f9f9f9; }
        .chart-section { text-align: center; }
        .text-section { line-height: 1.6; }
        @media print { .section { page-break-after: always; } }
    </style>
</head>
<body>
""")
        
        # Process each section
        for i, section in enumerate(self.sections):
            html_parts.append(f'<div class="section" id="section-{i}">')
            
            # Add section title
            if section['title']:
                bookmark_name = f"section_{i}"
                self.cross_ref_manager.add_bookmark(bookmark_name, section['title'], 1)
                html_parts.append(self.cross_ref_manager.generate_bookmark_html(bookmark_name))
                html_parts.append(f'<div class="section-title">{section["title"]}</div>')
            
            # Add section content based on type
            if section['type'] == 'main':
                html_parts.append('<div class="main-report">')
                main_html = self.main_report.generate_html().decode('utf-8')
                # Extract body content
                body_start = main_html.find('<body>')
                body_end = main_html.find('</body>')
                if body_start != -1 and body_end != -1:
                    body_content = main_html[body_start + 6:body_end]
                    html_parts.append(body_content)
                else:
                    html_parts.append(main_html)
                html_parts.append('</div>')
            
            elif section['type'] == 'subreport':
                html_parts.append('<div class="subreport">')
                subreport_name = section['content']['name']
                parameters = section['content']['parameters']
                try:
                    subreport_html = self.subreport_manager.execute_subreport(subreport_name, parameters)
                    # Extract body content
                    subreport_html_str = subreport_html.decode('utf-8')
                    body_start = subreport_html_str.find('<body>')
                    body_end = subreport_html_str.find('</body>')
                    if body_start != -1 and body_end != -1:
                        body_content = subreport_html_str[body_start + 6:body_end]
                        html_parts.append(body_content)
                    else:
                        html_parts.append(subreport_html_str)
                except Exception as e:
                    html_parts.append(f'<p>Error rendering subreport: {e}</p>')
                html_parts.append('</div>')
            
            elif section['type'] == 'chart':
                html_parts.append('<div class="chart-section">')
                try:
                    chart_html = self.main_report.add_chart(
                        section['content']['type'],
                        'current',
                        section['content']['config']
                    )
                    if chart_html.startswith('data:image'):
                        html_parts.append(f'<img src="{chart_html}" alt="Chart" style="max-width: 100%;">')
                    else:
                        html_parts.append(chart_html)
                except Exception as e:
                    html_parts.append(f'<p>Error rendering chart: {e}</p>')
                html_parts.append('</div>')
            
            elif section['type'] == 'text':
                html_parts.append('<div class="text-section">')
                html_parts.append(f'<p>{section["content"]}</p>')
                html_parts.append('</div>')
            
            html_parts.append('</div>')  # Close section div
        
        # End HTML document
        html_parts.append("""
</body>
</html>
""")
        
        return ''.join(html_parts)
    
    def add_main_report_section(self, title: str = "Main Report"):
        """Add the main report as a section."""
        self.add_section('main', None, title)
    
    def get_section_count(self) -> int:
        """Get the number of sections."""
        return len(self.sections)
    
    def clear_sections(self):
        """Clear all sections."""
        self.sections.clear()