from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, TelField, TimeField, TextAreaField, DateField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, InputRequired

class RegisterForm(FlaskForm):
    '''Form for registering new users.'''

    username = StringField(
        'Username', 
        validators=[InputRequired(), Length(min=4, max=25)],
        )

    password = PasswordField(
        'Password', 
        validators=[Length(min=8)],
        )

    email = EmailField(
        'E-mail', 
        validators=[InputRequired()],
        )

    first_name = StringField(
        'First Name', 
        validators=[InputRequired(), Length(max=30)],
        )

    last_name = StringField(
        'Last Name', 
        validators=[InputRequired(), Length(max=30)],
        )

    phone = TelField(
        'Phone Number', 
        validators=[InputRequired()],
        )


class AdminRegisterForm(FlaskForm):
    '''Form for registering new users.'''

    username = StringField(
        'Username', 
        validators=[InputRequired(), Length(min=4, max=25)],
        )

    password = PasswordField(
        'Password', 
        validators=[Length(min=8)],
        )

    email = EmailField(
        'E-mail', 
        validators=[InputRequired()],
        )

    first_name = StringField(
        'First Name', 
        validators=[InputRequired(), Length(max=30)],
        )

    last_name = StringField(
        'Last Name', 
        validators=[InputRequired(), Length(max=30)],
        )

    phone = TelField(
        'Phone Number', 
        validators=[InputRequired()],
        )

    is_admin = BooleanField(
        'Is admin',
        default="checked",
    )


class LoginForm(FlaskForm):
    '''Form for login a user.'''

    username = StringField(
        'Username', 
        validators=[DataRequired()],
        )

    password = PasswordField(
        'Password', 
        validators=[Length(min=6)],
        )

    
class UserEditForm(FlaskForm):
    '''Form for updating user's profile.'''

    username = StringField(
        'Username', 
        validators=[InputRequired(), Length(min=4, max=25)],
        )

    email = EmailField(
        'E-mail', 
        validators=[InputRequired()],
        )

    first_name = StringField(
        'First Name', 
        validators=[InputRequired(), Length(max=30)],
        )

    last_name = StringField(
        'Last Name', 
        validators=[InputRequired(), Length(max=30)],
        )

    phone = TelField(
        'Phone Number', 
        validators=[InputRequired()],
        )

    password = PasswordField(
        'Password', 
        validators=[Length(min=6)],
        )



class ResForm(FlaskForm):
    '''Reservation form'''

    passenger_name = StringField(
        "Passenger's Full Name",
        validators=[InputRequired()],
    )

    passenger_phone = TelField(
        "Passenger's Mobile#",
        validators=[InputRequired()],
    )

    passenger_email = EmailField(
        "Passenger's Email",
    )

    vehicle_type = SelectField(
        'Choose type of vehicle',
        choices=[('Sedan (up to 4 passengers)'), ('SUV (up to 7 passengers)'), ('Sprinter Van (up to 14 passengers)')],
        validate_choice=True
    )

    PU_date = DateField(
        'Pickup Date',
        validators=[DataRequired()],
    )

    PU_time = TimeField(
        'Pickup Time',
        validators=[DataRequired()],
    )

    PU_address = StringField(
        'Search for your pick-Up address',
    )

    PU_street = StringField(
        'Street Address',
        validators=[InputRequired()],
    )

    PU_city = StringField(
        'City',
        validators=[InputRequired()],
    )

    PU_state = StringField(
        'State', 
        validators=[Length(max=3)]
    )

    PU_zip = StringField(
        'Zip'
    )
    
    PU_country = StringField(
        'Country'
    )

    DO_address = StringField(
        'Search for your drop-off address',
    )

    DO_street = StringField(
        'Street Address',
        validators=[InputRequired()],
    )

    DO_city = StringField(
        'City',
        validators=[InputRequired()],
    )

    DO_state = StringField(
        'State', 
        validators=[Length(max=3)]
    )

    DO_zip = StringField(
        'Zip'
    )
    
    DO_country = StringField(
        'Country'
    )

    trip_notes = TextAreaField(
        'Trip Notes',
    )


class EmailRes(FlaskForm):
    '''Form for a user to email a confirmation'''

    email_res = EmailField(
        'Enter your email',
        validators=[InputRequired()],
    )


