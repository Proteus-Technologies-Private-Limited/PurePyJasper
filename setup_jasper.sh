#!/bin/bash

# Setup script for JasperReports dependencies

echo "Setting up JasperReports dependencies..."

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo "Java is not installed. Please install Java 8 or higher."
    echo "On macOS: brew install openjdk@11"
    echo "On Ubuntu/Debian: sudo apt-get install openjdk-11-jdk"
    echo "On RHEL/CentOS: sudo yum install java-11-openjdk"
    exit 1
else
    echo "Java is installed:"
    java -version
fi

# Create lib directory for JDBC drivers
mkdir -p jasper_report_editor/lib

# Download JDBC drivers if not present
echo "Checking JDBC drivers..."

# SQLite JDBC driver
if [ ! -f "jasper_report_editor/lib/sqlite-jdbc.jar" ]; then
    echo "Downloading SQLite JDBC driver..."
    curl -L -o jasper_report_editor/lib/sqlite-jdbc.jar \
        https://github.com/xerial/sqlite-jdbc/releases/download/3.42.0.0/sqlite-jdbc-3.42.0.0.jar
fi

# MySQL JDBC driver
if [ ! -f "jasper_report_editor/lib/mysql-connector.jar" ]; then
    echo "Downloading MySQL JDBC driver..."
    curl -L -o jasper_report_editor/lib/mysql-connector.jar \
        https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.1.0/mysql-connector-j-8.1.0.jar
fi

# PostgreSQL JDBC driver
if [ ! -f "jasper_report_editor/lib/postgresql.jar" ]; then
    echo "Downloading PostgreSQL JDBC driver..."
    curl -L -o jasper_report_editor/lib/postgresql.jar \
        https://jdbc.postgresql.org/download/postgresql-42.6.0.jar
fi

echo "Setup complete!"
echo ""
echo "To use JasperReports with this application:"
echo "1. Ensure Java is in your PATH"
echo "2. Install Python dependencies: pip install -r requirements.txt"
echo "3. The JDBC drivers are now in jasper_report_editor/lib/"