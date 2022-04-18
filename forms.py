from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, TelField, TimeField, TextAreaField, DateField, SelectField, FormField
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
        'Pick-Up Address',
        validators=[InputRequired()],
    )

    PU_address_2 = StringField(
        'Address 2'
    )

    PU_city = StringField(
        'City'
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
        'Drop-off Address',
        validators=[InputRequired()],
    )

    DO_address_2 = StringField(
        'Address 2'
    )

    DO_city = StringField(
        'City'
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

    notes = TextAreaField(
        'Reservation Notes',
    )


class EmailRes(FlaskForm):
    '''Form for a user to email a confirmation'''

    email_res = EmailField(
        'Enter your email',
        validators=[InputRequired()],
    )
