from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)

class Resource(db.Model):
    resource_id = db.Column(db.Integer, primary_key=True)
    resource_name = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)

class EventResourceAllocation(db.Model):
    allocation_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id'))
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.resource_id'))

    event = db.relationship("Event", backref="allocations")
    resource = db.relationship("Resource", backref="allocations")
