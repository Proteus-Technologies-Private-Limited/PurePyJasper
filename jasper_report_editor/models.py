from config import db

class DatabaseConnection(db.Model):
    __tablename__ = 'database_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    database_type = db.Column(db.String(50), nullable=False)  # sqlite, mysql, postgresql, etc.
    host = db.Column(db.String(255))
    port = db.Column(db.Integer)
    database_name = db.Column(db.String(255))
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    connection_string = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<DatabaseConnection {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'database_type': self.database_type,
            'host': self.host,
            'port': self.port,
            'database_name': self.database_name,
            'username': self.username,
            'connection_string': self.connection_string,
            'is_active': self.is_active,
            'created_at': self.created_at
        }