"""
Comprehensive test suite for PyJasper library.
"""

import unittest
import tempfile
import os
import sqlite3
from pathlib import Path

from pyjasper_lib import JasperReport, ReportBuilder
from pyjasper_lib.parsers import JRXMLParser
from pyjasper_lib.database import DatabaseEngine, DataProcessor
from pyjasper_lib.renderers import HTMLRenderer, PDFRenderer
from pyjasper_lib.charts import ChartRenderer, ImageHandler, FormattingUtils
from pyjasper_lib.subreports import SubreportManager, CrossReferenceManager, TemplateManager, ReportComposer
from pyjasper_lib.exceptions import JasperError, JRXMLParseError, DatabaseError


class TestJRXMLParser(unittest.TestCase):
    """Test JRXML parsing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_jrxml = '''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              name="TestReport" pageWidth="595" pageHeight="842"
              columnWidth="555" leftMargin="20" rightMargin="20"
              topMargin="20" bottomMargin="20">

    <queryString>
        <![CDATA[SELECT id, name, amount FROM test_table ORDER BY name]]>
    </queryString>

    <field name="id" class="java.lang.Integer"/>
    <field name="name" class="java.lang.String"/>
    <field name="amount" class="java.math.BigDecimal"/>

    <variable name="totalAmount" class="java.math.BigDecimal" calculation="Sum">
        <variableExpression><![CDATA[$F{amount}]]></variableExpression>
    </variable>

    <title>
        <band height="60">
            <staticText>
                <reportElement x="0" y="20" width="555" height="30"/>
                <textElement textAlignment="Center">
                    <font size="18" isBold="true"/>
                </textElement>
                <text><![CDATA[Test Report]]></text>
            </staticText>
        </band>
    </title>

    <detail>
        <band height="20">
            <textField>
                <reportElement x="0" y="0" width="100" height="20"/>
                <textElement/>
                <textFieldExpression><![CDATA[$F{id}]]></textFieldExpression>
            </textField>
            <textField>
                <reportElement x="100" y="0" width="200" height="20"/>
                <textElement/>
                <textFieldExpression><![CDATA[$F{name}]]></textFieldExpression>
            </textField>
            <textField pattern="¤#,##0.00">
                <reportElement x="300" y="0" width="100" height="20"/>
                <textElement textAlignment="Right"/>
                <textFieldExpression><![CDATA[$F{amount}]]></textFieldExpression>
            </textField>
        </band>
    </detail>

</jasperReport>'''
    
    def test_parse_basic_jrxml(self):
        """Test parsing basic JRXML content."""
        parser = JRXMLParser()
        report_def = parser.parse(self.sample_jrxml)
        
        self.assertEqual(report_def.name, "TestReport")
        self.assertEqual(report_def.page_width, 595)
        self.assertEqual(report_def.page_height, 842)
        self.assertEqual(len(report_def.fields), 3)
        self.assertEqual(len(report_def.variables), 1)
        self.assertIn('title', report_def.bands)
        self.assertIn('detail', report_def.bands)
    
    def test_parse_query(self):
        """Test query extraction."""
        parser = JRXMLParser()
        report_def = parser.parse(self.sample_jrxml)
        
        expected_query = "SELECT id, name, amount FROM test_table ORDER BY name"
        self.assertEqual(report_def.query.strip(), expected_query)
    
    def test_parse_fields(self):
        """Test field parsing."""
        parser = JRXMLParser()
        report_def = parser.parse(self.sample_jrxml)
        
        field_names = [f.name for f in report_def.fields]
        self.assertIn('id', field_names)
        self.assertIn('name', field_names)
        self.assertIn('amount', field_names)
        
        id_field = next(f for f in report_def.fields if f.name == 'id')
        self.assertEqual(id_field.class_name, 'java.lang.Integer')
    
    def test_parse_variables(self):
        """Test variable parsing."""
        parser = JRXMLParser()
        report_def = parser.parse(self.sample_jrxml)
        
        self.assertEqual(len(report_def.variables), 1)
        total_var = report_def.variables[0]
        self.assertEqual(total_var.name, 'totalAmount')
        self.assertEqual(total_var.calculation, 'Sum')
    
    def test_invalid_xml(self):
        """Test handling of invalid XML."""
        parser = JRXMLParser()
        invalid_xml = "<invalid><unclosed"
        
        with self.assertRaises(JRXMLParseError):
            parser.parse(invalid_xml)


class TestDatabaseEngine(unittest.TestCase):
    """Test database functionality."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Create test database
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                amount REAL DEFAULT 0.0
            )
        ''')
        cursor.execute("INSERT INTO test_table (name, amount) VALUES ('Alice', 100.50)")
        cursor.execute("INSERT INTO test_table (name, amount) VALUES ('Bob', 250.75)")
        cursor.execute("INSERT INTO test_table (name, amount) VALUES ('Charlie', 75.25)")
        conn.commit()
        conn.close()
        
        self.connection_string = f"sqlite:///{self.temp_db.name}"
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_connection(self):
        """Test database connection."""
        engine = DatabaseEngine(self.connection_string)
        self.assertTrue(engine.test_connection())
    
    def test_execute_query(self):
        """Test query execution."""
        engine = DatabaseEngine(self.connection_string)
        results = engine.execute_query("SELECT * FROM test_table ORDER BY name")
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['name'], 'Alice')
        self.assertEqual(results[1]['name'], 'Bob')
        self.assertEqual(results[2]['name'], 'Charlie')
    
    def test_get_tables(self):
        """Test getting table list."""
        engine = DatabaseEngine(self.connection_string)
        tables = engine.get_tables()
        
        self.assertIn('test_table', tables)
    
    def test_get_table_schema(self):
        """Test getting table schema."""
        engine = DatabaseEngine(self.connection_string)
        schema = engine.get_table_schema('test_table')
        
        column_names = [col['name'] for col in schema]
        self.assertIn('id', column_names)
        self.assertIn('name', column_names)
        self.assertIn('amount', column_names)


class TestDataProcessor(unittest.TestCase):
    """Test data processing functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data = [
            {'department': 'Sales', 'employee': 'Alice', 'salary': 50000},
            {'department': 'Sales', 'employee': 'Bob', 'salary': 55000},
            {'department': 'IT', 'employee': 'Charlie', 'salary': 60000},
            {'department': 'IT', 'employee': 'David', 'salary': 65000},
        ]
    
    def test_group_by(self):
        """Test grouping functionality."""
        processor = DataProcessor(self.test_data)
        groups = processor.group_by('department')
        
        self.assertEqual(len(groups), 2)
        self.assertIn('Sales', groups)
        self.assertIn('IT', groups)
        self.assertEqual(len(groups['Sales']), 2)
        self.assertEqual(len(groups['IT']), 2)
    
    def test_calculate_sum(self):
        """Test sum calculation."""
        processor = DataProcessor(self.test_data)
        total_salary = processor.calculate_sum('salary')
        
        self.assertEqual(total_salary, 230000)
    
    def test_calculate_average(self):
        """Test average calculation."""
        processor = DataProcessor(self.test_data)
        avg_salary = processor.calculate_average('salary')
        
        self.assertEqual(avg_salary, 57500)
    
    def test_sort_by(self):
        """Test sorting functionality."""
        processor = DataProcessor(self.test_data)
        sorted_data = processor.sort_by('salary')
        
        self.assertEqual(sorted_data[0]['employee'], 'Alice')
        self.assertEqual(sorted_data[-1]['employee'], 'David')


class TestJasperReport(unittest.TestCase):
    """Test main JasperReport functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_jrxml = '''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports"
              name="TestReport" pageWidth="595" pageHeight="842">
    <field name="name" class="java.lang.String"/>
    <field name="amount" class="java.math.BigDecimal"/>
    
    <title>
        <band height="60">
            <staticText>
                <reportElement x="0" y="20" width="555" height="30"/>
                <text><![CDATA[Test Report]]></text>
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
                <reportElement x="200" y="0" width="100" height="20"/>
                <textFieldExpression><![CDATA[$F{amount}]]></textFieldExpression>
            </textField>
        </band>
    </detail>
