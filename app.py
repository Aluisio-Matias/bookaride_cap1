from datetime import date
from time import strftime
from flask import Flask, jsonify, render_template, redirect, flash, session, g, request, url_for
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.exceptions import Unauthorized
from forms import EmailRes, RegisterForm, LoginForm, ResForm, UserEditForm, AdminForm, AdminLoginForm
from models import db, connect_db, User, Reservation, Admin
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc
from secret import em_user, em_pass
import smtplib
from email.message import EmailMessage
import os


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///project_test'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.debug = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

CURR_USER_KEY = "curr_user"
CURR_ADMIN_KEY = "curr_admin"
EMAIL_ADDRESS = em_user
EMAIL_PASSWORD = em_pass

connect_db(app)
# db.drop_all()
# db.create_all()

###########################################################################
# Homepage and error handling

@app.route('/')
def homepage():
    '''Display User's homepage'''

    return render_template('home.html')

@app.route('/admin/admin_home')
def admin_homepage():
    '''Display Admin's homepage'''
    return render_template('/admin/admin_home.html')

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

@app.before_request
def add_user_to_g():
    '''If user is logged in, add current user to Flask Global.'''
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def do_login(user):
    '''Login the user.'''
    session[CURR_USER_KEY] = user.id

def do_logout():
    '''Logout current user.'''
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

######## Admin routes for register / login / logout ############
def add_admin_to_g():
    '''If admin is logged in, and current admin to Flask Global.'''
    if CURR_ADMIN_KEY in session:
        g.user = Admin.query.get(session[CURR_ADMIN_KEY])
    else:
        g.user = None

def do_admin_login(admin):
    '''Login the admin user'''
    session[CURR_ADMIN_KEY] = admin.id

def do_admin_logout():
    '''Logout current Admin user.'''
    if CURR_ADMIN_KEY in session:
        del session[CURR_ADMIN_KEY]
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

        # except IntegrityError:
        except exc.SQLAlchemyError:
            
            flash('Username, E-mail, or Phone number is taken! Please check the form and try again.', 'danger')
            return render_template('users/register.html', form=form)
        
        do_login(user)
        flash('Welcome! Your account has been created successfully!', 'success')

        return redirect(f'/users/{user.id}')
    else:
        return render_template('users/register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''Show the page to login existing users.'''

    form = LoginForm()

    # if CURR_USER_KEY in session:
    #     return redirect(f'/users/{g.user.id}')

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                form.password.data)
        if user:
            do_login(user)
            flash(f'Hello, Welcome back {user.first_name}!', 'success')
            return redirect(f'/users/{user.id}')
        flash("Invalid credentials, please try again!", 'danger')
        
    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    '''Handle logout of a user.'''
    session.pop(CURR_USER_KEY)

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
############# API to check if admin username already exists in the admin database ############
@app.route('/check_admin/<admin_username>', methods=['GET'])
def check_admin(admin_username):
    
    user = Admin.query.filter_by(admin_username=admin_username).first()
    is_valid = True
    if user:
        is_valid = False
    return jsonify({"exists": is_valid})

############# API to check if email already exists in the users database ############
@app.route('/verify_admin/<admin_email>', methods=['GET'])
def admin_email(admin_email):
    
    ck_email = Admin.query.filter_by(admin_email=admin_email).first()
    valid = True
    if ck_email:
        valid = False
    return jsonify({"exists": valid})

################################################################################


#############################################################################
# User route for user's page / edit profile / reservations

@app.route('/users/<int:id>')
def show_user(id):
    '''Page for logged in users.'''

    if CURR_USER_KEY not in session:
        raise Unauthorized()

    user = User.query.get_or_404(id)

    reservations = Reservation.query.all()
    
    return render_template('users/show_user.html', user=user, reservations=reservations)



@app.route('/users/edit_profile/<int:id>', methods=['GET', 'POST'])
def edit_profile(id):
    '''Update a profile from a current user.'''

    if CURR_USER_KEY not in session:
        raise Unauthorized()

    user = g.user
    id = User.query.get_or_404(id)
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

    return render_template('users/edit_profile.html', form=form, user_id=user.id, id=id)


#############################################################################
# Reservations routes 

@app.route('/res', methods=['POST', 'GET'])
def res_form():
    '''Show form to submit a reservation.'''

    if CURR_USER_KEY not in session:
        raise Unauthorized()

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

        g.user.reservations.append(new_res)
        db.session.commit()
        flash('Your reservation has been successfully submitted!', 'success')

        return redirect(f'/users/{g.user.id}')
    else:
        return render_template('res/res_form.html', form=form)


################ routes to edit reservations ###########################
@app.route('/res/edit_res/<int:res_id>')
def show_edit_res(res_id):
    '''Display the form for editing the reservation'''

    if CURR_USER_KEY not in session:
        raise Unauthorized()

    res_id = Reservation.query.get_or_404(res_id)
    form = ResForm(obj=res_id)
    return render_template('/res/edit_res.html', res_id=res_id, form=form)


@app.route('/res/edit_res/<int:res_id>', methods=['POST'])
def edit_res(res_id):
    '''Edit a reservation '''

    if CURR_USER_KEY not in session:
        raise Unauthorized()

    user = g.user
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
        flash('Your reservation has been updated.', 'success')
        return redirect(f'/users/{user.id}')



