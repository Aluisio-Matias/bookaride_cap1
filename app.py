from flask import Flask, jsonify, render_template, redirect, flash, session, url_for
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.exceptions import Unauthorized
from forms import EmailRes, RegisterForm, LoginForm, ResForm, UserEditForm, AdminRegisterForm
from models import db, connect_db, User, Reservation
from sqlalchemy import exc
import os
import re
import smtplib
from email.message import EmailMessage
from twilio.rest import Client
try:
    from secret import em_user, em_pass, account_sid, auth_token, twilio_number
except:
    em_user = os.environ.get("EM_USER")
    em_pass = os.environ.get("EM_PASS")
    account_sid = os.environ.get("ACCOUNT_SID")
    auth_token = os.environ.get("AUTH_TOKEN")
    twilio_number = os.environ.get("TWILIO_NUMBER")

app = Flask(__name__)

uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///book_a_ride'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.debug = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

CURR_USER_KEY = "curr_user"
CURR_ADMIN_KEY = "curr_admin"
EMAIL_ADDRESS = em_user
EMAIL_PASSWORD = em_pass
ACCOUNT_SID = account_sid
AUTH_TOKEN = auth_token
TWILIO_NUMBER = twilio_number

# for working with the twilio API
client = Client(ACCOUNT_SID, AUTH_TOKEN)

connect_db(app)

###########################################################################
# Homepage and error handling

@app.route('/')
def homepage():
    '''Display User's homepage'''
    return render_template('home.html')

@app.route('/about')
def about():
    '''Display about us page'''
    return render_template('about.html')

@app.errorhandler(404)
def page_not_found(e):
    '''Page not found (404 error)'''
    return render_template('404.html'), 404

@app.errorhandler(401)
def not_allowed(e):
    '''Show 401 page for not authorized users.'''
    return render_template('401.html'), 401


