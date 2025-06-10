#!/usr/bin/env python3
"""
Example usage of the PyJasper library.

This script demonstrates the main features of the PyJasper library:
- Creating reports from JRXML files
- Database connectivity
- HTML and PDF rendering
- Programmatic report building
- Data processing and grouping
"""

import os
from pathlib import Path
from pyjasper_lib import JasperReport, ReportBuilder
from pyjasper_lib.database import DatabaseEngine
from pyjasper_lib.charts import ChartRenderer, FormattingUtils
from pyjasper_lib.subreports import TemplateManager, ReportComposer


def example_1_basic_report():
    """Example 1: Basic report generation from JRXML file."""
    print("=== Example 1: Basic Report Generation ===")
    
    # Use the existing sample JRXML file
    jrxml_path = "uploads/sample_employee_report.jrxml"
    
    if os.path.exists(jrxml_path):
        # Create report from file
        report = JasperReport(jrxml_path=jrxml_path)
        
        # Set up database connection
        report.set_database_connection("sqlite:///sample.db")
        
        # Generate HTML report
        html_content = report.generate_html()
        
        # Save the report
        with open("output/employee_report.html", "wb") as f:
            f.write(html_content)
        
        print("HTML report generated: output/employee_report.html")
        
        # Generate PDF report
        try:
            pdf_content = report.generate_pdf()
            with open("output/employee_report.pdf", "wb") as f:
                f.write(pdf_content)
            print("PDF report generated: output/employee_report.pdf")
        except Exception as e:
            print(f"PDF generation failed: {e}")
    else:
        print(f"JRXML file not found: {jrxml_path}")


def example_2_programmatic_report():
    """Example 2: Building reports programmatically."""
    print("\n=== Example 2: Programmatic Report Building ===")
    
    # Create a report builder
    builder = ReportBuilder("Sales Report")
    builder.set_title("Monthly Sales Report")
    builder.set_query("SELECT product_name, sales_amount, sale_date FROM sales")
    
    # Add fields
    builder.add_field("product_name", "java.lang.String")
    builder.add_field("sales_amount", "java.math.BigDecimal")
    builder.add_field("sale_date", "java.lang.String")
    
    # Add column headers
    builder.add_column_header("Product", 200)
    builder.add_column_header("Amount", 100)
    builder.add_column_header("Date", 100)
    
    # Build the report
    report = builder.build()
    
    # Set sample data (since we don't have the actual database)
    sample_data = [
        {"product_name": "Widget A", "sales_amount": 150.00, "sale_date": "2024-01-15"},
        {"product_name": "Widget B", "sales_amount": 200.50, "sale_date": "2024-01-16"},
        {"product_name": "Widget C", "sales_amount": 75.25, "sale_date": "2024-01-17"},
    ]
    report.set_data(sample_data)
    
    # Generate and save HTML report
    html_content = report.generate_html()
    os.makedirs("output", exist_ok=True)
    with open("output/sales_report.html", "wb") as f:
        f.write(html_content)
    
    print("Programmatic report generated: output/sales_report.html")


def example_3_data_processing():
    """Example 3: Data processing and formatting."""
    print("\n=== Example 3: Data Processing and Formatting ===")
    
    # Sample sales data
    sales_data = [
        {"region": "North", "salesperson": "Alice", "amount": 15000.50, "date": "2024-01-15"},
        {"region": "North", "salesperson": "Bob", "amount": 12000.75, "date": "2024-01-16"},
        {"region": "South", "salesperson": "Charlie", "amount": 18000.25, "date": "2024-01-17"},
        {"region": "South", "salesperson": "David", "amount": 14000.00, "date": "2024-01-18"},
        {"region": "East", "salesperson": "Eve", "amount": 16000.30, "date": "2024-01-19"},
    ]
    
    # Process data
    from pyjasper_lib.database import DataProcessor
    processor = DataProcessor(sales_data)
    
    # Group by region
    regions = processor.group_by("region")
    print("Sales by Region:")
    for region, sales in regions.items():
        total = processor.calculate_sum("amount", sales)
        print(f"  {region}: {FormattingUtils.format_currency(total)}")
    
    # Calculate overall totals
    total_sales = processor.calculate_sum("amount")
    avg_sale = processor.calculate_average("amount")
    
    print(f"\nTotal Sales: {FormattingUtils.format_currency(total_sales)}")
    print(f"Average Sale: {FormattingUtils.format_currency(avg_sale)}")


