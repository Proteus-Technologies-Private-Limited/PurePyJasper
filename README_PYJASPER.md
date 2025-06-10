# PyJasper - Python Jasper Reports Library

A comprehensive Python library that implements all the functionality of JasperReports in pure Python, eliminating the need for Java dependencies.

## Features

### Core Functionality
- **JRXML Parsing**: Complete parsing and processing of JRXML report definitions
- **SQL Execution**: Multi-database support (SQLite, MySQL, PostgreSQL)
- **HTML Rendering**: Professional HTML report generation with CSS styling
- **PDF Rendering**: High-quality PDF output using ReportLab
- **Data Processing**: Grouping, aggregation, and sorting capabilities

### Advanced Features
- **Charts & Graphs**: Bar, line, pie, and area charts using Matplotlib
- **Image Support**: Image embedding and processing with Pillow
- **Subreports**: Support for nested reports and cross-references
- **Templates**: Reusable report templates with parameter substitution
- **Expressions**: JasperReports expression evaluation
- **Formatting**: Currency, percentage, date, and number formatting
- **Validation**: Report definition validation and error checking

## Installation

```bash
# Basic installation
pip install -r requirements.txt

# Optional dependencies for enhanced features
pip install matplotlib  # For chart generation
pip install Pillow      # For image processing
pip install mysql-connector-python  # For MySQL support
pip install psycopg2    # For PostgreSQL support
```

## Quick Start

### 1. Basic Report Generation

```python
from pyjasper_lib import JasperReport

# Create report from JRXML file
report = JasperReport(jrxml_path="my_report.jrxml")

# Set database connection
report.set_database_connection("sqlite:///mydata.db")

# Generate HTML report
html_content = report.generate_html()
with open("report.html", "wb") as f:
    f.write(html_content)

# Generate PDF report
pdf_content = report.generate_pdf()
with open("report.pdf", "wb") as f:
    f.write(pdf_content)
```

### 2. Programmatic Report Building

```python
from pyjasper_lib import ReportBuilder

# Build report programmatically
builder = ReportBuilder("Sales Report")
builder.set_title("Monthly Sales Report")
builder.set_query("SELECT product, amount, date FROM sales")
builder.add_field("product", "java.lang.String")
builder.add_field("amount", "java.math.BigDecimal")
builder.add_field("date", "java.lang.String")

# Create and generate report
report = builder.build()
report.set_database_connection("sqlite:///sales.db")
html_content = report.generate_html()
```

### 3. Working with Data

```python
from pyjasper_lib.database import DataProcessor

# Process data
data = [
    {"region": "North", "sales": 15000},
    {"region": "South", "sales": 12000},
    {"region": "North", "sales": 18000}
]

processor = DataProcessor(data)
groups = processor.group_by("region")
total_sales = processor.calculate_sum("sales")
```

### 4. Chart Generation

```python
from pyjasper_lib.charts import ChartRenderer

renderer = ChartRenderer()
chart_data = [
    {"month": "Jan", "sales": 15000},
    {"month": "Feb", "sales": 18000}
]

config = {
    "title": "Monthly Sales",
    "x_field": "month",
    "y_field": "sales"
}

chart_image = renderer.create_chart("bar", chart_data, config)
```

## Library Structure

```
pyjasper_lib/
├── __init__.py          # Main exports
├── core.py              # JasperReport main class
├── parsers.py           # JRXML parsing functionality
├── database.py          # Database connectivity and data processing
├── renderers.py         # HTML and PDF rendering
├── charts.py            # Chart generation and image handling
├── subreports.py        # Subreport and template management
└── exceptions.py        # Exception classes
```

## API Reference

### JasperReport Class

The main class for report generation.

```python
class JasperReport:
    def __init__(self, jrxml_path=None, jrxml_content=None)
    def set_database_connection(self, connection_string)
    def set_parameters(self, parameters)
    def set_data(self, data)
    def execute_query(self)
    def generate_html(self) -> bytes
    def generate_pdf(self) -> bytes
    def save_report(self, output_path, format='html')
    def get_report_info(self) -> dict
    def validate_report(self) -> dict
    def preview_data(self, limit=10) -> list
```

### ReportBuilder Class

For programmatic report creation.

```python
class ReportBuilder:
    def __init__(self, name="Generated Report")
    def add_field(self, name, field_type="java.lang.String")
    def set_query(self, query)
    def set_title(self, title)
    def set_page_size(self, width, height)
    def set_margins(self, left, right, top, bottom)
    def add_column_header(self, text, width)
    def build() -> JasperReport
```