</jasperReport>'''
        
        self.test_data = [
            {'name': 'Item 1', 'amount': 100.50},
            {'name': 'Item 2', 'amount': 250.75},
        ]
    
    def test_create_report(self):
        """Test creating report from JRXML content."""
        report = JasperReport(jrxml_content=self.sample_jrxml)
        self.assertIsNotNone(report.report_def)
        self.assertEqual(report.report_def.name, "TestReport")
    
    def test_set_data(self):
        """Test setting data directly."""
        report = JasperReport(jrxml_content=self.sample_jrxml)
        report.set_data(self.test_data)
        
        self.assertEqual(len(report.data), 2)
        self.assertEqual(report.data[0]['name'], 'Item 1')
    
    def test_generate_html(self):
        """Test HTML generation."""
        report = JasperReport(jrxml_content=self.sample_jrxml)
        report.set_data(self.test_data)
        
        html_content = report.generate_html()
        self.assertIsInstance(html_content, bytes)
        
        html_str = html_content.decode('utf-8')
        self.assertIn('Test Report', html_str)
        self.assertIn('Item 1', html_str)
        self.assertIn('Item 2', html_str)
    
    def test_generate_pdf(self):
        """Test PDF generation."""
        report = JasperReport(jrxml_content=self.sample_jrxml)
        report.set_data(self.test_data)
        
        pdf_content = report.generate_pdf()
        self.assertIsInstance(pdf_content, bytes)
        self.assertTrue(len(pdf_content) > 0)
    
    def test_get_report_info(self):
        """Test getting report information."""
        report = JasperReport(jrxml_content=self.sample_jrxml)
        info = report.get_report_info()
        
        self.assertEqual(info['name'], 'TestReport')
        self.assertEqual(len(info['fields']), 2)
        self.assertIn('title', info['bands'])
        self.assertIn('detail', info['bands'])
    
    def test_validate_report(self):
        """Test report validation."""
        report = JasperReport(jrxml_content=self.sample_jrxml)
        validation = report.validate_report()
        
        self.assertIn('valid', validation)
        self.assertIn('issues', validation)
        self.assertIn('warnings', validation)


class TestReportBuilder(unittest.TestCase):
    """Test programmatic report building."""
    
    def test_build_simple_report(self):
        """Test building a simple report."""
        builder = ReportBuilder("Generated Report")
        builder.add_field("name", "java.lang.String")
        builder.add_field("value", "java.lang.Integer")
        builder.set_title("My Generated Report")
        builder.set_query("SELECT name, value FROM my_table")
        
        jrxml = builder.build_jrxml()
        self.assertIn("Generated Report", jrxml)
        self.assertIn("My Generated Report", jrxml)
        self.assertIn("SELECT name, value FROM my_table", jrxml)
        
        # Test building actual report
        report = builder.build()
        self.assertIsNotNone(report.report_def)


class TestChartRenderer(unittest.TestCase):
    """Test chart rendering functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.chart_data = [
            {'category': 'A', 'value': 10},
            {'category': 'B', 'value': 20},
            {'category': 'C', 'value': 15},
        ]
    
    def test_create_chart(self):
        """Test chart creation."""
        renderer = ChartRenderer()
        config = {
            'title': 'Test Chart',
            'x_field': 'category',
            'y_field': 'value'
        }
        
        # This should work even without matplotlib (falls back to HTML)
        result = renderer.create_chart('bar', self.chart_data, config)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


class TestFormattingUtils(unittest.TestCase):
    """Test formatting utilities."""
    
    def test_format_currency(self):
        """Test currency formatting."""
        result = FormattingUtils.format_currency(1234.56)
        self.assertEqual(result, "$1,234.56")
        
        result = FormattingUtils.format_currency(1000, "€", 0)
        self.assertEqual(result, "€1,000")
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        result = FormattingUtils.format_percentage(0.1234)
        self.assertEqual(result, "12.3%")
        
        result = FormattingUtils.format_percentage(0.5, 0)
        self.assertEqual(result, "50%")
    
    def test_format_number(self):
        """Test number formatting."""
        result = FormattingUtils.format_number(1234.5678, 2)
        self.assertEqual(result, "1,234.57")
        
        result = FormattingUtils.format_number(1000, 0, "")
        self.assertEqual(result, "1000")


class TestSubreportManager(unittest.TestCase):
    """Test subreport functionality."""
    
    def setUp(self):
        """Set up test reports."""
        self.main_jrxml = '''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports" name="MainReport">
    <field name="id" class="java.lang.Integer"/>
    <title><band height="30"><staticText><reportElement x="0" y="0" width="100" height="30"/><text><![CDATA[Main Report]]></text></staticText></band></title>
