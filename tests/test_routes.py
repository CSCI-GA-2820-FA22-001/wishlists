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

import os
import logging
from unittest import TestCase

# from unittest.mock import MagicMock, patch
from service import app
from service.routes import init_db, disconnect_db
from service.common import status
from service.models import db, Wishlists, Items
from tests.factories import WishlistsFactory, ItemsFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/api/wishlists"

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
        # app.logger.setLevel(logging.DEBUG)
        init_db()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        disconnect_db()
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.remove()
        db.drop_all()
        db.create_all()
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
        self.assertIn(b"Wishlists Demo REST API Service", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/healthcheck")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["status"], 200)
        self.assertEqual(data["message"], "Healthy")

    def test_create_wishlist(self):
        """It should Create a new wishlist"""

        create_args = {"name": "Test Wishlist", "customer_id": 1}
        resp = self.client.post(BASE_URL, json=create_args)

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        result = resp.get_json()
        self.assertEqual(int(result["id"]), 1)
        self.assertEqual(result["name"], create_args["name"])
        self.assertEqual(int(result["customer_id"]), create_args["customer_id"])

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

        "It should display all the wishlists when present."

        test_wishlists = self._create_wishlists(5)
        ids = [w["id"] for w in test_wishlists]

        response = self.client.get(f"{BASE_URL}")
        resp_wishlists = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_wishlists), len(test_wishlists))
        for r in resp_wishlists:
            self.assertIn(r["id"], ids)

    def test_list_wishlist(self):
        "It should display the wishlists for a particular customer"
        customer_id = 5678
        test_wishlists = self._create_wishlists_by_customer(5, customer_id)

        ids = [w["id"] for w in test_wishlists]
        response = self.client.get(
            f"{BASE_URL}?customer_id={test_wishlists[0]['customer_id']}"
        )

        resp_wishlists = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_wishlists), len(test_wishlists))
        for r in resp_wishlists:
            self.assertEqual(int(r["customer_id"]), customer_id)
            self.assertIn(int(r["id"]), ids)

    def test_list_wishlist_id(self):
        "It should display the wishlists for a particular wishlist id"
        test_wishlist = self._create_wishlists(1)[0]
        wishlist_id = test_wishlist['id']
        response = self.client.get(
            f"{BASE_URL}?id={wishlist_id}"
        )

        resp_wishlists = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_wishlists[0]["id"], wishlist_id)

    def test_get_wishlist(self):
        """It should get a wishlist by id."""
        test_wishlist = self._create_wishlists(2)[0]
        resp = self.client.get(f'{BASE_URL}/{test_wishlist["id"]}')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        result = resp.get_json()
        self.assertEqual(result["id"], test_wishlist["id"])
        self.assertEqual(result["name"], test_wishlist["name"])
        self.assertEqual(result["customer_id"], test_wishlist["customer_id"])

    def test_get_wishlist_name(self):
        """It should get a wishlist by name."""
        test_wishlist = self._create_wishlists(2)[0]
        resp = self.client.get(f'{BASE_URL}?name={test_wishlist["name"]}')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        result = resp.get_json()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], test_wishlist["id"])
        self.assertEqual(result[0]["name"], test_wishlist["name"])
        self.assertEqual(result[0]["customer_id"], test_wishlist["customer_id"])

    def test_get_wishlist_not_found(self):
        """It should not retrieve a wishlist"""
        test_wishlist = WishlistsFactory()
        url = BASE_URL + "/0"
        response = self.client.get(url, json=test_wishlist.serialize())

        # Checking Status
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Checking the name and id of the Wishlist
        new_wishlist = response.get_json()
        self.assertIn("was not found.", new_wishlist["message"])


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
            print(response)
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
        self.assertIn(b"Wishlists Demo REST API Service", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/healthcheck")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["status"], 200)
        self.assertEqual(data["message"], "Healthy")

    def test_add_item_to_wishlist(self):
        """It should Create a new ITEM"""
        test_wishlist = WishlistsFactory()
        test_wishlist.id = None
        test_wishlist.create()

        new_item = {"name": "test item", "product_id": 1}
        response = self.client.post(
            f"{BASE_URL}/{test_wishlist.id}/items", json=new_item
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        n_item = response.get_json()
        self.assertEqual(int(n_item["wishlist_id"]), test_wishlist.id)
        self.assertEqual(n_item["name"], new_item["name"])
        self.assertEqual(n_item["product_id"], new_item["product_id"])

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

    def test_delete_wishlist_items(self):
        """It should Delete a Wishlist"""
        test_wishlist, _ = self._create_wishlist_with_items(3)
        self.assertEqual(len(test_wishlist.items), 3)
        response = self.client.delete(f"{BASE_URL}/{test_wishlist.id}")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_wishlist.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_clear_wishlist_items(self):
        """It should Delete a Wishlist"""
        test_wishlist, _ = self._create_wishlist_with_items(3)
        self.assertEqual(len(test_wishlist.items), 3)
        response = self.client.put(f"{BASE_URL}/{test_wishlist.id}/clear")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(test_wishlist.items, [])
        response = self.client.get(f"{BASE_URL}/{test_wishlist.id}")
        self.assertFalse("items" in response.get_json())

    def test_clear_wishlist_items_404(self):
        """It should Delete a Wishlist"""
        response = self.client.put(f"{BASE_URL}/0/clear")

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

    def test_update_product_no_wid(self):
        """It should Update a product Name"""
        wishlist = Wishlists(name="Wishlist", customer_id=1)
        wishlist.create()
        item = Items(name="Test", wishlist_id=wishlist.id, product_id=1)
        item.create()

        response = self.client.put(
            f"{BASE_URL}/0/items/{item.id}",
            json={"product_name": "Test Rename"},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product_no_iid(self):
        """It should Update a product Name"""
        wishlist = Wishlists(name="Wishlist", customer_id=1)
        wishlist.create()
        item = Items(name="Test", wishlist_id=wishlist.id, product_id=1)
        item.create()

        response = self.client.put(
            f"{BASE_URL}/{wishlist.id}/items/0",
            json={"product_name": "Test Rename"},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product_no_pname(self):
        """It should Update a product Name"""
        wishlist = Wishlists(name="Wishlist", customer_id=1)
        wishlist.create()
        item = Items(name="Test", wishlist_id=wishlist.id, product_id=1)
        item.create()

        response = self.client.put(
            f"{BASE_URL}/{wishlist.id}/items/{item.id}",
            json={},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_wishlist_item(self):
        """It should retrieve an item in a wishlist."""

        test_item = self._create_items(1)[0]
        url = BASE_URL + "/" + str(test_item["wishlist_id"]) + "/items"
        response = self.client.get(f'{url}/{test_item["id"]}')

        # Checking Status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Checking the attributed of the Wishlist Item
        n_item = response.get_json()
        self.assertDictEqual(n_item, test_item)

    def test_list_wishlist_items(self):
        """It should retrieve all items in a wishlist."""

        wishlist, items = self._create_wishlist_with_items(3)

        url = BASE_URL + "/" + str(wishlist.id) + "/items"
        response = self.client.get(f"{url}")

        # Checking Status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Checking the attributed of the Wishlist Item
        n_item = response.get_json()
        self.assertEqual(len(n_item), len(items["pid"]))
        for i, actual in enumerate(n_item):
            self.assertEqual(actual["name"], items["name"][i])
            self.assertEqual(actual["product_id"], items["pid"][i])

    def test_get_wishlist_item_not_found(self):
        """It should not retrieve a wishlist item"""
        url = BASE_URL + "/0/items/0"
        response = self.client.get(f"{url}")

        # Checking Status
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Checking the name and id of the Wishlist
        new_wishlist = response.get_json()
        self.assertIn("was not found.", new_wishlist["message"])

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


    ######################################################################
    #  T E S T   S A D   P A T H S
    ######################################################################

    def test_bad_request(self):
        """It should not allow bad request"""
        response = self.client.post(BASE_URL, json={"name": " "})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_http_request(self):
        """It should not allow unsupported HTTP methods"""
        response = self.client.patch(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_wishlist_no_content_type(self):
        """It should not Create a Wishlist with no content type"""
        response = self.client.post(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_wishlist_bad_content_type(self):
        """It should not Create a Wishlist with bad content type"""
        response = self.client.post(BASE_URL, headers={"Content-Type": "notJSON"})
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_update_wishlist_not_found(self):
        """It should not Update a Wishlist who doesn't exist"""
        response = self.client.put(f"{BASE_URL}/0", json={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_activate_wishlist_not_found(self):
        """It should not activate a Wishlist who doesn't exist"""
        response = self.client.put(f"{BASE_URL}/0/activate", json={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deactivate_wishlist_not_found(self):
        """It should not activate a Wishlist who doesn't exist"""
        response = self.client.put(f"{BASE_URL}/0/deactivate", json={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
