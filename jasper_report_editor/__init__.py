from flask import Blueprint

jasper_report_editor_bp = Blueprint(
    'JasperReportEditor',
    __name__,
    template_folder='templates',
    static_folder='static'
)

from . import routes  # noqa: E402,F401
