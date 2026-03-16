from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta
import csv
from io import StringIO
from flask import Response

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///theatre_data.db"
app.config["SECRET_KEY"] = "secret"
app.jinja_env.globals.update(getattr=getattr)
db = SQLAlchemy(app)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thedate = db.Column(db.Date, index=True)
    theatre = db.Column(db.String(1))

    list_type = db.Column(db.String(10))
    list_finish = db.Column(db.String(6))

    start_anaesthetic_time = db.Column(db.String(5))
    start_surgical_prep_time = db.Column(db.String(5))

    # CASE TIMES
    case1_in_reason = db.Column(db.String(20))
    case1_in_notes = db.Column(db.Text)
    case1_out = db.Column(db.String(5))

    case2_in = db.Column(db.String(5))
    case2_in_reason = db.Column(db.String(20))
    case2_in_notes = db.Column(db.Text)
    case2_out = db.Column(db.String(5))

    case3_in = db.Column(db.String(5))
    case3_in_reason = db.Column(db.String(20))
    case3_in_notes = db.Column(db.Text)
    case3_out = db.Column(db.String(5))

    case4_in = db.Column(db.String(5))
    case4_in_reason = db.Column(db.String(20))
    case4_in_notes = db.Column(db.Text)
    case4_out = db.Column(db.String(5))

    case5_in = db.Column(db.String(5))
    case5_in_reason = db.Column(db.String(20))
    case5_in_notes = db.Column(db.Text)
    case5_out = db.Column(db.String(5))

    case6_in = db.Column(db.String(5))
    case6_in_reason = db.Column(db.String(20))
    case6_in_notes = db.Column(db.Text)
    case6_out = db.Column(db.String(5))

    record_complete = db.Column(db.Boolean, default=False)

def parse_time(t):
    if not t:
        return None
    return datetime.strptime(t,"%H:%M")

def validate_times(data):
    order = [
        "start_anaesthetic_time",
        "start_surgical_prep_time",
        "case1_out",
        "case2_in",
        "case2_out",
        "case3_in",
        "case3_out",
        "case4_in",
        "case4_out",
        "case5_in",
        "case5_out",
        "case6_in",
        "case6_out"
    ]
    previous = None
    for field in order:
        t = parse_time(data.get(field))
        if t:
            if previous and t < previous:
                return False, f"{field} occurs before previous case step"
            previous = t
    return True, None

def seed_february():
    start = date(2026, 2, 1)
    for i in range(28):
        d = start + timedelta(days=i)
        for theatre in ["A", "B", "C"]:
            exists = Record.query.filter_by(thedate=d, theatre=theatre).first()
            if not exists:
                r = Record(
                    thedate=d,
                    theatre=theatre,
                    list_type="No list",
                    record_complete=False
                )
                db.session.add(r)
    db.session.commit()

@app.before_request
def setup():
    db.create_all()
    seed_february()

def is_weekend(d):
    return d.weekday() >= 5

@app.route("/")
def dashboard():
    start = date(2026, 2, 1)
    days = []
    for i in range(28):
        d = start + timedelta(days=i)
        records = Record.query.filter_by(thedate=d).all()
        theatre_status = {}
        for r in records:
            theatre_status[r.theatre] = r.record_complete

        days.append({
            "date": d,
            "records": records,
            "status": theatre_status,
            "weekend": is_weekend(d)
        })
    return render_template("dashboard.html", days=days)

@app.route("/day/<d>")
def day_view(d):
    dt = datetime.strptime(d, "%Y-%m-%d").date()
    records = Record.query.filter_by(thedate=dt).order_by(Record.theatre).all()
    return render_template("day.html", records=records, date=dt)

# @app.route("/edit/<int:id>", methods=["GET", "POST"])
# def edit_record(id):
#     r = Record.query.get_or_404(id)
#     delay_fields = ["2", "3", "4", "5", "6"]
#     if request.method == "POST":
#         r.list_type = request.form["list_type"]
#         r.start_anaesthetic_time = request.form.get("start_anaesthetic_time")
#         r.start_surgical_prep_time = request.form.get("start_surgical_prep_time")
#
#         r.case1_out = request.form.get("case1_out")
#
#         for c in delay_fields:
#             setattr(r, f"case{c}_in", request.form.get(f"case{c}_in"))
#             setattr(r, f"case{c}_in_reason", request.form.get(f"case{c}_reason"))
#             setattr(r, f"case{c}_in_notes", request.form.get(f"case{c}_notes"))
#             setattr(r, f"case{c}_out", request.form.get(f"case{c}_out"))
#
#         r.record_complete = True if request.form.get("record_complete") else False
#
#         db.session.commit()
#         flash("Record Saved", "success")
#         return redirect(url_for("day_view", d=r.thedate.isoformat()))
#     return render_template("edit.html", r=r)

