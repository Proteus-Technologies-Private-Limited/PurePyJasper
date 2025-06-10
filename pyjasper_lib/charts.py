"""
Chart and image support for PyJasper reports.
"""

import base64
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
import os
from .exceptions import RenderError


class ChartRenderer:
    """Handles chart generation for reports."""
    
    def __init__(self):
        self.chart_types = {
            'bar': self._create_bar_chart,
            'line': self._create_line_chart,
            'pie': self._create_pie_chart,
            'area': self._create_area_chart,
            'column': self._create_column_chart
        }
    
    def create_chart(self, chart_type: str, data: List[Dict[str, Any]], 
                    config: Dict[str, Any]) -> str:
        """Create a chart and return it as base64 encoded string."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            chart_func = self.chart_types.get(chart_type.lower())
            if not chart_func:
                raise RenderError(f"Unsupported chart type: {chart_type}")
            
            fig, ax = plt.subplots(figsize=(8, 6))
            chart_func(ax, data, config)
            
            # Save to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return f"data:image/png;base64,{image_base64}"
            
        except ImportError:
            # Fallback: create a simple HTML representation
            return self._create_html_chart(chart_type, data, config)
        except Exception as e:
            raise RenderError(f"Chart creation failed: {e}")
    
    def _create_bar_chart(self, ax, data: List[Dict[str, Any]], config: Dict[str, Any]):
        """Create a bar chart."""
        x_field = config.get('x_field', 'category')
        y_field = config.get('y_field', 'value')
        
        categories = [row.get(x_field, '') for row in data]
        values = [float(row.get(y_field, 0)) for row in data]
        
        ax.bar(categories, values)
        ax.set_title(config.get('title', 'Bar Chart'))
        ax.set_xlabel(config.get('x_label', x_field))
        ax.set_ylabel(config.get('y_label', y_field))
        
        # Rotate x-axis labels if needed
        if len(categories) > 5:
            ax.tick_params(axis='x', rotation=45)
    
    def _create_line_chart(self, ax, data: List[Dict[str, Any]], config: Dict[str, Any]):
        """Create a line chart."""
        x_field = config.get('x_field', 'category')
        y_field = config.get('y_field', 'value')
        
        x_values = [row.get(x_field, '') for row in data]
        y_values = [float(row.get(y_field, 0)) for row in data]
        
        ax.plot(x_values, y_values, marker='o')
        ax.set_title(config.get('title', 'Line Chart'))
        ax.set_xlabel(config.get('x_label', x_field))
        ax.set_ylabel(config.get('y_label', y_field))
        
        if len(x_values) > 5:
            ax.tick_params(axis='x', rotation=45)
    
    def _create_pie_chart(self, ax, data: List[Dict[str, Any]], config: Dict[str, Any]):
        """Create a pie chart."""
        label_field = config.get('label_field', 'category')
        value_field = config.get('value_field', 'value')
        
        labels = [row.get(label_field, '') for row in data]
        values = [float(row.get(value_field, 0)) for row in data]
        
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title(config.get('title', 'Pie Chart'))
    
    def _create_area_chart(self, ax, data: List[Dict[str, Any]], config: Dict[str, Any]):
        """Create an area chart."""
        x_field = config.get('x_field', 'category')
        y_field = config.get('y_field', 'value')
        
        x_values = range(len(data))
        y_values = [float(row.get(y_field, 0)) for row in data]
        x_labels = [row.get(x_field, '') for row in data]
        
        ax.fill_between(x_values, y_values, alpha=0.7)
        ax.set_title(config.get('title', 'Area Chart'))
        ax.set_xlabel(config.get('x_label', x_field))
        ax.set_ylabel(config.get('y_label', y_field))
        ax.set_xticks(x_values)
        ax.set_xticklabels(x_labels)
        
        if len(x_labels) > 5:
            ax.tick_params(axis='x', rotation=45)
    
    def _create_column_chart(self, ax, data: List[Dict[str, Any]], config: Dict[str, Any]):
        """Create a column chart (same as bar chart but vertical)."""
        self._create_bar_chart(ax, data, config)
    
    def _create_html_chart(self, chart_type: str, data: List[Dict[str, Any]], 
                          config: Dict[str, Any]) -> str:
        """Create a simple HTML representation of a chart when matplotlib is not available."""
        return f"""
        <div class="chart-placeholder" style="
            width: 400px; 
            height: 300px; 
            border: 2px dashed #ccc; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            background-color: #f9f9f9;
            margin: 10px 0;
        ">
            <div style="text-align: center;">
                <strong>{config.get('title', chart_type.title() + ' Chart')}</strong><br>
                <small>Chart rendering requires matplotlib</small><br>
                <small>Data points: {len(data)}</small>
            </div>
        </div>
        """


class ImageHandler:
    """Handles image processing for reports."""
    
    @staticmethod
    def load_image(image_path: str) -> str:
        """Load an image and return it as base64 encoded string."""
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Determine image format
            image_format = ImageHandler._get_image_format(image_path)
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            return f"data:image/{image_format};base64,{image_base64}"
            
        except Exception as e:
            raise RenderError(f"Failed to load image: {e}")
    
    @staticmethod
    def _get_image_format(image_path: str) -> str:
        """Determine image format from file extension."""
        ext = os.path.splitext(image_path)[1].lower()
        format_map = {
            '.jpg': 'jpeg',
            '.jpeg': 'jpeg',
            '.png': 'png',
            '.gif': 'gif',
            '.bmp': 'bmp',
            '.webp': 'webp'
        }
        return format_map.get(ext, 'png')
    
    @staticmethod
    def resize_image(image_data: bytes, max_width: int, max_height: int) -> bytes:
        """Resize an image while maintaining aspect ratio."""
        try:
            from PIL import Image
            
            img = Image.open(BytesIO(image_data))
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            output = BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            
            return output.getvalue()
            
        except ImportError:
            # If PIL is not available, return original data
            return image_data
        except Exception as e:
            raise RenderError(f"Image resize failed: {e}")
    
    @staticmethod
    def create_placeholder_image(width: int, height: int, text: str = "Image") -> str:
        """Create a placeholder image as base64 string."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a new image with light gray background
            img = Image.new('RGB', (width, height), color='#f0f0f0')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position (center)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw text
            draw.text((x, y), text, fill='#666666', font=font)
            
            # Convert to base64
            output = BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            
            image_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{image_base64}"
            
        except ImportError:
            # HTML placeholder if PIL is not available
            return f"""
            <div style="
                width: {width}px; 
                height: {height}px; 
                border: 1px solid #ddd; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                background-color: #f0f0f0;
                color: #666;
                font-family: Arial, sans-serif;
            ">
                {text}
            </div>
            """
        except Exception as e:
            raise RenderError(f"Placeholder image creation failed: {e}")


