from flask import Flask
from config import db

def create_app():
    app = Flask(__name__)
    app.secret_key = 'change-me'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jasper_reports.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True  # Enable debug mode
    
    db.init_app(app)
    
    # Import blueprint
    from jasper_report_editor import jasper_report_editor_bp
    app.register_blueprint(jasper_report_editor_bp, url_prefix='/editor')
    
    with app.app_context():
        db.create_all()
    
    # Add a simple route to test
    @app.route('/')
    def index():
        return '<h1>Jasper Reports App</h1><p><a href="/editor/">Go to Editor</a></p>'
    
    return app

app = create_app()


if __name__ == '__main__':
    try:
        print("Starting Flask app...")
        print("App will be available at:")
        print("  - Local: http://127.0.0.1:8081/")
        print("  - Editor: http://127.0.0.1:8081/editor/")
        print("  - Network: http://0.0.0.0:8081/")
        app.run(host='0.0.0.0', port=8081, debug=True)
    except Exception as e:
        print(f"Error starting app: {e}")
        import traceback
        traceback.print_exc()