### DatabaseEngine Class

For database connectivity.

```python
class DatabaseEngine:
    def __init__(self, connection_string)
    def connect()
    def execute_query(self, query, parameters=None) -> list
    def get_tables() -> list
    def get_table_schema(self, table_name) -> list
    def test_connection() -> bool
```

### DataProcessor Class

For data processing and aggregation.

```python
class DataProcessor:
    def __init__(self, data)
    def group_by(self, field) -> dict
    def calculate_sum(self, field) -> float
    def calculate_average(self, field) -> float
    def calculate_count() -> int
    def sort_by(self, fields, ascending=True) -> list
```

## Database Support

### Connection Strings

```python
# SQLite
"sqlite:///path/to/database.db"

# MySQL
"mysql://username:password@host:port/database"

# PostgreSQL
"postgresql://username:password@host:port/database"
```

### Supported Operations

- SELECT queries with parameters
- Joins and subqueries
- Aggregation functions
- Sorting and filtering
- Schema introspection

## Report Elements

### Supported JRXML Elements

- **jasperReport**: Root element with page layout
- **queryString**: SQL query definition
- **field**: Data field definitions
- **variable**: Calculated variables
- **group**: Data grouping
- **band**: Report sections (title, detail, summary, etc.)
- **staticText**: Static text elements
- **textField**: Dynamic text with expressions
- **reportElement**: Element positioning and sizing

### Expression Support

```xml
<!-- Field references -->
$F{field_name}

<!-- Variable references -->
$V{variable_name}

<!-- Parameter references -->
$P{parameter_name}

<!-- Built-in variables -->
$V{PAGE_NUMBER}
$V{PAGE_COUNT}
```

## Formatting

### Currency Formatting

```python
from pyjasper_lib.charts import FormattingUtils

FormattingUtils.format_currency(1234.56)  # "$1,234.56"
FormattingUtils.format_currency(1000, "€", 0)  # "€1,000"
```

### Date Formatting

```python
FormattingUtils.format_date("2024-01-15", "%B %d, %Y")  # "January 15, 2024"
```

### Number Formatting

```python
FormattingUtils.format_number(1234.5678, 2)  # "1,234.57"
FormattingUtils.format_percentage(0.1234)    # "12.3%"
```

## Error Handling

The library provides specific exception types:

```python
from pyjasper_lib.exceptions import (
    JasperError,           # Base exception
    JRXMLParseError,       # JRXML parsing errors
    DatabaseError,         # Database connectivity errors
    RenderError,           # Report rendering errors
    ExpressionError,       # Expression evaluation errors
    ParameterError         # Parameter processing errors
)
```

## Integration with Flask App

The library includes integration with the existing Flask application:

```python
from pyjasper_lib_integration import pyjasper_integration

# Generate report
content, error = pyjasper_integration.generate_report(
    jrxml_content=jrxml_text,
    connection_string=db_connection,
    output_format='html'
)

# Validate JRXML
validation = pyjasper_integration.validate_jrxml(jrxml_content)

# Preview data
data, error = pyjasper_integration.preview_data(
    jrxml_content=jrxml_text,
    connection_string=db_connection
)
```

## Testing

Run the comprehensive test suite:

```bash
python test_pyjasper.py
```

The test suite covers:
- JRXML parsing
- Database connectivity
- Data processing
- Report generation
- Chart creation
- Template management
- Validation

## Examples

See `example_usage.py` for comprehensive examples demonstrating:

1. Basic report generation
2. Programmatic report building
3. Data processing and formatting
4. Chart generation
5. Template usage
6. Report validation

## Performance Considerations

- **Memory Usage**: Large datasets are processed efficiently using generators
- **Database Connections**: Connection pooling for multi-report generation
- **Caching**: Template and compiled report caching
- **Streaming**: Large PDF generation uses streaming output

## Limitations

- **Complex Layouts**: Some advanced JasperReports layout features may have limited support
- **Java Expressions**: Complex Java expressions may need Python equivalents
- **Fonts**: PDF font selection limited to built-in fonts without additional configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite
5. Submit a pull request

## License

This library is released under the same license as the main project.

## Compatibility

- Python 3.7+
- All major operating systems
- Compatible with existing JasperReports JRXML files
- No Java runtime required