############################################################################
# User routes for register / login / logout
#################################################################


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    '''Page to register a new user to create an account.'''

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

    form = RegisterForm()

    if form.validate_on_submit():
        try:
            user = User.register(
                username = form.username.data,
                password = form.password.data,
                email = form.email.data,
                first_name = form.first_name.data,
                last_name = form.last_name.data,
                phone = form.phone.data,
             )
            db.session.commit()

        except exc.SQLAlchemyError:
            
            flash('Username, E-mail, or Phone number is taken! Please check the form and try again.', 'danger')
            return render_template('users/register.html', form=form)
        
        session[CURR_USER_KEY] = user.id
        flash('Welcome! Your account has been created successfully!', 'success')
        return redirect(f'/users/{user.id}')
    else:
        return render_template('users/register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''Show the page to login existing users.'''

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        
        if user and not user.is_admin:
            session[CURR_USER_KEY] = user.id
            flash(f'Hello, Welcome back {user.first_name}!', 'success')
            return redirect(f'/users/{user.id}')

        elif user and user.is_admin:
            session[CURR_ADMIN_KEY] = user.id
            flash(f'Hello, Welcome back {user.first_name}!', 'success')
            return redirect(f'/admin/admin_home')

    
        flash("Invalid credentials, please check your username and password and try again!", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    '''Handle logout of a user.'''
    session.clear()

    flash('You have been successfully logged out!', 'success')

    return redirect('/')



############# API to check if username already exists in the users database ############
@app.route('/check/<username>', methods=['GET'])
def check_user(username):
    
    user = User.query.filter_by(username=username).first()
    is_valid = True
    if user:
        is_valid = False
    return jsonify({"exists": is_valid})

############# API to check if phone number already exists in the users database ############
@app.route('/verify/<phone>', methods=['GET'])
def check_phone(phone):
    
    phone_num = User.query.filter_by(phone=phone).first()
    is_avail = True
    if phone_num:
        is_avail = False
    return jsonify({"exists": is_avail})

############# API to check if email already exists in the users database ############
@app.route('/lookup/<email>', methods=['GET'])
def check_email(email):
    
    ck_email = User.query.filter_by(email=email).first()
    valid = True
    if ck_email:
        valid = False
    return jsonify({"exists": valid})

################################################################################


#############################################################################
# User route for user's page / edit profile / reservations

@app.route('/users/<int:id>')
def user_dashboard(id):
    '''Page for logged in users.'''
    user = User.query.get_or_404(id)

    if CURR_USER_KEY not in session or session[CURR_USER_KEY] != user.id:
        raise Unauthorized()

    user = User.query.get_or_404(id)

    reservations = Reservation.query.all()
    
    return render_template('users/user_dashboard.html', user=user, reservations=reservations)


@app.route('/users/edit_profile/<int:user_id>', methods=['GET', 'POST'])
def edit_profile(user_id):
    '''Update a profile from a current user.'''

    user = User.query.get(session[CURR_USER_KEY])

    if CURR_USER_KEY not in session or session[CURR_USER_KEY] != user_id:
        raise Unauthorized()

    user_id = user.id
    form = UserEditForm(obj=user)

    if form.validate_on_submit():
        if User.authenticate(user.username, form.password.data):
            user.username = form.username.data
            user.email = form.email.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.phone = form.phone.data

            db.session.commit()
            return redirect(f'/users/{user.id}')

        flash('Wrong password, please try again!', 'danger')

    return render_template('users/edit_profile.html', user=user, form=form, user_id=user_id)


#############################################################################
# Reservations routes 

@app.route('/res/res_form', methods=['POST', 'GET'])
def res_form():
    '''Show form to submit a reservation.'''

    if CURR_USER_KEY not in session:
        raise Unauthorized()

    user = User.query.get(session[CURR_USER_KEY])

    form = ResForm()

    if form.validate_on_submit():
        passenger_name = form.passenger_name.data,
        passenger_phone = form.passenger_phone.data,
        passenger_email = form.passenger_email.data,
        vehicle_type = form.vehicle_type.data,
        PU_date = form.PU_date.data,
        PU_time = form.PU_time.data,
        PU_address = form.PU_address.data,
        PU_street = form.PU_street.data,
        PU_city = form.PU_city.data,
        PU_state = form.PU_state.data,
        PU_zip = form.PU_zip.data,
        PU_country = form.PU_country.data,
        DO_address = form.DO_address.data,
        DO_street = form.DO_street.data,
        DO_city = form.DO_city.data,
        DO_state = form.DO_state.data,
        DO_zip = form.DO_zip.data,
        DO_country = form.DO_country.data,
        trip_notes = form.trip_notes.data,

        new_res = Reservation(
            passenger_name = passenger_name,
            passenger_phone = passenger_phone,
            passenger_email = passenger_email,
            vehicle_type = vehicle_type,
            PU_date = PU_date,
            PU_time = PU_time,
            PU_address = PU_address,
            PU_street = PU_street,
            PU_city = PU_city,
            PU_state = PU_state,
            PU_zip = PU_zip,
            PU_country = PU_country,
            DO_address = DO_address,
            DO_street = DO_street,
            DO_city = DO_city,
            DO_state = DO_state,
            DO_zip = DO_zip,
            DO_country = DO_country,
            trip_notes = trip_notes,
        )

        user.reservations.append(new_res)
        db.session.commit()
        flash('Your reservation has been successfully submitted!', 'success')

        # SMS message using the Twilio API
        SMS_MESSAGE = client.messages.create(
            body=f'Your reservation has been successfully booked! {PU_date} - {PU_time}',
            from_=TWILIO_NUMBER,
            to=f'+1{passenger_phone}'
            )
        print(SMS_MESSAGE.body)

        return redirect(f'/users/{user.id}')
    else:
        return render_template('res/res_form.html', form=form, user=user)


################ routes to edit reservations ###########################
@app.route('/res/edit_res/<int:res_id>')
def show_edit_res(res_id):
    '''Display the form for editing the reservation'''

    res_id = Reservation.query.get_or_404(res_id)

    if CURR_USER_KEY not in session or session[CURR_USER_KEY] != res_id.user_id:
        raise Unauthorized()

    form = ResForm(obj=res_id)
    return render_template('/res/edit_res.html', res_id=res_id, form=form)


@app.route('/res/edit_res/<int:res_id>', methods=['POST'])
def edit_res(res_id):
    '''Edit a reservation '''
    user = User.query.get(session[CURR_USER_KEY])
    res_id = Reservation.query.get_or_404(res_id)
    
    if CURR_USER_KEY not in session or session[CURR_USER_KEY] != res_id.user_id:
        raise Unauthorized()

    form = ResForm(obj=res_id)

    if form.validate_on_submit():
        res_id.passenger_name = form.passenger_name.data,
        res_id.passenger_phone = form.passenger_phone.data,
        res_id.passenger_email = form.passenger_email.data,
        res_id.vehicle_type = form.vehicle_type.data,
        res_id.PU_date = form.PU_date.data,
        res_id.PU_time = form.PU_time.data,
        res_id.PU_address = form.PU_address.data,
        res_id.PU_street = form.PU_street.data,
        res_id.PU_city = form.PU_city.data,
        res_id.PU_state = form.PU_state.data,
        res_id.PU_zip = form.PU_zip.data,
        res_id.PU_country = form.PU_country.data,
        res_id.DO_address = form.DO_address.data,
        res_id.DO_street = form.DO_street.data,
        res_id.DO_city = form.DO_city.data,
        res_id.DO_state = form.DO_state.data,
        res_id.DO_zip = form.DO_zip.data,
        res_id.DO_country = form.DO_country.data,
        res_id.trip_notes = form.trip_notes.data,

        db.session.commit()
        flash('Your reservation has been updated.', 'success')
        return redirect(f'/users/{user.id}')



################# reservation view route ####################
@app.route('/res/view/<int:res_id>')
def view_res(res_id):
    '''display reservation details in HTML'''

    if (CURR_USER_KEY not in session) and (CURR_ADMIN_KEY not in session):
        raise Unauthorized()

    res = Reservation.query.get_or_404(res_id)
    return render_template('/res/view_res.html', res=res)


################ email reservation routes ###################

@app.route('/res/email_res_form/<int:res_id>')
def email_res_form(res_id):
    '''Display a form so a user can email the booking confirmation'''

    if CURR_USER_KEY not in session and CURR_ADMIN_KEY not in session:
        raise Unauthorized()

    user = User.query.get(session[CURR_USER_KEY or CURR_ADMIN_KEY])
    res_id = Reservation.query.get_or_404(res_id)
    form = EmailRes()
    return render_template('/res/email_res.html', user=user, res_id=res_id, form=form)


@app.route('/res/email_res_form/<int:res_id>', methods=['POST'])
def email_res(res_id):
    '''Display a form so a user can email the booking confirmation'''

    if CURR_USER_KEY not in session and CURR_ADMIN_KEY not in session:
        raise Unauthorized()

    user = User.query.get(session[CURR_USER_KEY])
    res = Reservation.query.get_or_404(res_id)

    form = EmailRes()

    if form.validate_on_submit:
        EMAIL_TO = form.email_res.data,
        msg = EmailMessage()
        msg['Subject'] = f'Booking confirmation {res.id}'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_TO
        msg.set_content('This is a plain text email')

        lines = []

        with open("email.txt") as f:
            lines = f.readlines()
          
        email_string = ' '.join(lines)
        
        email_string = email_string.replace('{first_name}', user.first_name)
        email_string = email_string.replace('{last_name}', user.last_name)
        email_string = email_string.replace('{phone}', user.phone)
        email_string = email_string.replace('{conf}', str(res.id))
        email_string = email_string.replace('{PU_date}', res.PU_date.strftime('%A, %B %d, %Y'))
        email_string = email_string.replace('{PU_time}', res.PU_time.strftime('%I:%M %p'))
        email_string = email_string.replace('{passenger_name}', res.passenger_name)
        email_string = email_string.replace('{passenger_phone}', res.passenger_phone)
        email_string = email_string.replace('{vehicle_type}', res.vehicle_type)
        email_string = email_string.replace('{PU_date}', res.PU_date.strftime('%m/%d/%Y'))
        email_string = email_string.replace('{PU_time}', res.PU_time.strftime('%I:%M %p'))
        email_string = email_string.replace('{PU_address}', res.PU_address)
        email_string = email_string.replace('{DO_address}', res.DO_address)
        email_string = email_string.replace('{trip_notes}', res.trip_notes)

        # print(email_string)

        msg.add_alternative(email_string, subtype='html')
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    
        return redirect(f'/users/{user.id}')


#################################################################################
############## System Administrator routes ##################
#################################################################################

@app.route('/admin/register_admin', methods=['GET', 'POST'])
def register_admin():
    '''Register administrator to the system.'''

    if CURR_ADMIN_KEY in session:
        del session[CURR_ADMIN_KEY]

    form = AdminRegisterForm()

    if form.validate_on_submit():
        try:
            user = User.registerAdmin(
                username = form.username.data,
                password = form.password.data,
                email = form.email.data,
                first_name = form.first_name.data,
                last_name = form.last_name.data,
                phone = form.phone.data,
                is_admin = form.is_admin.data
            )
            db.session.commit()
            # admin_role = db.session.query(Role).filter_by(name='Admin').first()
            # admin.roles.append(admin_role)
            # db.session.commit()

        except exc.SQLAlchemyError:
            flash('Username or E-mail are taken! Please check the form and try again.', 'danger')
            return render_template('/admin/register_admin.html', form=form)
        
        session[CURR_ADMIN_KEY] = user.id
        flash('Welcome! Your admin account has been created successfully!', 'success')

        return redirect(f'/admin/admin_home')
    else:
        return render_template('admin/register_admin.html', form=form)


@app.route('/admin/admin_home')
def admin_home():
    '''Dispatch view page for admin users.'''

    if CURR_ADMIN_KEY not in session:
        raise Unauthorized()

    reservations = Reservation.query.all()
    users = User.query.all()
    
    return render_template('admin/admin_home.html', reservations=reservations, users=users)


@app.route('/admin/admin_edit_res/<int:res_id>')
def admin_show_edit_res(res_id):
    '''Display the form for editing reservation'''

    if CURR_ADMIN_KEY not in session:
        raise Unauthorized()

    res_id = Reservation.query.get_or_404(res_id)
    form = ResForm(obj=res_id)
    return render_template('/admin/admin_edit_res.html', res_id=res_id, form=form)


@app.route('/admin/admin_edit_res/<int:res_id>', methods=['POST'])
def admin_edit_res(res_id):
    '''Edit a reservation '''

    if CURR_ADMIN_KEY not in session:
        raise Unauthorized()

    res_id = Reservation.query.get_or_404(res_id)
    form = ResForm(obj=res_id)

    if form.validate_on_submit():
        res_id.passenger_name = form.passenger_name.data,
        res_id.passenger_phone = form.passenger_phone.data,
        res_id.passenger_email = form.passenger_email.data,
        res_id.vehicle_type = form.vehicle_type.data,
        res_id.PU_date = form.PU_date.data,
        res_id.PU_time = form.PU_time.data,
        res_id.PU_address = form.PU_address.data,
        res_id.PU_street = form.PU_street.data,
        res_id.PU_city = form.PU_city.data,
        res_id.PU_state = form.PU_state.data,
        res_id.PU_zip = form.PU_zip.data,
        res_id.PU_country = form.PU_country.data,
        res_id.DO_address = form.DO_address.data,
        res_id.DO_street = form.DO_street.data,
        res_id.DO_city = form.DO_city.data,
        res_id.DO_state = form.DO_state.data,
        res_id.DO_zip = form.DO_zip.data,
        res_id.DO_country = form.DO_country.data,
        res_id.trip_notes = form.trip_notes.data,

        db.session.commit()
        flash('Reservation has been updated.', 'success')
        return redirect(f'/admin/admin_home')


@app.route('/admin/select_user')
def select_user():
    '''Select a user to create a reservation'''

    if CURR_ADMIN_KEY not in session:
        raise Unauthorized()

    users = User.query.all()
    return render_template('admin/select_user.html', users=users)



@app.route('/admin/new_res/<int:user_id>')
def new_res_form(user_id):
    '''Display the form for an admin to submit a new reservation.'''

    if CURR_ADMIN_KEY not in session:
        raise Unauthorized()

    user = User.query.get(user_id)
    user_id = user.id
    form = ResForm()

    return render_template('admin/new_res.html', user_id=user_id, form=form, user=user)

    
@app.route('/admin/new_res/<int:user_id>', methods=['POST'])
def new_res(user_id):
    '''Allow admin to create a new reservation to an existing user.'''

    if CURR_ADMIN_KEY not in session:
        raise Unauthorized()
    
    user_id = User.query.get(user_id)
    user = user_id
    form = ResForm()

    if form.validate_on_submit():
        passenger_name = form.passenger_name.data,
        passenger_phone = form.passenger_phone.data,
        passenger_email = form.passenger_email.data,
        vehicle_type = form.vehicle_type.data,
        PU_date = form.PU_date.data,
        PU_time = form.PU_time.data,
        PU_address = form.PU_address.data,
        PU_street = form.PU_street.data,
        PU_city = form.PU_city.data,
        PU_state = form.PU_state.data,
        PU_zip = form.PU_zip.data,
        PU_country = form.PU_country.data,
        DO_address = form.DO_address.data,
        DO_street = form.DO_street.data,
        DO_city = form.DO_city.data,
        DO_state = form.DO_state.data,
        DO_zip = form.DO_zip.data,
        DO_country = form.DO_country.data,
        trip_notes = form.trip_notes.data,

        new_res = Reservation(
            passenger_name = passenger_name,
            passenger_phone = passenger_phone,
            passenger_email = passenger_email,
            vehicle_type = vehicle_type,
            PU_date = PU_date,
            PU_time = PU_time,
            PU_address = PU_address,
            PU_street = PU_street,
            PU_city = PU_city,
            PU_state = PU_state,
            PU_zip = PU_zip,
            PU_country = PU_country,
            DO_address = DO_address,
            DO_street = DO_street,
            DO_city = DO_city,
            DO_state = DO_state,
            DO_zip = DO_zip,
            DO_country = DO_country,
            trip_notes = trip_notes,
        )

        user.reservations.append(new_res)

        db.session.commit()
        flash('Reservation has been successfully submitted!', 'success')

        return redirect(url_for('admin_home'))