</jasperReport>'''
        
        self.sub_jrxml = '''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports" name="SubReport">
    <field name="detail" class="java.lang.String"/>
    <title><band height="30"><staticText><reportElement x="0" y="0" width="100" height="30"/><text><![CDATA[Sub Report]]></text></staticText></band></title>
</jasperReport>'''
    
    def test_add_subreport(self):
        """Test adding subreports."""
        main_report = JasperReport(jrxml_content=self.main_jrxml)
        manager = SubreportManager(main_report)
        
        manager.add_subreport('sub1', jrxml_content=self.sub_jrxml)
        
        self.assertIn('sub1', manager.subreports)
        self.assertEqual(len(manager.get_subreport_names()), 1)


class TestTemplateManager(unittest.TestCase):
    """Test template management."""
    
    def setUp(self):
        """Set up test template directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.template_manager = TemplateManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_template(self):
        """Test saving and loading templates."""
        template_content = '''<?xml version="1.0"?>
<jasperReport name="Template">
    <title><band height="30"><staticText><text><![CDATA[Template Report]]></text></staticText></band></title>
</jasperReport>'''
        
        self.template_manager.save_template('test_template', template_content)
        
        self.assertIn('test_template', self.template_manager.list_templates())
        
        loaded_content = self.template_manager.get_template('test_template')
        self.assertEqual(loaded_content, template_content)
    
    def test_create_report_from_template(self):
        """Test creating reports from templates."""
        template_content = '''<?xml version="1.0"?>
<jasperReport name="{{REPORT_NAME}}">
    <title><band height="30"><staticText><text><![CDATA[{{TITLE}}]]></text></staticText></band></title>
</jasperReport>'''
        
        self.template_manager.save_template('parametric_template', template_content)
        
        replacements = {
            '{{REPORT_NAME}}': 'MyReport',
            '{{TITLE}}': 'Custom Report Title'
        }
        
        report = self.template_manager.create_report_from_template('parametric_template', replacements)
        
        self.assertIsNotNone(report.report_def)
        self.assertEqual(report.report_def.name, 'MyReport')


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestJRXMLParser,
        TestDatabaseEngine,
        TestDataProcessor,
        TestJasperReport,
        TestReportBuilder,
        TestChartRenderer,
        TestFormattingUtils,
        TestSubreportManager,
        TestTemplateManager
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")