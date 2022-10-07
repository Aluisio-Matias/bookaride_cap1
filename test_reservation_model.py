'''Testing for Reservation model'''

#to run these tests us: FLASK_ENV=production python -m unittest test_reservation_model.py

import os 
from unittest import TestCase
from werkzeug.exceptions import Unauthorized

from models import db, Reservation, User

#Before importing the app.py, create an evironmental var to use a different database for tests
os.environ['DATABASE_URL'] = "postgresql:///book_a_ride_test"

from app import CURR_USER_KEY, app

db.create_all()

class ReservationModelTestCase(TestCase):

    def setUp(self):

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.register(username="testuser",
                                    password="anypassword",
                                    email="test@testing.org",
                                    first_name="Test",
                                    last_name="User",
                                    phone="123-456-7890")

        self.testuser_id = 100
        self.testuser.id = self.testuser_id

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_valid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/res/res_form')
            self.assertEqual(resp.status_code, 200)   


    def test_reservation_model(self):
        "Are you able to add a reservation?"

        res = Reservation(
                passenger_name="Test User",
                passenger_phone="987-654-3210",
                passenger_email="testuser@email.com",
                vehicle_type="Sedan",
                PU_time="00:00:00",
                PU_date="2022-07-15",
                PU_address="123 Main Street, San Francisco, CA, 94104",
                PU_street="Main Street",
                PU_city="San Francisco",
                PU_state="CA",
                PU_zip="94104",
                PU_country="USA",
                DO_address="101 California Street, San Francisco, CA 94104",
                DO_street="California Street",
                DO_city="San Francisco",
                DO_state="CA",
                DO_zip="94104",
                DO_country="USA",
                trip_notes=None
        )

        resId = 10001
        res.id = resId

        db.session.add(res)
        db.session.commit()


    def test_view_reservation_unauthorized(self):
        "Are you able to view reservations that doesn't belong to you?"

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/res/view/{10001}')

            self.assertEqual(resp.status_code, 404) #Unauthorized




  
                


