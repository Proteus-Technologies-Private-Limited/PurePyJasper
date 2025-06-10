# jasper_report.ai

This application provides a simple web based editor for JasperReports JRXML files powered by GPT-4.1.  The `JasperReportEditor` blueprint exposes an interface that allows uploading and editing JRXML files with CodeMirror, managing database connections and calling a language model to regenerate reports.

## Running

```
pip install -r requirements.txt
python app.py
```

Access the editor at `http://localhost:8080/editor`.
