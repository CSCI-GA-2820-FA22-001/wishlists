"""
Models for YourResourceModel

All of the models are stored in this module
"""
import logging
from flask_sqlalchemy import SQLAlchemy
import datetime

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """ Used for an data validation errors when deserializing """
    pass


class Wishlists(db.Model):
    """
    Class that represents Wishlists
    """

    app = None

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.datetime.now())
    items = db.relationship('Items', backref='wishlists', lazy=True)

    def __repr__(self):
        return "<Wishlist %r id=[%s]>" % (self.name, self.id)

    def create(self):
        """
        Creates a wishlist to the database
        """
        logger.info("Creating %s", self.name)
        self.id = None  # id must be none to generate next primary key
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a wishlist to the database
        """
        logger.info("Saving %s", self.name)
        db.session.commit()

    def delete(self):
        """ Removes a wishlist from the data store """
        logger.info("Deleting %s", self.name)
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        """ Serializes a wishlist into a dictionary """
        return {"id": self.id,
                "name": self.name,
                "created_by": self.customer_id,
                "created_on": self.created_on}

    def deserialize(self, data):
        """
        Deserializes a wishlist model from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.name = data["name"]
            if isinstance(data["customer_id"], int):
                self.customer_id = data["customer_id"]
            else:
                raise DataValidationError(
                    "Invalid type for integer [customer_id]: "
                    + str(type(data["available"]))
                )
        except KeyError as error:
            raise DataValidationError("Invalid Wishlist : missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError(
                "Invalid YourResourceModel: body of request contained bad or no data - "
                "Error message: " + error
            )
        return self

    @classmethod
    def init_db(cls, app):
        """ Initializes the database session """
        logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls):
        """ Returns all of the wishlist in the database """
        logger.info("Processing all YourResourceModels")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """ Finds a wishlist by it's ID """
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.get(by_id)

    @classmethod
    def find_by_name(cls, name):
        """Returns all wishlists with the given name

        Args:
            name (string): the name of the YourResourceModels you want to match
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_customer_id(cls, customer_id):
        """Returns all wishlists with the given name

        Args:
            name (string): the name of the YourResourceModels you want to match
        """
        logger.info("Processing customer id query for %s ...", str(customer_id))
        return cls.query.filter(cls.customer_id == customer_id)


class Items(db.Model):
    """
    Class that represents Wishlists
    """

    app = None

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)
    wishlist_id = db.Column(db.Integer, db.ForeignKey('wishlists.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer, nullable=False, default=0)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Integer, nullable=False, default=0)
    created_on = db.Column(db.DateTime, default=datetime.datetime.now())
    updated_on = db.Column(db.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "<Wishlist %r id=[%s]>" % (self.name, self.id)

    def create(self):
        """
        Adds a wishlist items to the database
        """
        logger.info("Creating %s", self.name)
        self.id = None  # id must be none to generate next primary key
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a wishlist item to the database
        """
        logger.info("Saving %s", self.name)
        db.session.commit()

    def delete(self):
        """ Removes a wishlist item from the data store """
        logger.info("Deleting %s", self.name)
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        """ Serializes a wishlist item into a dictionary """
        return {"id": self.id,
                "name": self.name,
                "wishlist_id": self.wishlist_id,
                "product_id": self.product_id,
                "created_on": self.created_on,
                "rank": self.rank,
                "price": self.price,
                "quantity": self.quantity,
                "updated_on": self.updated_on}

    def deserialize(self, data):
        """
        Deserializes a YourResourceModel from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.name = data["name"]
            if isinstance(data["product_id"], int):
                self.product_id = data["product_id"]
            else:
                raise DataValidationError(
                    "Invalid type for integer [product_id]: "
                    + str(type(data["product_id"]))
                )

            if isinstance(data["wishlist_id"], int):
                self.wishlist_id = data["wishlist_id"]
            else:
                raise DataValidationError(
                    "Invalid type for integer [wishlist_id]: "
                    + str(type(data["wishlist_id"]))
                )

            if data.get("rank", None):
                if isinstance(data["rank"], int):
                    self.rank = data["rank"]
                else:
                    raise DataValidationError(
                        "Invalid type for integer [rank]: "
                        + str(type(data["rank"]))
                    )

            if data.get("price", None):
                if isinstance(data["price"], int):
                    self.rank = data["price"]
                else:
                    raise DataValidationError(
                        "Invalid type for integer [price]: "
                        + str(type(data["price"]))
                    )

            if data.get("quantity", None):
                if isinstance(data["quantity"], int):
                    self.quantity = data["quantity"]
                else:
                    raise DataValidationError(
                        "Invalid type for integer [quantity]: "
                        + str(type(data["quantity"]))
                    )

        except KeyError as error:
            raise DataValidationError("Invalid Item : missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError(
                "Invalid YourResourceModel: body of request contained bad or no data - "
                "Error message: " + error
            )
        return self

    @classmethod
    def init_db(cls, app):
        """ Initializes the database session """
        logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls):
        """ Returns all of the wishlist items in the database """
        logger.info("Processing all YourResourceModels")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """ Finds a wishlist item by it's ID """
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.get(by_id)

    @classmethod
    def find_by_name(cls, name):
        """Returns all wishlists items with the given name

        Args:
            name (string): the name of the YourResourceModels you want to match
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_wishlist_id(cls, wishlist_id):
        """Returns all wishlists items with the given name

        Args:
            name (string): the name of the YourResourceModels you want to match
        """
        logger.info("Processing wishlist id query for %s ...", str(wishlist_id))
        return cls.query.filter(cls.wishlist_id == wishlist_id)
