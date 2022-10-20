# Copyright 2016, 2021 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Wishlists Models

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_wishlists.py:TestwishlistModel

"""
import os
import logging
import unittest
from werkzeug.exceptions import NotFound
from service.models import Wishlists, DataValidationError, db,
from service import app
from tests.factories import WishlistsFactory
import datetime

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  WISHLISTS   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestWishlistsModel(unittest.TestCase):
    """Test Cases for wishlist Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Wishlists.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Wishlists).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_wishlist(self):
        """It should Create a wishlist and assert that it exists"""
        current_time = datetime.datetime.now()
        wishlist = Wishlists(name="wishlist-1", customer_id=1, created_on=current_time)
        self.assertEqual(str(wishlist), "<Wishlist 'wishlist-1' id=[None]>")
        self.assertTrue(wishlist is not None)
        self.assertEqual(wishlist.id, None)
        self.assertEqual(wishlist.name, "wishlist-1")
        self.assertEqual(wishlist.customer_id, 1)
        self.assertEqual(wishlist.created_on, current_time)

    def test_add_a_wishlist(self):
        """It should Create a wishlist and add it to the database"""
        wishlists = Wishlists.all()
        self.assertEqual(wishlists, [])
        current_time = datetime.datetime.now()
        wishlist = Wishlists(name="wishlist-1", customer_id=1, created_on=current_time)
        self.assertTrue(wishlist is not None)
        self.assertEqual(wishlist.id, None)
        wishlist.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(wishlist.id)
        wishlists = Wishlists.all()
        self.assertEqual(len(wishlists), 1)

    def test_read_a_wishlist(self):
        """It should Read a wishlist"""
        wishlist = WishlistsFactory()
        logging.debug(wishlist)
        wishlist.id = None
        wishlist.create()
        self.assertIsNotNone(wishlist.id)
        # Fetch it back
        found_wishlist = Wishlists.find(wishlist.id)
        self.assertEqual(found_wishlist.id, wishlist.id)
        self.assertEqual(found_wishlist.name, wishlist.name)
        self.assertEqual(found_wishlist.customer_id, wishlist.customer_id)
        self.assertEqual(found_wishlist.created_on, wishlist.created_on)

    def test_update_a_wishlist(self):
        """It should Update a wishlist"""
        wishlist = WishlistsFactory()
        logging.debug(wishlist)
        wishlist.id = None
        wishlist.create()
        logging.debug(wishlist)
        self.assertIsNotNone(wishlist.id)
        # Change it an save it
        wishlist.customer_id = 2
        original_id = wishlist.id
        wishlist.update()
        self.assertEqual(wishlist.id, original_id)
        self.assertEqual(wishlist.customer_id, 2)
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        wishlists = Wishlists.all()
        self.assertEqual(len(wishlists), 1)
        self.assertEqual(wishlists[0].id, original_id)
        self.assertEqual(wishlists[0].customer_id, 2)

    def test_update_no_id(self):
        """It should not Update a wishlist with no id"""
        wishlist = WishlistsFactory()
        logging.debug(wishlist)
        wishlist.id = None
        self.assertRaises(DataValidationError, wishlist.update)

    def test_delete_a_wishlist(self):
        """It should Delete a wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        self.assertEqual(len(Wishlists.all()), 1)
        # delete the wishlist and make sure it isn't in the database
        wishlist.delete()
        self.assertEqual(len(Wishlists.all()), 0)

    def test_list_all_wishlists(self):
        """It should List all wishlists in the database"""
        wishlists = Wishlists.all()
        self.assertEqual(wishlists, [])
        # Create 5 wishlists
        for _ in range(5):
            wishlist = WishlistsFactory()
            wishlist.create()
        # See if we get back 5 wishlists
        wishlists = Wishlists.all()
        self.assertEqual(len(wishlists), 5)

    def test_serialize_a_wishlist(self):
        """It should serialize a wishlist"""
        wishlist = WishlistsFactory()
        data = wishlist.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], wishlist.id)
        self.assertIn("name", data)
        self.assertEqual(data["name"], wishlist.name)
        self.assertIn("customer_id", data)
        self.assertEqual(data["customer_id"], wishlist.customer_id)
        self.assertIn("created_on", data)
        self.assertEqual(data["created_on"], wishlist.created_on)

    def test_deserialize_a_wishlist(self):
        """It should de-serialize a wishlist"""
        data = WishlistsFactory().serialize()
        wishlist = Wishlists()
        wishlist.deserialize(data)
        self.assertNotEqual(wishlist, None)
        self.assertEqual(wishlist.id, None)
        self.assertEqual(wishlist.name, data["name"])
        self.assertEqual(wishlist.customer_id, data["customer_id"])
        self.assertEqual(wishlist.created_on, data["created_on"])

    def test_deserialize_missing_data(self):
        """It should not deserialize a wishlist with missing data"""
        data = {"id": 1, "name": "Kitty"}
        wishlist = Wishlists()
        self.assertRaises(DataValidationError, wishlist.deserialize, data)

    def test_deserialize_bad_data(self):
        """It should not deserialize bad data"""
        data = "this is not a dictionary"
        wishlist = Wishlists()
        self.assertRaises(DataValidationError, wishlist.deserialize, data)

    def test_deserialize_bad_customer_id(self):
        """It should not deserialize a bad customer_id attribute"""
        test_wishlist = WishlistsFactory()
        data = test_wishlist.serialize()
        data["customer_id"] = "1"
        wishlist = Wishlists()
        self.assertRaises(DataValidationError, wishlist.deserialize, data)

    def test_find_wishlist(self):
        """It should Find a Wishlist by ID"""
        wishlists = WishlistsFactory.create_batch(5)
        for wishlist in wishlists:
            wishlist.create()
        logging.debug(wishlists)
        # make sure they got saved
        self.assertEqual(len(Wishlists.all()), 5)
        # find the 2nd wishlist in the list
        wishlist = Wishlists.find(wishlists[1].id)
        self.assertIsNot(wishlist, None)
        self.assertEqual(wishlist.id, wishlists[1].id)
        self.assertEqual(wishlist.name, wishlists[1].name)
        self.assertEqual(wishlist.customer_id, wishlists[1].customer_id)
        self.assertEqual(wishlist.created_on, wishlists[1].created_on)

    def test_find_by_customer_id(self):
        """It should Find Wishlists by Category"""
        wishlists = WishlistsFactory.create_batch(10)
        for wishlist in wishlists:
            wishlist.create()
        customer_id = wishlists[0].customer_id
        count = len([wishlist for wishlist in wishlists if wishlist.customer_id == customer_id])
        found = Wishlists.find_by_customer_id(customer_id)
        self.assertEqual(found.count(), count)
        for wishlist in found:
            self.assertEqual(wishlist.customer_id, customer_id)

    def test_find_by_name(self):
        """It should Find a Wishlist by Name"""
        wishlists = WishlistsFactory.create_batch(5)
        for wishlist in wishlists:
            wishlist.create()
        name = wishlists[0].name
        found = Wishlists.find_by_name(name)
        self.assertEqual(found.count(), 1)
        self.assertEqual(found[0].customer_id, wishlists[0].customer_id)
        self.assertEqual(found[0].created_on, wishlists[0].created_on)

    def test_find_or_404_found(self):
        """It should Find or return 404 not found"""
        wishlists = WishlistsFactory.create_batch(3)
        for wishlist in wishlists:
            wishlist.create()

        wishlist = Wishlists.find_or_404(wishlists[1].id)
        self.assertIsNot(wishlist, None)
        self.assertEqual(wishlist.id, wishlists[1].id)
        self.assertEqual(wishlist.name, wishlists[1].name)
        self.assertEqual(wishlist.customer_id, wishlists[1].customer_id)
        self.assertEqual(wishlist.created_on, wishlists[1].created_on)

    def test_find_or_404_not_found(self):
        """It should return 404 not found"""
        self.assertRaises(NotFound, Wishlists.find_or_404, 0)
