from email.policy import default
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy.schema import Sequence
from datetime import datetime, timezone

bcrypt = Bcrypt()
db = SQLAlchemy()

class User(db.Model):
    '''User in the system'''

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    username = db.Column(
        db.String,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    email = db.Column(
        db.String,
        nullable=False,
        unique=True,
    )

    first_name = db.Column(
        db. String,
        nullable=False,
    )

    last_name = db.Column(
        db.String,
        nullable=False,
    )

    phone = db.Column(
        db.String,
        nullable=False,
        unique=True,
    )

    is_admin = db.Column(
        db.Boolean, 
        nullable=False,
        default=False,
    )

    member_since = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now(timezone.utc),
    )

    @classmethod
    def register(cls, username, password, email, first_name, last_name, phone):
        '''Register a user 
        Hashes password and add user to the system'''

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = cls(
            username=username,
            password=hashed_pwd,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )

        db.session.add(user)
        return user

    @classmethod 
    def authenticate(cls, username, password):
        '''Finds a user with a matching username and password, 
        if it doesn't find it or password is wrong, returns False.'''

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            return user
        else:
            return False


class Reservation(db.Model):
    '''Database for all reservations.'''

    __tablename__ = 'reservations'


    id = db.Column(
        db.Integer, 
        Sequence('res_seq', start=10001, increment=1),
        primary_key=True,
    )

    # driver_id = db.Column(
    #     db.Integer,
    #     db.ForeignKey('drivers.id', ondelete='cascade'),
    #     primary_key=True,
    # )

    passenger_name = db.Column(
        db.String,
        nullable=False,
    )

    passenger_phone = db.Column(
        db.String,
        nullable=False,
    )

    passenger_email = db.Column(
        db.String,
    )

    vehicle_type = db.Column(
        db.String,
        nullable=False,
    )

    PU_time = db.Column(
        db.Time,
        nullable=False,
    )

    PU_date = db.Column(
        db.Date,
        nullable=False,
    )

    PU_address = db.Column(
        db.String,
        nullable=False,
    )

    PU_street = db.Column(
        db.String
    )

    PU_city = db.Column(
        db.String
    )

    PU_state = db.Column(
        db.String(3)
    )

    PU_zip = db.Column(
        db.String
    )

    PU_country = db.Column(
        db.String
    )

    DO_address = db.Column(
        db.String,
        nullable=False,
    )

    DO_street = db.Column(
        db.String
    )

    DO_city = db.Column(
        db.String
    )

    DO_state = db.Column(
        db.String(3)
    )

    DO_zip = db.Column(
        db.String
    )

    DO_country = db.Column(
        db.String
    )

    trip_notes = db.Column(
        db.Text,
    )

    created_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now(timezone.utc),
    )

    user_id = db.Column(
                        db.Integer,
                        db.ForeignKey('users.id'),
                        )

    user = db.relationship(User,  backref=db.backref("reservations", cascade="all, delete-orphan"))


class Admin(db.Model):
    '''System admnistrator'''

    __tablename__ = "admin"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    admin_username = db.Column(
        db.String,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    admin_email = db.Column(
        db.String,
        nullable=False,
        unique=True,
    )

    company_name = db.Column(
        db.String,
    )

    company_phone = db.Column(
        db.String,
    )

    company_email = db.Column(
        db.String,
    )

    company_website = db.Column(
        db.String,
    )

    logo_url = db.Column(
        db.Text,
        # default="/static/images/",
    )

    @classmethod
    def register_admin(cls, admin_username, password, admin_email):
        '''Register an administrator
        Hashes password and adds the admin to the system'''

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        admin = cls(
            admin_username=admin_username,
            password=hashed_pwd,
            admin_email=admin_email,
        )

        db.session.add(admin)
        return admin

    @classmethod 
    def authenticate_admin(cls, admin_username, password):
        '''Finds a user with a matching username and password, 
        if it doesn't find it or password is wrong, returns False.'''

        admin = Admin.query.filter_by(admin_username=admin_username).first()

        if admin and bcrypt.check_password_hash(admin.password, password):
            return admin
        else:
            return False


# class Driver(db.Model):
#     '''Driver '''

#     __tablename__ = 'drivers'


#     id = db.Column(
#         db.Integer,
#         primary_key=True,
#     )

#     driver_first_name = db.Column(
#         db.Text,
#     )

#     driver_last_name = db.Column(
#         db.Text,
#     )

#     driver_phone = db.Column(
#         db.Integer,
#     )

#     driver_email = db.Column(
#         db.Text,
#     )

#     driver_details = db.Column(
#         db.Text,
#     )


def connect_db(app):
    '''Connect this database to Flask app'''
    db.app = app
    db.init_app(app)
