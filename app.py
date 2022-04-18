from datetime import date
from time import strftime
from flask import Flask, jsonify, render_template, redirect, flash, session, g, request, url_for
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.exceptions import Unauthorized
from forms import EmailRes, RegisterForm, LoginForm, ResForm, UserEditForm
from models import db, connect_db, User, Reservation
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
EMAIL_ADDRESS = em_user
EMAIL_PASSWORD = em_pass

connect_db(app)
# db.drop_all()
# db.create_all()

###########################################################################
# Homepage and error handling

@app.route('/')
def homepage():
    '''Display homepage'''

    return render_template('home.html')


@app.errorhandler(404)
def page_not_found(e):
    '''Page not found (404 error)'''

    return render_template('users/404.html'), 404


@app.errorhandler(401)
def not_allowed(e):
    '''Show 401 page for not authorized users.'''

    return render_template('users/401.html'), 401



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

    if CURR_USER_KEY in session:
        return redirect(f'/users/{g.user.id}')

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



############# API to check if user already exists in the database ############
@app.route('/check/<username>', methods=['GET'])
def check_user(username):
    
    user = User.query.filter_by(username=username).first()
    is_valid = True
    if user:
        is_valid = False
    return jsonify({"exists": is_valid})

############# API to check if phone number already exists in the database ############
@app.route('/verify/<phone>', methods=['GET'])
def check_phone(phone):
    
    phone_num = User.query.filter_by(phone=phone).first()
    is_avail = True
    if phone_num:
        is_avail = False
    return jsonify({"exists": is_avail})

############# API to check if email already exists in the database ############
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

    if not g.user:
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

    if not g.user:
        raise Unauthorized()

    form = ResForm()
    ############### will need to add the vehicle type to the reservation's database ############
    ######### the add the vehicle select field to the res form. #################

    if form.validate_on_submit():
        passenger_name = form.passenger_name.data,
        passenger_phone = form.passenger_phone.data,
        passenger_email = form.passenger_email.data,
        vehicle_type = form.vehicle_type.data,
        PU_date = form.PU_date.data,
        PU_time = form.PU_time.data,
        PU_address = form.PU_address.data,
        PU_address_2 = form.PU_address_2.data,
        PU_city = form.PU_city.data,
        PU_state = form.PU_state.data,
        PU_zip = form.PU_zip.data,
        PU_country = form.PU_country.data,
        DO_address = form.DO_address.data,
        DO_address_2 = form.DO_address_2.data,
        DO_city = form.DO_city.data,
        DO_state = form.DO_state.data,
        DO_zip = form.DO_zip.data,
        DO_country = form.DO_country.data,
        notes = form.notes.data,

        new_res = Reservation(
            passenger_name = passenger_name,
            passenger_phone = passenger_phone,
            passenger_email = passenger_email,
            vehicle_type = vehicle_type,
            PU_date = PU_date,
            PU_time = PU_time,
            PU_address = PU_address,
            PU_address_2 = PU_address_2,
            PU_city = PU_city,
            PU_state = PU_state,
            PU_zip = PU_zip,
            PU_country = PU_country,
            DO_address = DO_address,
            DO_address_2 = DO_address_2,
            DO_city = DO_city,
            DO_state = DO_state,
            DO_zip = DO_zip,
            DO_country = DO_country,
            notes = notes,
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

    if not g.user:
        raise Unauthorized()

    res_id = Reservation.query.get_or_404(res_id)
    form = ResForm(obj=res_id)
    return render_template('/res/edit_res.html', res_id=res_id, form=form)


@app.route('/res/edit_res/<int:res_id>', methods=['POST'])
def edit_res(res_id):
    '''Edit a reservation '''

    if not g.user:
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
        res_id.PU_address_2 = form.PU_address_2.data,
        res_id.PU_city = form.PU_city.data,
        res_id.PU_state = form.PU_state.data,
        res_id.PU_zip = form.PU_zip.data,
        res_id.PU_country = form.PU_country.data,
        res_id.DO_address = form.DO_address.data,
        res_id.DO_address_2 = form.DO_address_2.data,
        res_id.DO_city = form.DO_city.data,
        res_id.DO_state = form.DO_state.data,
        res_id.DO_zip = form.DO_zip.data,
        res_id.DO_country = form.DO_country.data,
        res_id.notes = form.notes.data,

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

        msg.add_alternative(f'''\
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Booking Confirmation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" 
    integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" 
    integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
    <link rel="stylesheet" href="https://use.fontawesome.com/releases/v6.1.0/css/all.css"
        integrity="sha384-eLT4eRYPHTmTsFGFAzjcCWX+wHfUInVWNm9YnwpiatljsZOwXtwV2Hh6sHM6zZD9" 
        crossorigin="anonymous" />
</head>
<body>
  <div class="container">
    <h3 class="text-center my-5">Booking Confirmation</h1>
    <div class="container px-4">
        <div class="row gx-5 my-5">
          <div class="col">
           <div class="p-3">
               <img src="" alt="Company Logo">
               <h6 class="fw-bold text-start">Company info</h6>
           </div>
          </div>
          <div class="col">
            <div class="p-3">
              
              {{% if user %}}
           <p class="fs-5 text-end">Customer: {{user.first_name}} {{user.last_name}}</p>
           <p class="fs-5 text-end">Phone: {{user.phone}}</p>
                {{% endif %}}
                
            </div>
          </div>
        </div>
      </div>

      <hr>

      <table class="table">
        <thead>
            <tr class="table-active">
              <th scope="col">Conf #</th>
              <th scope="col">Date</th>
              <th scope="col">Time</th>
              <th scope="col">Passenger</th>
              <th scope="col">Passenger Cell#</th>
              <th scope="col">Vehicle Type</th>
            </tr>
          </thead>
          {{% if res_id %}}
           
          <tbody>
            <tr>
                <td>{{res_id.id}}</td>
                <td>{{res_id.PU_date.strftime('%A, %B %d, %Y')}}</td>
                <td>{{res_id.PU_time.strftime('%I:%M %p')}}</td>
                <td>{{res_id.passenger_name}}</td>
                <td>{{res_id.passenger_phone}}</td>
                <td>{{res_id.vehicle_type}} </td>
              </tr>

          </tbody>
      </table>

      <div class="row g-0">
        <div class="border bg-dark bg-opacity-25 fw-bold text-center my-2">Service Details</div>
      </div>
      <div class="row g-2">
        <div class="col-2 p-2 border bg-light">Pick-Up:</div>
        <div class="col-3 border bg-light text-center">{{res_id.PU_date.strftime('%m/%d/%Y')}} - {{res_id.PU_time.strftime('%I:%M %p')}}</div>
        <div class="col-7 border bg-light">{{res_id.PU_address}}</div>
      </div>

      <!-- consider adding stops in between here!!!!!!!!! -->

      <div class="row g-2">
        <div class="col-2 p-2 border bg-light">Drop-Off:</div>
        <div class="col-3 border bg-light text-center"></div>
        <div class="col-7 border bg-light">{{res_id.DO_address}} {{res_id.DO_city}} {{res_id.DO_state}} {{res_id.DO_zip}}</div>
      </div>
      <div class="row g-0">
        <div class="border bg-dark bg-opacity-25 fw-bold text-center my-2">Trip notes</div>
        <div class="row g-12">{{res_id.notes}}</div>
      </div>
      <hr>
         
      <!-- Add amount and anything else needed here -->
      
          {{% endif %}}
  </div>
  
</body>
</html>
        ''', subtype='html')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    
        return redirect(f'/users/{user.id}')