class FormattingUtils:
    """Utility functions for advanced formatting."""
    
    @staticmethod
    def format_currency(value: Any, currency_symbol: str = "$", decimal_places: int = 2) -> str:
        """Format a value as currency."""
        try:
            num_value = float(value)
            return f"{currency_symbol}{num_value:,.{decimal_places}f}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def format_percentage(value: Any, decimal_places: int = 1) -> str:
        """Format a value as percentage."""
        try:
            num_value = float(value) * 100
            return f"{num_value:.{decimal_places}f}%"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def format_date(value: Any, format_string: str = "%Y-%m-%d") -> str:
        """Format a date value."""
        try:
            from datetime import datetime
            
            if isinstance(value, str):
                # Try to parse common date formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        date_obj = datetime.strptime(value, fmt)
                        return date_obj.strftime(format_string)
                    except ValueError:
                        continue
            elif hasattr(value, 'strftime'):
                return value.strftime(format_string)
            
            return str(value)
        except Exception:
            return str(value)
    
    @staticmethod
    def format_number(value: Any, decimal_places: int = 2, thousands_separator: str = ",") -> str:
        """Format a number with thousands separator."""
        try:
            num_value = float(value)
            if thousands_separator:
                return f"{num_value:,.{decimal_places}f}"
            else:
                return f"{num_value:.{decimal_places}f}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def apply_conditional_formatting(value: Any, conditions: List[Dict[str, Any]]) -> Dict[str, str]:
        """Apply conditional formatting based on value conditions."""
        styles = {}
        
        for condition in conditions:
            condition_type = condition.get('type', 'equals')
            condition_value = condition.get('value')
            styles_to_apply = condition.get('styles', {})
            
            if FormattingUtils._check_condition(value, condition_type, condition_value):
                styles.update(styles_to_apply)
                break  # Apply first matching condition
        
        return styles
    
    @staticmethod
    def _check_condition(value: Any, condition_type: str, condition_value: Any) -> bool:
        """Check if a value meets a condition."""
        try:
            if condition_type == 'equals':
                return value == condition_value
            elif condition_type == 'greater_than':
                return float(value) > float(condition_value)
            elif condition_type == 'less_than':
                return float(value) < float(condition_value)
            elif condition_type == 'greater_equal':
                return float(value) >= float(condition_value)
            elif condition_type == 'less_equal':
                return float(value) <= float(condition_value)
            elif condition_type == 'contains':
                return str(condition_value).lower() in str(value).lower()
            elif condition_type == 'starts_with':
                return str(value).lower().startswith(str(condition_value).lower())
            elif condition_type == 'ends_with':
                return str(value).lower().endswith(str(condition_value).lower())
        except (ValueError, TypeError):
            return False
        
        return False