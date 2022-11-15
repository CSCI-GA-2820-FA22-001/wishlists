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
Test cases for items, Items Models

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_items.py:TestitemModel

"""
import os
import logging
import unittest
from werkzeug.exceptions import NotFound
from service.models import Wishlists, Items, DataValidationError, db
from service import app
from tests.factories import ItemsFactory, WishlistsFactory
import datetime

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  ITEMS   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestItemsModel(unittest.TestCase):
    """Test Cases for Items Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Items.init_db(app)
        Wishlists.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Items).delete()  # clean up the last tests
        db.session.query(Wishlists).delete()  # clean up the wishlists
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_item(self):
        """It should Create a item and assert that it exists"""
        current_time = datetime.datetime.now()
        item = Items(
            name="item-1",
            wishlist_id=1,
            rank=1,
            quantity=1,
            price=100,
            created_on=current_time,
            updated_on=current_time,
        )
        self.assertEqual(str(item), "<Items 'item-1' id=[None]>")
        self.assertTrue(item is not None)
        self.assertEqual(item.id, None)
        self.assertEqual(item.name, "item-1")
        self.assertEqual(item.wishlist_id, 1)
        self.assertEqual(item.rank, 1)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.price, 100)
        self.assertEqual(item.created_on, current_time)
        self.assertEqual(item.updated_on, current_time)

    def test_add_a_item(self):
        """It should Create a item and add it to the database"""
        items = Items.all()
        self.assertEqual(items, [])
        current_time = datetime.datetime.now()
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        item = Items(
            name="item-1",
            wishlist_id=wishlist.id,
            product_id=1,
            rank=1,
            quantity=1,
            price=100,
            created_on=current_time,
            updated_on=current_time,
        )
        self.assertTrue(item is not None)
        self.assertEqual(item.id, None)
        item.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(item.id)
        items = Items.all()
        self.assertEqual(len(items), 1)

    def test_read_a_item(self):
        """It should Read a item"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        item = ItemsFactory()
        logging.debug(item)
        item.id = None
        item.wishlist_id = wishlist.id
        item.create()
        self.assertIsNotNone(item.id)
        # Fetch it back
        found_item = Items.find(item.id)
        self.assertEqual(found_item.id, item.id)
        self.assertEqual(found_item.name, item.name)
        self.assertEqual(found_item.wishlist_id, item.wishlist_id)
        self.assertEqual(found_item.product_id, item.product_id)
        self.assertEqual(found_item.rank, item.rank)
        self.assertEqual(found_item.quantity, item.quantity)
        self.assertEqual(found_item.price, item.price)
        self.assertEqual(found_item.created_on, item.created_on)
        self.assertEqual(found_item.updated_on, item.updated_on)

    def test_update_a_item(self):
        """It should Update a item"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        item = ItemsFactory()
        item.wishlist_id = wishlist.id
        logging.debug(item)
        item.id = None
        item.product_id = 1
        item.create()
        logging.debug(item)
        self.assertIsNotNone(item.id)
        # Change it an save it
        item.product_id = 2
        original_id = item.id
        item.update()
        self.assertEqual(item.id, original_id)
        self.assertEqual(item.product_id, 2)
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        items = Items.all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, original_id)
        self.assertEqual(items[0].product_id, 2)

    def test_update_no_id(self):
        """It should not Update a item with no id"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        item = ItemsFactory()
        logging.debug(item)
        item.id = None
        item.wishlist_id = wishlist.id
        self.assertRaises(DataValidationError, item.update)

    def test_delete_a_item(self):
        """It should Delete a item"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        item = ItemsFactory()
        item.wishlist_id = wishlist.id
        item.create()
        self.assertEqual(len(Items.all()), 1)
        # delete the item and make sure it isn't in the database
        item.delete()
        self.assertEqual(len(Items.all()), 0)

    def test_list_all_items(self):
        """It should List all items in the database"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        items = Items.all()
        self.assertEqual(items, [])
        # Create 5 items
        for _ in range(5):
            item = ItemsFactory()
            item.wishlist_id = wishlist.id
            item.create()
        # See if we get back 5 items
        items = Items.all()
        self.assertEqual(len(items), 5)

    def test_serialize_a_item(self):
        """It should serialize a item"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        item = ItemsFactory()
        data = item.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], item.id)
        self.assertIn("name", data)
        self.assertEqual(data["name"], item.name)
        self.assertIn("wishlist_id", data)
        self.assertEqual(data["wishlist_id"], item.wishlist_id)
        self.assertIn("product_id", data)
        self.assertEqual(data["product_id"], item.product_id)
        self.assertIn("rank", data)
        self.assertEqual(data["rank"], item.rank)
        self.assertIn("price", data)
        self.assertEqual(data["price"], item.price)
        self.assertIn("quantity", data)
        self.assertEqual(data["quantity"], item.quantity)
        self.assertIn("created_on", data)
        self.assertEqual(data["created_on"], item.created_on)
        self.assertIn("updated_on", data)
        self.assertEqual(data["updated_on"], item.updated_on)

    def test_deserialize_a_item(self):
        """It should de-serialize a item"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        item = ItemsFactory()
        item.wishlist_id = wishlist.id
        data = item.serialize()
        item = Items()
        item.deserialize(data)
        self.assertNotEqual(item, None)
        self.assertEqual(item.id, None)
        self.assertEqual(data["name"], item.name)
        self.assertEqual(data["product_id"], item.product_id)
        self.assertEqual(data["wishlist_id"], item.wishlist_id)
        self.assertEqual(data["quantity"], item.quantity)
        self.assertEqual(data["price"], item.price)
        self.assertEqual(data["rank"], item.rank)

    def test_deserialize_missing_data(self):
        """It should not deserialize a item with missing data"""
        data = {"id": 1, "name": "item-1"}
        item = Items()
        self.assertRaises(DataValidationError, item.deserialize, data)

    def test_deserialize_bad_data(self):
        """It should not deserialize bad data"""
        data = "this is not a dictionary"
        item = Items()
        self.assertRaises(DataValidationError, item.deserialize, data)

    def test_deserialize_bad_wishlist_id(self):
        """It should not deserialize a bad customer_id attribute"""
        test_item = ItemsFactory()
        data = test_item.serialize()
        data["wishlist_id"] = "$"
        item = Items()
        self.assertRaises(DataValidationError, item.deserialize, data)

    def test_deserialize_bad_product_id(self):
        """It should not deserialize a bad customer_id attribute"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        test_item = ItemsFactory()
        data = test_item.serialize()
        data["product_id"] = "1"
        item = Items()
        self.assertRaises(DataValidationError, item.deserialize, data)

    def test_deserialize_bad_price(self):
        """It should not deserialize a bad customer_id attribute"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        test_item = ItemsFactory()
        data = test_item.serialize()
        data["price"] = "1"
        item = Items()
        app.logger.info(item.deserialize)
        self.assertRaises(DataValidationError, item.deserialize, data)

    def test_deserialize_bad_quantity(self):
        """It should not deserialize a bad customer_id attribute"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        test_item = ItemsFactory()
        data = test_item.serialize()
        data["quantity"] = "1"
        item = Items()
        self.assertRaises(DataValidationError, item.deserialize, data)

    def test_deserialize_bad_rank(self):
        """It should not deserialize a bad customer_id attribute"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        test_item = ItemsFactory()
        data = test_item.serialize()
        data["rank"] = "1"
        item = Items()
        self.assertRaises(DataValidationError, item.deserialize, data)

    def test_find_item(self):
        """It should Find a item by ID"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        items = ItemsFactory.create_batch(5)
        for item in items:
            item.wishlist_id = wishlist.id
            item.create()
        logging.debug(items)
        # make sure they got saved
        self.assertEqual(len(Items.all()), 5)
        # find the 2nd item in the list
        item = Items.find(items[1].id)
        self.assertIsNot(item, None)
        self.assertEqual(item.id, items[1].id)
        self.assertEqual(item.name, items[1].name)
        self.assertEqual(items[1].product_id, item.product_id)
        self.assertEqual(items[1].wishlist_id, item.wishlist_id)
        self.assertEqual(items[1].quantity, item.quantity)
        self.assertEqual(items[1].price, item.price)
        self.assertEqual(items[1].rank, item.rank)
        self.assertEqual(item.created_on, items[1].created_on)
        self.assertEqual(item.updated_on, items[1].updated_on)

    def test_find_by_wishlist_id(self):
        """It should Find items by wishlist id"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        items = ItemsFactory.create_batch(10)
        for item in items:
            item.wishlist_id = wishlist.id
            item.create()
        wishlist_id = items[0].wishlist_id
        count = len([item for item in items if item.wishlist_id == wishlist_id])
        found = Items.find_by_wishlist_id(wishlist_id)
        self.assertEqual(found.count(), count)
        for item in found:
            self.assertEqual(item.wishlist_id, wishlist_id)

    def test_find_by_name(self):
        """It should Find a item by Name"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        items = ItemsFactory.create_batch(5)
        for item in items:
            item.wishlist_id = wishlist.id
            item.create()
        name = items[0].name
        found = Items.find_by_name(name)
        self.assertEqual(found.count(), 1)
        self.assertEqual(found[0].wishlist_id, items[0].wishlist_id)
        self.assertEqual(found[0].created_on, items[0].created_on)
        self.assertEqual(items[0].product_id, found[0].product_id)
        self.assertEqual(items[0].wishlist_id, found[0].wishlist_id)
        self.assertEqual(items[0].quantity, found[0].quantity)
        self.assertEqual(items[0].price, found[0].price)
        self.assertEqual(items[0].rank, found[0].rank)
        self.assertEqual(items[0].updated_on, found[0].updated_on)

    def test_find_or_404_found(self):
        """It should Find or return 404 not found"""
        wishlist = WishlistsFactory()
        wishlist.id = None
        wishlist.create()
        items = ItemsFactory.create_batch(3)
        for item in items:
            item.wishlist_id = wishlist.id
            item.create()

        item = Items.find_or_404(items[1].id)
        self.assertIsNot(item, None)
        self.assertEqual(item.id, items[1].id)
        self.assertEqual(item.name, items[1].name)
        self.assertEqual(items[1].product_id, item.product_id)
        self.assertEqual(items[1].wishlist_id, item.wishlist_id)
        self.assertEqual(items[1].quantity, item.quantity)
        self.assertEqual(items[1].price, item.price)
        self.assertEqual(items[1].rank, item.rank)
        self.assertEqual(item.created_on, items[1].created_on)
        self.assertEqual(item.updated_on, items[1].updated_on)

    def test_find_or_404_not_found(self):
        """It should return 404 not found"""
        self.assertRaises(NotFound, Items.find_or_404, 0)
