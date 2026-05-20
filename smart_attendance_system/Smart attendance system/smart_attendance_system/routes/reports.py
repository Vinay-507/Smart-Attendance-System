from flask import Blueprint, render_template, request

from services.report_service import ReportService


reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/", methods=["GET"])
def attendance_reports():
    attendance_date = request.args.get("date", "").strip() or None
    student_id_raw = request.args.get("student_id", "").strip()
    student_id = int(student_id_raw) if student_id_raw.isdigit() else None

    report_data = ReportService().report(attendance_date, student_id)
    return render_template("reports/index.html", **report_data)
