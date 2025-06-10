import os
import base64
from flask import request, render_template, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

from . import jasper_report_editor_bp
from .manager import JasperManager
from .models import DatabaseConnection
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyjasper_lib_integration import pyjasper_integration

manager = JasperManager()


@jasper_report_editor_bp.route('/', methods=['GET', 'POST'])
def editor():
    print("=== Editor route accessed ===")
    jrxml_text = ''
    try:
        connections = manager.get_all_connections()
        sample_reports = manager.get_sample_reports()
        print(f"Loaded {len(connections)} connections and {len(sample_reports)} sample reports")
    except Exception as e:
        connections = []
        sample_reports = []
        print(f'Error loading data: {str(e)}')
    
    if request.method == 'POST':
        file = request.files.get('jrxml')
        if file:
            filename = secure_filename(file.filename)
            path = os.path.join('uploads', filename)
            os.makedirs('uploads', exist_ok=True)
            file.save(path)
            with open(path) as f:
                jrxml_text = f.read()
    
    try:
        print("Attempting to render template...")
        return render_template('jasper_report_editor/editor.html',
                               jrxml_text=jrxml_text,
                               connections=connections,
                               sample_reports=sample_reports)
    except Exception as e:
        print(f"Template rendering failed: {e}")
        # Return a simplified HTML page as fallback
        sample_reports_html = ""
        for report in sample_reports:
            sample_reports_html += f'<li><a href="/editor/load_sample_report/{report["id"]}">{report["name"]}</a></li>'
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Jasper Report Editor</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                textarea {{ width: 100%; height: 400px; font-family: monospace; }}
                .preview {{ border: 1px solid #ccc; min-height: 300px; padding: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Jasper Report Editor (Simplified)</h1>
                <p><strong>Template Error:</strong> {e}</p>
                
                <h3>Sample Reports:</h3>
                <ul>{sample_reports_html}</ul>
                
                <h3>JRXML Editor:</h3>
                <form method="post" action="/editor/preview">
                    <textarea name="jrxml_content" placeholder="Enter JRXML content here...">{jrxml_text}</textarea>
                    <br><br>
                    <select name="connection_id">
                        <option value="">Select Database Connection</option>
                        {"".join([f'<option value="{conn.id}">{conn.name}</option>' for conn in connections])}
                    </select>
                    <button type="submit">Preview Report</button>
                </form>
                
                <h3>Preview:</h3>
                <div class="preview" id="preview">Click "Preview Report" to see output</div>
            </div>
        </body>
        </html>
        """


@jasper_report_editor_bp.route('/save', methods=['POST'])
def save_jrxml():
    content = request.form.get('jrxml_text', '')
    path = request.form.get('path', 'output.jrxml')
    with open(path, 'w') as f:
        f.write(content)
    flash('JRXML saved')
    return redirect(url_for('JasperReportEditor.editor'))


@jasper_report_editor_bp.route('/generate_sample_db')
def generate_sample_db():
    manager.create_sample_db()
    flash('Sample database created')
    return redirect(url_for('JasperReportEditor.editor'))

@jasper_report_editor_bp.route('/test/<report_id>')
def test_route(report_id):
    return f"Test route working for report_id: {report_id}"

@jasper_report_editor_bp.route('/load_sample_report/<report_id>')
def load_sample_report(report_id):
    print(f"=== Loading sample report: {report_id} ===")
    
    # Validate report_id
    valid_reports = ['customer_orders', 'customer_summary', 'orders_by_date']
    if report_id not in valid_reports:
        print(f"Invalid report_id: {report_id}")
        return f"<h1>Error</h1><p>Invalid report ID: {report_id}</p><p><a href='/editor/'>Back to Editor</a></p>"
    
    try:
        print(f"Generating JRXML for: {report_id}")
        sample_jrxml = manager.generate_sample_jrxml(report_id)
        print(f"Generated JRXML length: {len(sample_jrxml) if sample_jrxml else 0}")
        
        print("Loading connections...")
        connections = manager.get_all_connections()
        print(f"Found {len(connections)} connections")
        
        print("Getting sample reports list...")
        sample_reports = manager.get_sample_reports()
        print(f"Found {len(sample_reports)} sample reports")
        
        print("Rendering template...")
        try:
            result = render_template('jasper_report_editor/editor.html',
                                   jrxml_text=sample_jrxml,
                                   connections=connections,
                                   sample_reports=sample_reports)
            print(f"Template rendered successfully, length: {len(result)}")
            return result
        except Exception as template_error:
            print(f"Template rendering error: {template_error}")
            # Return a simple HTML page with the JRXML content
            return f"""
            <html>
            <head><title>Sample Report: {report_id}</title></head>
            <body>
                <h1>Sample Report Loaded: {report_id}</h1>
                <p><a href="/editor/">Back to Editor</a></p>
                <h3>JRXML Content:</h3>
                <pre style="background: #f5f5f5; padding: 10px; overflow: auto;">{sample_jrxml}</pre>
            </body>
            </html>
            """
        
    except Exception as e:
        print(f"ERROR loading sample report {report_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error</h1><p>Error loading sample report: {str(e)}</p><p><a href='/editor/'>Back to Editor</a></p>"


@jasper_report_editor_bp.route('/assistant', methods=['POST'])
def assistant():
    prompt = request.form.get('prompt', '')
    image = request.files.get('image')
    image_data = None
    if image:
        image_data = image.read()
    new_jrxml = manager.regenerate_jrxml(prompt, image_data)
    return jsonify({'jrxml': new_jrxml})


@jasper_report_editor_bp.route('/generate_pyjasper', methods=['POST'])
def generate_with_pyjasper():
    """Generate report using PyJasper library."""
    try:
        jrxml_content = request.form.get('jrxml_text', '')
        connection_id = request.form.get('connection')
        output_format = request.form.get('format', 'html').lower()
        
        if not jrxml_content.strip():
            return jsonify({'error': 'No JRXML content provided'}), 400
        
        # Get connection string if connection is selected
        connection_string = None
        if connection_id:
            try:
                connection = DatabaseConnection.query.get(int(connection_id))
                if connection:
                    connection_string = connection.connection_string
            except (ValueError, TypeError):
                pass
        
        # Generate report using PyJasper
        content, error = pyjasper_integration.generate_report(
            jrxml_content=jrxml_content,
            connection_string=connection_string,
            output_format=output_format
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        # Return content as base64 for HTML or direct bytes for PDF
        if output_format == 'pdf':
            return jsonify({
                'content': base64.b64encode(content).decode('utf-8'),
                'type': 'pdf'
            })
        else:
            return jsonify({
                'content': content.decode('utf-8'),
                'type': 'html'
            })
            
    except Exception as e:
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500


@jasper_report_editor_bp.route('/validate_jrxml', methods=['POST'])
def validate_jrxml():
    """Validate JRXML using PyJasper library."""
    try:
        jrxml_content = request.form.get('jrxml_text', '')
        
        if not jrxml_content.strip():
            return jsonify({'error': 'No JRXML content provided'}), 400
        
        validation = pyjasper_integration.validate_jrxml(jrxml_content)
        return jsonify(validation)
        
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500


@jasper_report_editor_bp.route('/preview_data', methods=['POST'])
def preview_data():
    """Preview data for a report using PyJasper library."""
    try:
        jrxml_content = request.form.get('jrxml_text', '')
        connection_id = request.form.get('connection')
        limit = int(request.form.get('limit', 10))
        
        if not jrxml_content.strip():
            return jsonify({'error': 'No JRXML content provided'}), 400
        
        # Get connection string
        connection_string = None
        if connection_id:
            try:
                connection = DatabaseConnection.query.get(int(connection_id))
                if connection:
                    connection_string = connection.connection_string
            except (ValueError, TypeError):
                pass
        
        if not connection_string:
            return jsonify({'error': 'No database connection selected'}), 400
        
        # Preview data using PyJasper
        data, error = pyjasper_integration.preview_data(
            jrxml_content=jrxml_content,
            connection_string=connection_string,
            limit=limit
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({'data': data})
        
    except Exception as e:
        return jsonify({'error': f'Data preview failed: {str(e)}'}), 500


@jasper_report_editor_bp.route('/generate_sample_jrxml', methods=['POST'])
def generate_sample_jrxml():
    """Generate sample JRXML based on database table using PyJasper library."""
    try:
        table_name = request.form.get('table_name')
        connection_id = request.form.get('connection')
        
        if not table_name:
            return jsonify({'error': 'No table name provided'}), 400
        
        # Get connection string
        connection_string = None
        if connection_id:
            try:
                connection = DatabaseConnection.query.get(int(connection_id))
                if connection:
                    connection_string = connection.connection_string
            except (ValueError, TypeError):
                pass
        
        if not connection_string:
            return jsonify({'error': 'No database connection selected'}), 400
        
        # Generate sample JRXML using PyJasper
        jrxml_content, error = pyjasper_integration.generate_sample_jrxml(
            table_name=table_name,
            connection_string=connection_string
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({'jrxml': jrxml_content})
        
    except Exception as e:
        return jsonify({'error': f'Sample JRXML generation failed: {str(e)}'}), 500


@jasper_report_editor_bp.route('/library_status')
def library_status():
    """Get PyJasper library status."""
    try:
        status = pyjasper_integration.check_library_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500

@jasper_report_editor_bp.route('/connections')
def connections():
    try:
        connections = manager.get_all_connections()
    except Exception as e:
        connections = []
        flash(f'Error loading connections: {str(e)}', 'error')
    return render_template('jasper_report_editor/connections.html', connections=connections)

@jasper_report_editor_bp.route('/connections/add', methods=['GET', 'POST'])
def add_connection():
    if request.method == 'POST':
        name = request.form.get('name')
        database_type = request.form.get('database_type')
        host = request.form.get('host')
        port = request.form.get('port')
        database_name = request.form.get('database_name')
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            port = int(port) if port else None
        except ValueError:
            port = None
            
        connection_string = manager.save_connection(
            name, database_type, host, port, database_name, username, password
        )
        
        # Test connection
        success, message = manager.test_connection(connection_string)
        if success:
            flash(f'Connection "{name}" added successfully!', 'success')
        else:
            flash(f'Connection added but test failed: {message}', 'warning')
            
        return redirect(url_for('JasperReportEditor.connections'))
    
    return render_template('jasper_report_editor/add_connection.html')

@jasper_report_editor_bp.route('/connections/delete/<int:connection_id>', methods=['POST'])
def delete_connection(connection_id):
    if manager.delete_connection(connection_id):
        flash('Connection deleted successfully!', 'success')
    else:
        flash('Connection not found!', 'error')
    return redirect(url_for('JasperReportEditor.connections'))

@jasper_report_editor_bp.route('/connections/test/<int:connection_id>')
def test_connection(connection_id):
    connection = DatabaseConnection.query.get(connection_id)
    if connection:
        success, message = manager.test_connection(connection.connection_string)
        return jsonify({'success': success, 'message': message})
    return jsonify({'success': False, 'message': 'Connection not found'})

@jasper_report_editor_bp.route('/preview', methods=['POST'])
def preview_report():
    jrxml_content = request.form.get('jrxml_content')
    connection_id = request.form.get('connection_id')
    output_format = request.form.get('format', 'html')
    
    if not jrxml_content:
        return jsonify({
            'success': False,
            'message': 'No JRXML content provided'
        })
    
    # Get connection details
    connection_string = None
    if connection_id:
        try:
            connection = DatabaseConnection.query.get(int(connection_id))
            if connection:
                connection_string = connection.connection_string
        except (ValueError, TypeError):
            pass
    
    try:
        # Use PyJasper library for report generation
        content, error = pyjasper_integration.generate_report(
            jrxml_content=jrxml_content,
            connection_string=connection_string,
            output_format=output_format
        )
        
        if error:
            return jsonify({
                'success': False,
                'message': f'Error generating preview: {error}'
            })
        
        if output_format == 'html':
            # Decode bytes content for HTML display
            html_content = content.decode('utf-8') if isinstance(content, bytes) else content
            return jsonify({
                'success': True,
                'html_preview': html_content,
                'message': f'Report preview generated in {output_format.upper()} format'
            })
        elif output_format == 'pdf':
            # For PDF, encode as base64 for embedding
            pdf_base64 = base64.b64encode(content).decode('utf-8')
            pdf_embed_html = f'''
                <div style="height: 100%; min-height: 500px;">
                    <embed src="data:application/pdf;base64,{pdf_base64}" 
                           type="application/pdf" 
                           width="100%" 
                           height="600px" />
                </div>
                <div class="mt-2 text-center">
                    <a href="data:application/pdf;base64,{pdf_base64}" 
                       download="report.pdf" 
                       class="btn btn-sm btn-primary">
                        <i class="fas fa-download"></i> Download PDF
                    </a>
                </div>
            '''
            return jsonify({
                'success': True,
                'html_preview': pdf_embed_html,
                'message': 'PDF report generated successfully'
            })
        else:
            # For other formats, return success with download info
            return jsonify({
                'success': True,
                'html_preview': f'<div class="alert alert-success"><i class="fas fa-check"></i> {output_format.upper()} report generated successfully! Download functionality coming soon.</div>',
                'message': f'Report generated in {output_format.upper()} format'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating preview: {str(e)}'
        })
