'''Testing for User model'''

#to run these tests us: FLASK_ENV=production python -m unittest test_user_model.py

import os 
from unittest import TestCase
from sqlalchemy import exc

from models import db, User

#Before importing the app.py, create an evironmental var to use a different database for tests
os.environ['DATABASE_URL'] = "postgresql:///book_a_ride_test"

from app import app

db.create_all()

class UserModelTestCase(TestCase):

    def setUp(self):
        '''Create test user, add sample data'''
        db.drop_all()
        db.create_all()

        user1 = User.register("Test-User1", 
                            "test-password", 
                            "testuser1@testing.com", 
                            "Test", "User1", 
                            "555-555-5555")
        user1id = 2
        user1.id = user1id

        user2 = User.register("Test-User2", 
                            "testing-password", 
                            "testuser2@testing.com", 
                            "Test2", 
                            "User2", 
                            "777-555-5555")
        user2id = 3
        user2.id = user2id

        db.session.commit()

        user1 = User.query.get(user1id)
        user2 = User.query.get(user2id)

        self.user1 = user1
        self.user1id = user1id

        self.user2 = user2
        self.user2id = user2id

        self.client = app.test_client()

    def tearDown(self) -> None:
        result =  super().tearDown()
        db.session.rollback()
        return result

    ######### Test if user model works #############################    
    def test_user_model(self):
        user = User(
            username = "Tester",
            password = "HASHED-PASSWORD",
            email = "tester@email.com",
            first_name = "Tester",
            last_name = "User",
            phone = "777-777-7777"
        )

        db.session.add(user)
        db.session.commit()

    ########### Tests for signup feature ############################
    def test_valid_signup(self):
        user_test = User.register('testuser', 
                                'anypassword', 
                                'tester@testing.com', 
                                'Test', 
                                'User', 
                                '454-454-4545')
        user_test_id = 4
        user_test.id = user_test_id
        db.session.commit()

        user_test = User.query.get(user_test_id)
        self.assertIsNotNone(user_test)
        self.assertEqual(user_test.username, 'testuser')
        self.assertEqual(user_test.email, 'tester@testing.com')
        ##since password should be hashed, test if password is NOT equal to what user entered###
        self.assertNotEqual(user_test.password, 'anypassword')
        ## Test if hashed password using Bcrypt starts with $2b$ ##
        self.assertTrue(user_test.password.startswith('$2b$'))

    ########### Test if register proccess will raise errors if fields are missing or wrong during sign up############
    def test_invalid_username_signup(self):
        invalid_user = User.register(None, 
                                    'password', 
                                    'invalid_test@testing.com', 
                                    None, 
                                    None, 
                                    None)
        user_id = 55
        invalid_user.id = user_id
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        invalid_user2 = User.register('invalid', 
                                    'anypassword', 
                                    None, 
                                    'Any', 
                                    'Name', 
                                    '111-222-3333')
        user_id = 56
        invalid_user2.id = user_id
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password(self):
        with self.assertRaises(ValueError) as context:
            User.register('invalid',
                         '',
                         'testing@test.com', 
                         'Any', 'Name', 
                         '111-222-3333')

        with self.assertRaises(ValueError) as context:
            User.register('invalid', 
                        None, 
                        'testing@test.com', 
                        'Any', 
                        'Name', 
                        '111-222-3333')

    ###### Authentication Tests #######################
    def test_valid_authentication(self):
        u = User.authenticate(self.user1.username, 'password')
        self.assertIsNotNone(u)
        self.assertEqual(self.user1.id, self.user1id)

    def test_invalid_username(self):
        self.assertFalse(User.authenticate('badusername', 'password'))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.user1.username, 'wrongpassword'))