################# reservation view route ####################
@app.route('/res/view/<int:res_id>')
def view_res(res_id):
    '''display reservation details in HTML'''

    if CURR_USER_KEY not in session:
        raise Unauthorized()

    user = g.user
    res_id = Reservation.query.get_or_404(res_id)


    return render_template('/res/view_res.html', res_id=res_id, user=user)


################ email reservation routes ###################

@app.route('/res/email_res_form/<int:res_id>')
def email_res_form(res_id):
    '''Display a form so a user can email the booking confirmation'''

    if CURR_USER_KEY not in session:
        raise Unauthorized()

    user = g.user
    res_id = Reservation.query.get_or_404(res_id)
    form = EmailRes()
    return render_template('/res/email_res.html', user=user, res_id=res_id, form=form)


@app.route('/res/email_res_form/<int:res_id>', methods=['POST'])
def email_res(res_id):
    '''Display a form so a user can email the booking confirmation'''

    if CURR_USER_KEY not in session:
        raise Unauthorized()

    user = g.user
    res_id = Reservation.query.get_or_404(res_id)

    form = EmailRes()

    if form.validate_on_submit:
        EMAIL_TO = form.email_res.data,
        msg = EmailMessage()
        msg['Subject'] = f'Booking confirmation {res_id.id}'
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
        email_string = email_string.replace('{conf}', str(res_id.id))
        email_string = email_string.replace('{PU_date}', res_id.PU_date.strftime('%A, %B %d, %Y'))
        email_string = email_string.replace('{PU_time}', res_id.PU_time.strftime('%I:%M %p'))
        email_string = email_string.replace('{passenger_name}', res_id.passenger_name)
        email_string = email_string.replace('{passenger_phone}', res_id.passenger_phone)
        email_string = email_string.replace('{vehicle_type}', res_id.vehicle_type)
        email_string = email_string.replace('{PU_date}', res_id.PU_date.strftime('%m/%d/%Y'))
        email_string = email_string.replace('{PU_time}', res_id.PU_time.strftime('%I:%M %p'))
        email_string = email_string.replace('{PU_address}', res_id.PU_address)
        email_string = email_string.replace('{DO_address}', res_id.DO_address)
        email_string = email_string.replace('{trip_notes}', res_id.trip_notes)

        # print(email_string)

        msg.add_alternative(email_string, subtype='html')
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    
        return redirect(f'/users/{user.id}')



############## System Administrator routes ##################

@app.route('/admin/register_admin', methods=['GET', 'POST'])
def register_admin():
    '''Register administrator to the system.'''

    if CURR_ADMIN_KEY in session:
        del session[CURR_ADMIN_KEY]

    form = AdminForm()

    if form.validate_on_submit():
        try:
            admin = Admin.register_admin(
                admin_username=form.admin_username.data,
                password=form.password.data,
                admin_email=form.admin_email.data,
            )
            db.session.commit()

        except exc.SQLAlchemyError:
            flash('Username or E-mail are taken! Please check the form and try again.', 'danger')
            return render_template('/admin/register_admin.html', form=form)

        do_admin_login(admin)
        flash('Welcome! Your admin account has been created successfully!', 'success')

        return redirect(f'/admin/admin_home/{admin.id}')
    else:
        return render_template('admin/register_admin.html', form=form)


@app.route('/admin/admin_login', methods=['GET', 'POST'])
def admin_login():
    '''Display the page to login an admin user'''
    
    form = AdminLoginForm()

    if form.validate_on_submit():
        admin = Admin.authenticate_admin(form.admin_username.data,
                                form.password.data)
        if admin:
            do_login(admin)
            flash(f'Hello, Welcome back {admin.admin_username}!', 'success')
            return redirect(f'/admin/admin_home/{admin.id}')
        flash("Invalid credentials, please try again!", 'danger')
        
    return render_template('admin/admin_login.html', form=form)


@app.route('/admin/admin_logout')
def admin_logout():
    '''Handle logout of a user.'''
    session.pop(CURR_ADMIN_KEY)

    do_admin_logout()

    flash('You have been successfully logged out!', 'success')

    return redirect('/')


@app.route('/admin/admin_home/<int:admin_id>')
def show_admin(admin_id):
    '''Dispatch view page for admin users.'''

    if CURR_ADMIN_KEY not in session:
        raise Unauthorized()

    admin = Admin.query.get_or_404(admin_id)
    reservations = Reservation.query.all()
    users = User.query.all()
    
    return render_template('admin/admin_home.html', admin=admin, reservations=reservations, users=users)


@app.route('/admin/edit_admin/<int:admin_id>', methods=['GET', 'POST'])
def edit_admin(admin_id):
    '''Update admin profile'''

    if CURR_ADMIN_KEY not in session:
        raise Unauthorized()

    admin = g.user
    admin_id = Admin.query.get_or_404(admin_id)
    form = AdminForm(obj=admin)

    if form.validate_on_submit():
        if Admin.authenticate_admin(admin.admin_username, form.password.data):
            admin.admin_username = form.admin_username.data
            admin.admin_email = form.admin_email.data
            admin.company_name = form.company_name.data
            admin.company_phone = form.company_phone.data
            admin.company_email = form.company_email.data
            admin.company_website = form.company_website.data
            admin.logo_url = form.logo_url.data

            db.session.commit()
            return redirect(f'/admin/admin_home/{admin.id}')

        flash('Wrong password, please try again!', 'danger')

    return render_template('/admin/edit_admin.html', form=form, admin_id=admin_id, admin=admin)


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

    user = g.user
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
        return redirect(f'/admin/admin_home/{user.id}')



