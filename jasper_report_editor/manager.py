import json
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from flask import current_app

from utils.llm_client import LLMClient
from config import db
from .models import DatabaseConnection
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyjasper_lib_integration import pyjasper_integration

SETTINGS_DIR = Path('settings')
CONNECTION_FILE = SETTINGS_DIR / 'database_connections.json'


class JasperManager:
    def __init__(self):
        SETTINGS_DIR.mkdir(exist_ok=True)
        if not CONNECTION_FILE.exists():
            with open(CONNECTION_FILE, 'w') as f:
                json.dump({}, f)
        self.llm = LLMClient()

    def load_connections(self):
        connections = DatabaseConnection.query.filter_by(is_active=True).all()
        return {conn.name: conn.connection_string for conn in connections}

    def save_connection(self, name, database_type, host=None, port=None, 
                       database_name=None, username=None, password=None, 
                       connection_string=None):
        if not connection_string:
            if database_type == 'sqlite':
                connection_string = f'sqlite:///{database_name}'
            elif database_type == 'mysql':
                connection_string = f'mysql://{username}:{password}@{host}:{port}/{database_name}'
            elif database_type == 'postgresql':
                connection_string = f'postgresql://{username}:{password}@{host}:{port}/{database_name}'
            else:
                raise ValueError(f"Unsupported database type: {database_type}")
        
        existing = DatabaseConnection.query.filter_by(name=name).first()
        if existing:
            existing.database_type = database_type
            existing.host = host
            existing.port = port
            existing.database_name = database_name
            existing.username = username
            existing.password = password
            existing.connection_string = connection_string
        else:
            connection = DatabaseConnection(
                name=name,
                database_type=database_type,
                host=host,
                port=port,
                database_name=database_name,
                username=username,
                password=password,
                connection_string=connection_string
            )
            db.session.add(connection)
        
        db.session.commit()
        return connection_string

    def create_sample_db(self, db_path='sample.db'):
        """Create a sample sqlite database using LLM to generate schema."""
        import sqlite3
        import os
        
        # Remove existing database file if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ask LLM for simple example tables
        prompt = (
            "Create SQL statements to generate a sample schema with two tables:"
            " customers(id integer primary key, name text) and orders(id integer"
            " primary key, customer_id integer, amount real)."
        )
        sql = self.llm.getcompletion(prompt)
        
        for stmt in sql.split(';'):
            stmt = stmt.strip()
            if stmt:
                try:
                    cursor.execute(stmt)
                except sqlite3.Error as e:
                    # Log the error but continue with other statements
                    print(f"SQL execution error: {e}")
                    continue
                    
        conn.commit()
        conn.close()
        self.save_connection('sample', 'sqlite', database_name=db_path)
        return db_path

    def regenerate_jrxml(self, prompt, image=None):
        """Return new jrxml text from LLM based on prompt and optional image."""
        if image:
            prompt = f"{prompt}\nImage info: {image}"
        return self.llm.getcompletion(prompt)
    
    def parse_jrxml_for_preview(self, jrxml_content, connection_string):
        """Generate exact JRXML preview using PyJasper library."""
        try:
            if not jrxml_content or not jrxml_content.strip():
                return "<div class='alert alert-warning'>No JRXML content provided</div>"
            
            # Use PyJasper library to generate the preview
            content, error = pyjasper_integration.generate_report(
                jrxml_content=jrxml_content,
                connection_string=connection_string,
                output_format='html'
            )
            
            if error:
                return f"<div class='alert alert-danger'>Report generation error: {error}</div>"
            
            if content:
                # Extract body content from the generated HTML
                html_str = content.decode('utf-8')
                
                # Remove the fallback notice if present
                import re
                html_str = re.sub(r'<div class="fallback-notice">.*?</div>', '', html_str, flags=re.DOTALL)
                
                # Extract the report container content
                body_start = html_str.find('<div class="report-container">')
                body_end = html_str.find('</div>', body_start) + 6 if body_start != -1 else -1
                
                if body_start != -1 and body_end != -1:
                    return html_str[body_start:body_end]
                else:
                    # If no report container found, extract body content
                    body_start = html_str.find('<body>')
                    body_end = html_str.find('</body>')
                    if body_start != -1 and body_end != -1:
                        return html_str[body_start + 6:body_end]
                    else:
                        return html_str
            
            return "<div class='alert alert-warning'>No content generated</div>"
            
        except Exception as e:
            print(f"Preview generation error: {e}")
            return f"<div class='alert alert-danger'>Preview generation error: {str(e)}</div>"
    
    
    def get_sample_reports(self):
        """Get list of available sample reports."""
        return [
            {'id': 'customer_orders', 'name': 'Customer Orders Report'},
            {'id': 'customer_summary', 'name': 'Customer Summary Report'},
            {'id': 'orders_by_date', 'name': 'Orders by Date Report'}
        ]
    
    def generate_sample_jrxml(self, report_id='customer_orders'):
        """Generate a sample JRXML file for the sample database."""
        if report_id == 'customer_summary':
            return self._generate_customer_summary_jrxml()
        elif report_id == 'orders_by_date':
            return self._generate_orders_by_date_jrxml()
        else:
            return self._generate_customer_orders_jrxml()
    
    def _generate_customer_orders_jrxml(self):
        """Generate the Customer Orders Report JRXML."""
        sample_jrxml = '''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://jasperreports.sourceforge.net/jasperreports
              http://jasperreports.sourceforge.net/xsd/jasperreport.xsd"
              name="CustomerOrdersReport" pageWidth="595" pageHeight="842"
              columnWidth="555" leftMargin="20" rightMargin="20"
              topMargin="20" bottomMargin="20">

    <property name="ireport.zoom" value="1.0"/>
    <property name="ireport.x" value="0"/>
    <property name="ireport.y" value="0"/>

    <queryString>
        <![CDATA[
        SELECT 
            c.id as customer_id,
            c.name as customer_name,
            c.email as customer_email,
            o.id as order_id,
            o.amount as order_amount,
            o.order_date
        FROM customers c
        LEFT JOIN orders o ON c.id = o.customer_id
        ORDER BY c.name, o.order_date
        ]]>
    </queryString>

    <field name="customer_id" class="java.lang.Integer"/>
    <field name="customer_name" class="java.lang.String"/>
    <field name="customer_email" class="java.lang.String"/>
    <field name="order_id" class="java.lang.Integer"/>
    <field name="order_amount" class="java.math.BigDecimal"/>
    <field name="order_date" class="java.lang.String"/>

    <variable name="customer_total" class="java.math.BigDecimal" resetType="Group" resetGroup="customer_group" calculation="Sum">
        <variableExpression><![CDATA[$F{order_amount}]]></variableExpression>
    </variable>

    <group name="customer_group">
        <groupExpression><![CDATA[$F{customer_id}]]></groupExpression>
        <groupHeader>
            <band height="40">
                <rectangle>
                    <reportElement x="0" y="0" width="555" height="25" backcolor="#E6E6E6"/>
                    <graphicElement>
                        <pen lineWidth="0.5"/>
                    </graphicElement>
                </rectangle>
                <textField>
                    <reportElement x="10" y="5" width="200" height="15"/>
                    <textElement>
                        <font size="12" isBold="true"/>
                    </textElement>
                    <textFieldExpression><![CDATA[$F{customer_name}]]></textFieldExpression>
                </textField>
                <textField>
                    <reportElement x="220" y="5" width="200" height="15"/>
                    <textElement>
                        <font size="10"/>
                    </textElement>
                    <textFieldExpression><![CDATA[$F{customer_email}]]></textFieldExpression>
                </textField>
            </band>
        </groupHeader>
        <groupFooter>
            <band height="25">
                <staticText>
                    <reportElement x="350" y="5" width="100" height="15"/>
                    <textElement textAlignment="Right">
                        <font isBold="true"/>
                    </textElement>
                    <text><![CDATA[Customer Total:]]></text>
                </staticText>
                <textField pattern="¤ #,##0.00">
                    <reportElement x="460" y="5" width="80" height="15"/>
                    <textElement textAlignment="Right">
                        <font isBold="true"/>
                    </textElement>
                    <textFieldExpression><![CDATA[$V{customer_total}]]></textFieldExpression>
                </textField>
                <line>
                    <reportElement x="0" y="0" width="555" height="1"/>
                </line>
            </band>
        </groupFooter>
    </group>

    <title>
        <band height="60">
            <staticText>
                <reportElement x="0" y="10" width="555" height="30"/>
                <textElement textAlignment="Center">
                    <font size="20" isBold="true"/>
                </textElement>
                <text><![CDATA[Customer Orders Report]]></text>
            </staticText>
            <staticText>
                <reportElement x="0" y="40" width="555" height="15"/>
                <textElement textAlignment="Center">
                    <font size="12"/>
                </textElement>
                <text><![CDATA[Generated from Sample Database]]></text>
            </staticText>
        </band>
    </title>

    <columnHeader>
        <band height="25">
            <rectangle>
                <reportElement x="0" y="0" width="555" height="20" backcolor="#CCCCCC"/>
                <graphicElement>
                    <pen lineWidth="0.5"/>
                </graphicElement>
            </rectangle>
            <staticText>
                <reportElement x="10" y="5" width="80" height="15"/>
                <textElement>
                    <font isBold="true"/>
                </textElement>
                <text><![CDATA[Order ID]]></text>
            </staticText>
            <staticText>
                <reportElement x="100" y="5" width="120" height="15"/>
                <textElement>
                    <font isBold="true"/>
                </textElement>
                <text><![CDATA[Order Date]]></text>
            </staticText>
            <staticText>
                <reportElement x="430" y="5" width="100" height="15"/>
                <textElement textAlignment="Right">
                    <font isBold="true"/>
                </textElement>
                <text><![CDATA[Amount]]></text>
            </staticText>
        </band>
    </columnHeader>

    <detail>
        <band height="20">
            <textField isBlankWhenNull="true">
                <reportElement x="10" y="2" width="80" height="15"/>
                <textElement/>
                <textFieldExpression><![CDATA[$F{order_id}]]></textFieldExpression>
            </textField>
            <textField isBlankWhenNull="true">
                <reportElement x="100" y="2" width="120" height="15"/>
                <textElement/>
                <textFieldExpression><![CDATA[$F{order_date}]]></textFieldExpression>
            </textField>
            <textField pattern="¤ #,##0.00" isBlankWhenNull="true">
                <reportElement x="430" y="2" width="100" height="15"/>
                <textElement textAlignment="Right"/>
                <textFieldExpression><![CDATA[$F{order_amount}]]></textFieldExpression>
            </textField>
        </band>
    </detail>

    <pageFooter>
        <band height="20">
            <textField>
                <reportElement x="430" y="5" width="100" height="15"/>
                <textElement textAlignment="Right"/>
                <textFieldExpression><![CDATA["Page " + $V{PAGE_NUMBER}]]></textFieldExpression>
            </textField>
        </band>
    </pageFooter>

</jasperReport>'''
        return sample_jrxml
    
    def _generate_customer_summary_jrxml(self):
        """Generate the Customer Summary Report JRXML."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://jasperreports.sourceforge.net/jasperreports
              http://jasperreports.sourceforge.net/xsd/jasperreport.xsd"
              name="CustomerSummaryReport" pageWidth="595" pageHeight="842"
              columnWidth="555" leftMargin="20" rightMargin="20"
              topMargin="20" bottomMargin="20">

    <queryString>
        <![CDATA[
        SELECT 
            c.id as customer_id,
            c.name as customer_name,
            c.email as customer_email,
            COUNT(o.id) as total_orders,
            COALESCE(SUM(o.amount), 0) as total_amount,
            COALESCE(AVG(o.amount), 0) as average_order
        FROM customers c
        LEFT JOIN orders o ON c.id = o.customer_id
        GROUP BY c.id, c.name, c.email
        ORDER BY total_amount DESC
        ]]>
    </queryString>

    <field name="customer_id" class="java.lang.Integer"/>
    <field name="customer_name" class="java.lang.String"/>
    <field name="customer_email" class="java.lang.String"/>
    <field name="total_orders" class="java.lang.Integer"/>
    <field name="total_amount" class="java.math.BigDecimal"/>
    <field name="average_order" class="java.math.BigDecimal"/>

    <title>
        <band height="60">
            <staticText>
                <reportElement x="0" y="10" width="555" height="30"/>
                <textElement textAlignment="Center">
                    <font size="20" isBold="true"/>
                </textElement>
                <text><![CDATA[Customer Summary Report]]></text>
            </staticText>
            <staticText>
                <reportElement x="0" y="40" width="555" height="15"/>
                <textElement textAlignment="Center">
                    <font size="12"/>
                </textElement>
                <text><![CDATA[Customer Performance Overview]]></text>
            </staticText>
        </band>
    </title>

    <columnHeader>
        <band height="25">
            <rectangle>
                <reportElement x="0" y="0" width="555" height="20" backcolor="#CCCCCC"/>
            </rectangle>
            <staticText>
                <reportElement x="10" y="5" width="150" height="15"/>
                <textElement><font isBold="true"/></textElement>
                <text><![CDATA[Customer Name]]></text>
            </staticText>
            <staticText>
                <reportElement x="170" y="5" width="120" height="15"/>
                <textElement><font isBold="true"/></textElement>
                <text><![CDATA[Email]]></text>
            </staticText>
            <staticText>
                <reportElement x="300" y="5" width="80" height="15"/>
                <textElement textAlignment="Right"><font isBold="true"/></textElement>
                <text><![CDATA[Total Orders]]></text>
            </staticText>
            <staticText>
                <reportElement x="390" y="5" width="80" height="15"/>
                <textElement textAlignment="Right"><font isBold="true"/></textElement>
                <text><![CDATA[Total Amount]]></text>
            </staticText>
            <staticText>
                <reportElement x="480" y="5" width="65" height="15"/>
                <textElement textAlignment="Right"><font isBold="true"/></textElement>
                <text><![CDATA[Avg Order]]></text>
            </staticText>
        </band>
    </columnHeader>

    <detail>
        <band height="20">
            <textField>
                <reportElement x="10" y="2" width="150" height="15"/>
                <textElement/>
                <textFieldExpression><![CDATA[$F{customer_name}]]></textFieldExpression>
            </textField>
            <textField>
                <reportElement x="170" y="2" width="120" height="15"/>
                <textElement/>
                <textFieldExpression><![CDATA[$F{customer_email}]]></textFieldExpression>
            </textField>
            <textField>
                <reportElement x="300" y="2" width="80" height="15"/>
                <textElement textAlignment="Right"/>
                <textFieldExpression><![CDATA[$F{total_orders}]]></textFieldExpression>
            </textField>
            <textField pattern="¤ #,##0.00">
                <reportElement x="390" y="2" width="80" height="15"/>
                <textElement textAlignment="Right"/>
                <textFieldExpression><![CDATA[$F{total_amount}]]></textFieldExpression>
            </textField>
            <textField pattern="¤ #,##0.00">
                <reportElement x="480" y="2" width="65" height="15"/>
                <textElement textAlignment="Right"/>
                <textFieldExpression><![CDATA[$F{average_order}]]></textFieldExpression>
            </textField>
        </band>
    </detail>

    <pageFooter>
        <band height="20">
            <textField>
                <reportElement x="430" y="5" width="100" height="15"/>
                <textElement textAlignment="Right"/>
                <textFieldExpression><![CDATA["Page " + $V{PAGE_NUMBER}]]></textFieldExpression>
            </textField>
        </band>
    </pageFooter>

</jasperReport>'''

    def _generate_orders_by_date_jrxml(self):
        """Generate the Orders by Date Report JRXML."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://jasperreports.sourceforge.net/jasperreports
              http://jasperreports.sourceforge.net/xsd/jasperreport.xsd"
              name="OrdersByDateReport" pageWidth="595" pageHeight="842"
              columnWidth="555" leftMargin="20" rightMargin="20"
              topMargin="20" bottomMargin="20">

    <queryString>
        <![CDATA[
        SELECT 
            o.order_date,
            o.id as order_id,
            c.name as customer_name,
            o.amount as order_amount
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        ORDER BY o.order_date DESC, o.id
        ]]>
    </queryString>

    <field name="order_date" class="java.lang.String"/>
    <field name="order_id" class="java.lang.Integer"/>
    <field name="customer_name" class="java.lang.String"/>
    <field name="order_amount" class="java.math.BigDecimal"/>

    <variable name="date_total" class="java.math.BigDecimal" resetType="Group" resetGroup="date_group" calculation="Sum">
        <variableExpression><![CDATA[$F{order_amount}]]></variableExpression>
    </variable>

    <group name="date_group">
        <groupExpression><![CDATA[$F{order_date}]]></groupExpression>
        <groupHeader>
            <band height="30">
                <rectangle>
                    <reportElement x="0" y="0" width="555" height="25" backcolor="#E6E6E6"/>
                </rectangle>
                <staticText>
                    <reportElement x="10" y="5" width="80" height="15"/>
                    <textElement><font size="12" isBold="true"/></textElement>
                    <text><![CDATA[Date:]]></text>
                </staticText>
                <textField>
                    <reportElement x="90" y="5" width="200" height="15"/>
                    <textElement><font size="12" isBold="true"/></textElement>
                    <textFieldExpression><![CDATA[$F{order_date}]]></textFieldExpression>
                </textField>
            </band>
        </groupHeader>
        <groupFooter>
            <band height="25">
                <staticText>
                    <reportElement x="350" y="5" width="100" height="15"/>
                    <textElement textAlignment="Right"><font isBold="true"/></textElement>
                    <text><![CDATA[Date Total:]]></text>
                </staticText>
                <textField pattern="¤ #,##0.00">
                    <reportElement x="460" y="5" width="80" height="15"/>
                    <textElement textAlignment="Right"><font isBold="true"/></textElement>
                    <textFieldExpression><![CDATA[$V{date_total}]]></textFieldExpression>
                </textField>
                <line>
                    <reportElement x="0" y="0" width="555" height="1"/>
                </line>
            </band>
        </groupFooter>
    </group>

    <title>
        <band height="60">
            <staticText>
                <reportElement x="0" y="10" width="555" height="30"/>
                <textElement textAlignment="Center">
                    <font size="20" isBold="true"/>
                </textElement>
                <text><![CDATA[Orders by Date Report]]></text>
            </staticText>
            <staticText>
                <reportElement x="0" y="40" width="555" height="15"/>
                <textElement textAlignment="Center">
                    <font size="12"/>
                </textElement>
                <text><![CDATA[Daily Order Summary]]></text>
            </staticText>
        </band>
    </title>

    <columnHeader>
        <band height="25">
            <rectangle>
                <reportElement x="0" y="0" width="555" height="20" backcolor="#CCCCCC"/>
            </rectangle>
            <staticText>
                <reportElement x="10" y="5" width="80" height="15"/>
                <textElement><font isBold="true"/></textElement>
                <text><![CDATA[Order ID]]></text>
            </staticText>
            <staticText>
                <reportElement x="100" y="5" width="200" height="15"/>
                <textElement><font isBold="true"/></textElement>
                <text><![CDATA[Customer]]></text>
            </staticText>
            <staticText>
                <reportElement x="430" y="5" width="100" height="15"/>
                <textElement textAlignment="Right"><font isBold="true"/></textElement>
                <text><![CDATA[Amount]]></text>
            </staticText>
        </band>
    </columnHeader>

    <detail>
        <band height="20">
            <textField>
                <reportElement x="10" y="2" width="80" height="15"/>
                <textElement/>
                <textFieldExpression><![CDATA[$F{order_id}]]></textFieldExpression>
            </textField>
            <textField>
                <reportElement x="100" y="2" width="200" height="15"/>
                <textElement/>
                <textFieldExpression><![CDATA[$F{customer_name}]]></textFieldExpression>
            </textField>
            <textField pattern="¤ #,##0.00">
                <reportElement x="430" y="2" width="100" height="15"/>
                <textElement textAlignment="Right"/>
                <textFieldExpression><![CDATA[$F{order_amount}]]></textFieldExpression>
            </textField>
        </band>
    </detail>

    <pageFooter>
        <band height="20">
            <textField>
                <reportElement x="430" y="5" width="100" height="15"/>
                <textElement textAlignment="Right"/>
                <textFieldExpression><![CDATA["Page " + $V{PAGE_NUMBER}]]></textFieldExpression>
            </textField>
        </band>
    </pageFooter>

</jasperReport>'''
    
    def get_all_connections(self):
        """Get all database connections."""
        return DatabaseConnection.query.filter_by(is_active=True).all()
    
    def delete_connection(self, connection_id):
        """Delete a database connection."""
        connection = DatabaseConnection.query.get(connection_id)
        if connection:
            connection.is_active = False
            db.session.commit()
            return True
        return False
    
    def test_connection(self, connection_string):
        """Test if database connection is valid."""
        try:
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