def example_4_chart_generation():
    """Example 4: Chart generation."""
    print("\n=== Example 4: Chart Generation ===")
    
    try:
        chart_renderer = ChartRenderer()
        
        # Sample data for chart
        chart_data = [
            {"month": "Jan", "sales": 15000},
            {"month": "Feb", "sales": 18000},
            {"month": "Mar", "sales": 12000},
            {"month": "Apr", "sales": 20000},
            {"month": "May", "sales": 22000},
        ]
        
        # Create bar chart
        chart_config = {
            "title": "Monthly Sales",
            "x_field": "month",
            "y_field": "sales",
            "x_label": "Month",
            "y_label": "Sales ($)"
        }
        
        chart_html = chart_renderer.create_chart("bar", chart_data, chart_config)
        
        # Create HTML page with chart
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sales Chart</title>
        </head>
        <body>
            <h1>Monthly Sales Chart</h1>
            {chart_html if not chart_html.startswith('data:image') else f'<img src="{chart_html}" alt="Sales Chart">'}
        </body>
        </html>
        """
        
        os.makedirs("output", exist_ok=True)
        with open("output/sales_chart.html", "w") as f:
            f.write(html_content)
        
        print("Chart generated: output/sales_chart.html")
        
    except Exception as e:
        print(f"Chart generation failed: {e}")


def example_5_templates():
    """Example 5: Using templates."""
    print("\n=== Example 5: Template Usage ===")
    
    try:
        # Create template manager
        template_manager = TemplateManager("templates")
        
        # Create a simple template
        template_jrxml = '''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports"
              name="{{REPORT_NAME}}" pageWidth="595" pageHeight="842">
    
    <field name="name" class="java.lang.String"/>
    <field name="value" class="java.lang.String"/>
    
    <title>
        <band height="60">
            <staticText>
                <reportElement x="0" y="20" width="555" height="30"/>
                <textElement textAlignment="Center">
                    <font size="18" isBold="true"/>
                </textElement>
                <text><![CDATA[{{TITLE}}]]></text>
            </staticText>
        </band>
    </title>
    
    <detail>
        <band height="20">
            <textField>
                <reportElement x="0" y="0" width="200" height="20"/>
                <textFieldExpression><![CDATA[$F{name}]]></textFieldExpression>
            </textField>
            <textField>
                <reportElement x="200" y="0" width="200" height="20"/>
                <textFieldExpression><![CDATA[$F{value}]]></textFieldExpression>
            </textField>
        </band>
    </detail>
</jasperReport>'''
        
        # Save template
        template_manager.save_template("generic_report", template_jrxml)
        
        # Create report from template
        replacements = {
            "{{REPORT_NAME}}": "CustomerReport",
            "{{TITLE}}": "Customer Information Report"
        }
        
        report = template_manager.create_report_from_template("generic_report", replacements)
        
        # Set sample data
        customer_data = [
            {"name": "John Doe", "value": "john@example.com"},
            {"name": "Jane Smith", "value": "jane@example.com"},
        ]
        report.set_data(customer_data)
        
        # Generate report
        html_content = report.generate_html()
        os.makedirs("output", exist_ok=True)
        with open("output/customer_report.html", "wb") as f:
            f.write(html_content)
        
        print("Template-based report generated: output/customer_report.html")
        print(f"Available templates: {template_manager.list_templates()}")
        
    except Exception as e:
        print(f"Template example failed: {e}")


def example_6_validation():
    """Example 6: Report validation."""
    print("\n=== Example 6: Report Validation ===")
    
    # Valid JRXML
    valid_jrxml = '''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports" name="ValidReport">
    <field name="test_field" class="java.lang.String"/>
    <detail>
        <band height="20">
            <textField>
                <reportElement x="0" y="0" width="100" height="20"/>
                <textFieldExpression><![CDATA[$F{test_field}]]></textFieldExpression>
            </textField>
        </band>
    </detail>
</jasperReport>'''
    
    # Invalid JRXML (references non-existent field)
    invalid_jrxml = '''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports" name="InvalidReport">
    <field name="test_field" class="java.lang.String"/>
    <detail>
        <band height="20">
            <textField>
                <reportElement x="0" y="0" width="100" height="20"/>
                <textFieldExpression><![CDATA[$F{nonexistent_field}]]></textFieldExpression>
            </textField>
        </band>
    </detail>
</jasperReport>'''
    
    print("Validating valid JRXML:")
    try:
        valid_report = JasperReport(jrxml_content=valid_jrxml)
        validation = valid_report.validate_report()
        print(f"  Valid: {validation['valid']}")
        print(f"  Issues: {validation['issues']}")
        print(f"  Warnings: {validation['warnings']}")
    except Exception as e:
        print(f"  Validation failed: {e}")
    
    print("\nValidating invalid JRXML:")
    try:
        invalid_report = JasperReport(jrxml_content=invalid_jrxml)
        validation = invalid_report.validate_report()
        print(f"  Valid: {validation['valid']}")
        print(f"  Issues: {validation['issues']}")
        print(f"  Warnings: {validation['warnings']}")
    except Exception as e:
        print(f"  Validation failed: {e}")


def main():
    """Run all examples."""
    print("PyJasper Library Examples")
    print("=" * 50)
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Run examples
    example_1_basic_report()
    example_2_programmatic_report()
    example_3_data_processing()
    example_4_chart_generation()
    example_5_templates()
    example_6_validation()
    
    print("\n" + "=" * 50)
    print("All examples completed!")
    print("Check the 'output' directory for generated reports.")


if __name__ == "__main__":
    main()