@app.route("/edit/<int:id>",methods=["GET","POST"])
def edit_record(id):
    r = Record.query.get_or_404(id)

    if request.method=="POST":
        form = request.form.to_dict()
        valid,msg = validate_times(form)

        if not valid:
            flash(msg,"danger")
            return redirect(url_for("edit_record",id=id))
        r.list_type = form.get("list_type")
        r.list_finish = form.get("list_finish")

        for field in form:
            if hasattr(r, field):
                print(field+"#"+form[field])

        r.start_anaesthetic_time = form.get("start_anaesthetic_time") or None
        r.start_surgical_prep_time = form.get("start_surgical_prep_time") or None
        r.case1_in_notes = form.get("case1_notes")
        r.case1_in_reason = form.get("case1_reason")
        r.case1_out = form.get("case1_out") or None

        r.case2_in = form.get("case2_in") or None
        r.case2_in_reason = form.get("case2_reason")
        r.case2_in_notes = form.get("case2_notes")
        r.case2_out = form.get("case2_out") or None

        r.case3_in = form.get("case3_in") or None
        r.case3_in_reason = form.get("case3_reason")
        r.case3_in_notes = form.get("case3_notes")
        r.case3_out = form.get("case3_out") or None

        r.case4_in = form.get("case4_in") or None
        r.case4_in_reason = form.get("case4_reason")
        r.case4_in_notes = form.get("case4_notes")
        r.case4_out = form.get("case4_out") or None

        r.case5_in = form.get("case5_in") or None
        r.case5_in_reason = form.get("case5_reason")
        r.case5_in_notes = form.get("case5_notes")
        r.case5_out = form.get("case5_out") or None

        r.case6_in = form.get("case6_in") or None
        r.case6_in_reason = form.get("case6_reason")
        r.case6_in_notes = form.get("case6_notes")
        r.case6_out = form.get("case6_out") or None

        r.record_complete = True if form.get("record_complete") else False
        db.session.commit()
        flash("Record saved","success")
        return redirect(url_for("day_view",d=r.thedate.isoformat()))
    return render_template("edit.html",r=r)

@app.route("/complete_day/<d>", methods=["POST"])
def complete_day(d):
    dt = datetime.strptime(d,"%Y-%m-%d").date()
    recs = Record.query.filter_by(thedate=dt).all()
    for r in recs:
        r.record_complete = True
    db.session.commit()
    flash(f"All theatres marked complete for {dt}", "success")
    return redirect(url_for("dashboard"))

@app.route("/export_csv")
def export_csv():

    records = Record.query.order_by(Record.thedate, Record.theatre).all()

    output = StringIO()
    writer = csv.writer(output)

    header = [
        "date","theatre","list_type", "list_finish",
        "start_anaesthetic_time","start_surgical_prep_time",

        "case1_out",

        "case2_in","case2_reason","case2_notes","case2_out",
        "case3_in","case3_reason","case3_notes","case3_out",
        "case4_in","case4_reason","case4_notes","case4_out",
        "case5_in","case5_reason","case5_notes","case5_out",
        "case6_in","case6_reason","case6_notes","case6_out",

        "record_complete"
    ]

    writer.writerow(header)

    for r in records:

        writer.writerow([
            r.thedate,
            r.theatre,
            r.list_type,
            r.list_finish,

            r.start_anaesthetic_time,
            r.start_surgical_prep_time,
            r.case1_in_reason,
            r.case1_in_notes,
            r.case1_out,
            r.case1_in_reason,

            r.case2_in, r.case2_in_reason, r.case2_in_notes, r.case2_out,
            r.case3_in, r.case3_in_reason, r.case3_in_notes, r.case3_out,
            r.case4_in, r.case4_in_reason, r.case4_in_notes, r.case4_out,
            r.case5_in, r.case5_in_reason, r.case5_in_notes, r.case5_out,
            r.case6_in, r.case6_in_reason, r.case6_in_notes, r.case6_out,

            r.record_complete
        ])

    response = Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=theatre_data_feb_2026.csv"
        }
    )

    return response

if __name__ == "__main__":
    app.run(debug=True)