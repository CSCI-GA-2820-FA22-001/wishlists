# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
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
Wishlists API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestWishlistsService
"""

from cgi import test
import os
import logging
from unittest import TestCase

# from unittest.mock import MagicMock, patch
from urllib.parse import quote_plus
from service import app
from service.common import status
from service.models import db, Wishlists, Items
from tests.factories import WishlistsFactory, ItemsFactory
import datetime

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/wishlists"


######################################################################
#  T E S T   WISHLIST   S E R V I C E
######################################################################
class TestWishlistsService(TestCase):
    """Wishlist Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Wishlists.init_db(app)
        Items.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Items).delete()  # clean up the last tests
        db.session.query(Wishlists).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    def _create_wishlists(self, count):
        """Factory method to create wishlists in bulk"""
        wishlists = []
        for _ in range(count):
            test_wishlists = WishlistsFactory()
            response = self.client.post(BASE_URL, json=test_wishlists.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test wishlist",
            )
            new_wishlist = response.get_json()
            test_wishlists.id = new_wishlist["id"]
            wishlists.append(new_wishlist)
        return wishlists

    def _create_wishlists_by_customer(self, count, customer_id):
        """Factory method to create wishlists in bulk"""
        wishlists = []
        for _ in range(count):
            test_wishlists = WishlistsFactory()
            json_req = test_wishlists.serialize()
            json_req["customer_id"] = customer_id
            response = self.client.post(BASE_URL, json=json_req)
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test wishlist",
            )
            new_wishlist = response.get_json()
            test_wishlists.id = new_wishlist["id"]
            wishlists.append(new_wishlist)
        return wishlists

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should call the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], "Wishlists Demo REST API Service")

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/healthcheck")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["status"], 200)
        self.assertEqual(data["message"], "Healthy")

    def test_create_wishlist(self):
        """It should Create a new wishlist"""
        test_wishlist = WishlistsFactory()
        logging.debug("Test Wishlist: %s", test_wishlist.serialize())
        response = self.client.post(BASE_URL, json=test_wishlist.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_wishlist = response.get_json()
        self.assertEqual(new_wishlist["name"], test_wishlist.name)
        self.assertEqual(new_wishlist["customer_id"], test_wishlist.customer_id)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_wishlist = response.get_json()
        self.assertEqual(new_wishlist["name"], test_wishlist.name)
        self.assertEqual(new_wishlist["customer_id"], test_wishlist.customer_id)

    def test_create_wishlists_no_data(self):
        "should not create a wishlist"
        response = self.client.post(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_wishlists_no_content_type(self):
        "should not create a wishlist"
        response = self.client.post(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_wishlists_bad_content_type(self):
        "should not create a wishlist"
        response = self.client.post(
            BASE_URL, headers={"Content-Type": "application/octet-stream"}
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_delete_wishlist(self):
        """It should Delete a Wishlist"""
        test_wishlist = self._create_wishlists(1)[0]
        response = self.client.delete(f"{BASE_URL}/{test_wishlist['id']}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_wishlist['id']}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rename_wishlist(self):
        """It should rename the wishlist."""
        test_wishlist = self._create_wishlists(1)[0]
        response = self.client.put(
            f"{BASE_URL}/{test_wishlist['id']}", json={"name": "Test Rename"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        renamed_wishlist = response.get_json()
        self.assertEqual(renamed_wishlist["name"], "Test Rename")

        response = self.client.get(f"{BASE_URL}/{test_wishlist['id']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wishlist = response.get_json()
        self.assertEqual(wishlist["name"], "Test Rename")

    def test_list_all_wishlists(self):
        "It should display all the wishlists when present. When no wishlists found, it should display a message that no wishlists found"

        response = self.client.get(f"{BASE_URL}")
        self.assertEqual(response.get_json()["message"], "No wishlists found")

        test_wishlists = self._create_wishlists(5)
        ids = [w["id"] for w in test_wishlists]
        response = self.client.get(f"{BASE_URL}")

        resp_wishlists = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_wishlists['wishlists']),len(test_wishlists))
        for r in resp_wishlists['wishlists']:
            self.assertIn(r['id'], ids)
    
    def test_list_wishlist(self):
        "It should display the wishlists for a particular customer"
        customer_id = 5678
        test_wishlists = self._create_wishlists_by_customer(5,customer_id)
        
        ids = [w["id"] for w in test_wishlists]
        response = self.client.get(f"{BASE_URL}",query_string ="customer_id="+str(customer_id))
        
        resp_wishlists = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_wishlists['wishlists']),len(test_wishlists))
        for r in resp_wishlists['wishlists']:
            self.assertEqual(r['customer_id'], customer_id)
            self.assertIn(r['id'], ids)
        cid = 789
        response = self.client.get(f"{BASE_URL}",query_string ="customer_id="+str(cid))
        self.assertEqual(response.get_json()["message"],"No wishlists found for the customer id - "+str(cid))

######################################################################
#  T E S T   ITEMS   S E R V I C E
######################################################################
class TestItemsService(TestCase):
    """Items Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Items.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Items).delete()  # clean up the last tests
        db.session.query(Wishlists).delete()  # clean up the last wishlists
        db.session.commit()

    def tearDown(self):
        db.session.query(Items).delete()  # clean up the last tests
        db.session.query(Wishlists).delete()  # clean up the last wishlists
        db.session.remove()

    def _create_items(self, count):
        """Factory method to create items in bulk"""
        items = []
        for _ in range(count):
            test_wishlist = WishlistsFactory()
            test_wishlist.id = None
            test_wishlist.create()
            test_item = ItemsFactory()
            test_item.wishlist_id = test_wishlist.id
            url = BASE_URL + "/" + str(test_item.wishlist_id) + "/items"
            response = self.client.post(url, json=test_item.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test item",
            )
            new_item = response.get_json()
            test_item.id = new_item["id"]
            items.append(new_item)
        return items

    def _create_wishlists_by_customer(self, count, customer_id):
        """Factory method to create wishlists in bulk"""
        wishlists = []
        for _ in range(count):
            test_wishlists = WishlistsFactory()
            json_req = test_wishlists.serialize()
            json_req["customer_id"] = customer_id
            response = self.client.post(BASE_URL, json=json_req)
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test wishlist",
            )
            new_wishlist = response.get_json()
            test_wishlists.id = new_wishlist["id"]
            wishlists.append(new_wishlist)
        return wishlists

    def _create_wishlist_with_items(self, item_count):
        """Creates a wishlist with item_item count items."""
        test_wishlist = WishlistsFactory()
        test_wishlist.id = None
        test_wishlist.create()
        items_name, items_pid = [None] * item_count, [None] * item_count
        for i in range(item_count):
            test_item = ItemsFactory()
            test_item.wishlist_id = test_wishlist.id
            url = BASE_URL + "/" + str(test_wishlist.id) + "/items"
            response = self.client.post(url, json=test_item.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Make sure location header is set
            location = response.headers.get("Location", None)
            self.assertIsNotNone(location)

            # Check the data is correct
            new_item = response.get_json()
            self.assertEqual(new_item["name"], test_item.name)
            self.assertEqual(new_item["product_id"], test_item.product_id)
            items_name[i] = new_item["name"]
            items_pid[i] = new_item["product_id"]
        return test_wishlist, {"name": items_name, "pid": items_pid}

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should call the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], "Wishlists Demo REST API Service")

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/healthcheck")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["status"], 200)
        self.assertEqual(data["message"], "Healthy")

    def test_add_item_to_wishlist(self):
        """It should Create a new ITEM"""
        test_item = ItemsFactory()
        logging.debug("Test Item: %s", test_item.serialize())
        test_wishlist = WishlistsFactory()
        test_wishlist.id = None
        test_wishlist.create()
        test_item = ItemsFactory()
        test_item.wishlist_id = test_wishlist.id
        url = BASE_URL + "/" + str(test_wishlist.id) + "/items"
        response = self.client.post(url, json=test_item.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_item = response.get_json()
        self.assertEqual(new_item["name"], test_item.name)
        self.assertEqual(new_item["product_id"], test_item.product_id)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_item = response.get_json()
        self.assertEqual(new_item["name"], test_item.name)
        self.assertEqual(new_item["product_id"], test_item.product_id)

    def test_delete_item(self):
        """It should Delete a Item"""
        test_item = self._create_items(1)[0]
        url = BASE_URL + "/" + str(test_item["wishlist_id"]) + "/items"
        response = self.client.delete(f"{url}/{test_item['id']}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{url}/{test_item['id']}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        """It should Update a product Name"""
        wishlist = Wishlists(name="Wishlist", customer_id=1)
        wishlist.create()
        item = Items(name="Test", wishlist_id=wishlist.id, product_id=1)
        item.create()

        response = self.client.put(
            f"{BASE_URL}/{wishlist.id}/items/{item.id}",
            json={"product_name": "Test Rename"},
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_get_wishlist(self):
        """It should retrieve a wishlist"""
        test_wishlist = WishlistsFactory()
        test_wishlist.id = None
        test_wishlist.create()
        test_wishlist_id = test_wishlist.id
        url = BASE_URL + "/" + str(test_wishlist_id)
        response = self.client.get(url, json=test_wishlist.serialize())

        ##Checking Status##
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ##Checking the name and id of the Wishlist##
        new_wishlist = response.get_json()
        self.assertEqual(new_wishlist["id"], test_wishlist.id)
        self.assertEqual(new_wishlist["name"], test_wishlist.name)

    def test_get_wishlist_not_found(self):
        """It should not retrieve a wishlist"""
        test_wishlist = WishlistsFactory()
        url = BASE_URL + "/0"
        response = self.client.get(url, json=test_wishlist.serialize())

        ##Checking Status##
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        ##Checking the name and id of the Wishlist##
        new_wishlist = response.get_json()
        self.assertIn("was not found.", new_wishlist["message"])

    def test_get_wishlist_item(self):
        """It should retrieve items in a wishlist."""

        test_item = self._create_items(1)[0]
        url = BASE_URL + "/" + str(test_item["wishlist_id"]) + "/items"
        response = self.client.get(f'{url}/{test_item["id"]}', json=test_item)

        ##Checking Status##
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ##Checking the attributed of the Wishlist Item##
        n_item = response.get_json()
        self.assertDictEqual(n_item, test_item)

    def test_get_wishlist_item_not_found(self):
        """It should not retrieve a wishlist item"""
        url = BASE_URL + "/0/items/0"
        response = self.client.get(f"{url}")

        ##Checking Status##
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        ##Checking the name and id of the Wishlist##
        new_wishlist = response.get_json()
        self.assertIn("was not found.", new_wishlist["message"])

    def test_list_wishlist_items(self):
        """It should list wishlist items"""
        test_wishlist, item_info = self._create_wishlist_with_items(2)

        URL = BASE_URL + "/" + str(test_wishlist.id) + "/items"
        response = self.client.get(URL)

        ##Checking Status##
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ##Checking the attributed of the Wishlist Item##
        n_item = response.get_json()["items"]

        self.assertEqual(len(n_item), 2)
        for i in range(0, 1):
            self.assertEqual(item_info["name"][i], n_item[i]["name"])
            self.assertEqual(item_info["pid"][i], n_item[i]["product_id"])

    def test_unsupported_HTTP_request(self):
        """It should not allow unsupported HTTP methods"""
        response = self.client.patch(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_clear_wishlist(self):
        """It should clear a wishlist of its items."""
        test_wishlist, _ = self._create_wishlist_with_items(3)
        self.assertEqual(len(test_wishlist.items), 3)
        response = self.client.delete(f"{BASE_URL}/{test_wishlist.id}/items")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(test_wishlist.items, [])
        response = self.client.get(f"{BASE_URL}/{test_wishlist.id}")
        self.assertFalse("items" in response.get_json())
