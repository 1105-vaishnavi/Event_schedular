from flask import Flask, render_template, request, redirect, flash, session
from datetime import datetime
from config import Config
from models import db, Event, Resource, EventResourceAllocation, User
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()


# -------------------- LOGIN REQUIRED DECORATOR --------------------
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper


# -------------------- CONFLICT CHECK --------------------
def check_conflict(resource_id, start, end, ignore_event=None):
    allocations = EventResourceAllocation.query.filter_by(resource_id=resource_id).all()

    for alloc in allocations:
        event = alloc.event
        if ignore_event and event.event_id == ignore_event:
            continue

        if not (end <= event.start_time or start >= event.end_time):
            return True
    return False


# -------------------- HOME --------------------
@app.route("/")
def home():
    return redirect("/events")


# -------------------- EVENTS --------------------
@app.route("/events", methods=["GET", "POST"])
@login_required
def events():
    if request.method == "POST":
        title = request.form["title"]
        start = datetime.fromisoformat(request.form["start"])
        end = datetime.fromisoformat(request.form["end"])
        description = request.form["description"]

        if start >= end:
            flash("❌ Start time must be before end time")
            return redirect("/events")

        event = Event(
            title=title,
            start_time=start,
            end_time=end,
            description=description
        )
        db.session.add(event)
        db.session.commit()
        flash("✅ Event added successfully")

    return render_template("events.html", events=Event.query.all())


# -------------------- RESOURCES --------------------
@app.route("/resources", methods=["GET", "POST"])
@login_required
def resources():
    if request.method == "POST":
        name = request.form["name"]
        rtype = request.form["type"]

        resource = Resource(
            resource_name=name,
            resource_type=rtype
        )
        db.session.add(resource)
        db.session.commit()
        flash("✅ Resource added successfully")

    return render_template("resources.html", resources=Resource.query.all())


# -------------------- ALLOCATE RESOURCE --------------------
@app.route("/allocate", methods=["GET", "POST"])
@login_required
def allocate():
    if request.method == "POST":
        event_id = int(request.form["event"])
        resource_id = int(request.form["resource"])

        event = Event.query.get(event_id)

        if check_conflict(resource_id, event.start_time, event.end_time):
            flash("❌ Resource is already booked for this time")
            return redirect("/allocate")

        allocation = EventResourceAllocation(
            event_id=event_id,
            resource_id=resource_id
        )
        db.session.add(allocation)
        db.session.commit()
        flash("✅ Resource allocated successfully")

    return render_template(
        "allocate.html",
        events=Event.query.all(),
        resources=Resource.query.all()
    )


# -------------------- CONFLICT VIEW --------------------
@app.route("/conflicts")
@login_required
def conflicts():
    conflict_list = []

    for alloc in EventResourceAllocation.query.all():
        if check_conflict(
            alloc.resource_id,
            alloc.event.start_time,
            alloc.event.end_time,
            ignore_event=alloc.event_id
        ):
            conflict_list.append(alloc)

    return render_template("conflicts.html", conflicts=conflict_list)


# -------------------- RESOURCE UTILISATION REPORT --------------------
@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    report_data = []

    if request.method == "POST":
        start = datetime.fromisoformat(request.form["start"])
        end = datetime.fromisoformat(request.form["end"])

        for resource in Resource.query.all():
            total_hours = 0
            upcoming = []

            for alloc in resource.allocations:
                event = alloc.event

                # OVERLAP CHECK
                if event.end_time > start and event.start_time < end:
                    actual_start = max(event.start_time, start)
                    actual_end = min(event.end_time, end)

                    duration = (actual_end - actual_start).total_seconds() / 3600
                    total_hours += round(duration, 2)
                    upcoming.append(event.title)

            report_data.append({
                "resource": resource.resource_name,
                "hours": total_hours,
                "bookings": upcoming
            })

    return render_template("report.html", report=report_data)


# -------------------- SIGNUP --------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("❌ Username already exists")
            return redirect("/signup")

        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("✅ Signup successful. Please login.")
        return redirect("/login")

    return render_template("signup.html")


# -------------------- LOGIN --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            flash("✅ Login successful")
            return redirect("/events")

        flash("❌ Invalid credentials")
        return redirect("/login")

    return render_template("login.html")


# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully")
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
