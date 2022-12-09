"""
My Service
Describe what your service does here
"""


# from email.mime import application
from flask_restx import Api, Resource, fields, reqparse, inputs
from flask import jsonify, request, url_for, abort
from service.models import Wishlists, Items, DataValidationError
from .common import status  # HTTP Status Codes

# Import Flask application
from . import app

######################################################################
# CONFIGURE SWAGGER
######################################################################


@app.errorhandler(status.HTTP_400_BAD_REQUEST)
def bad_request_error(error):
    """Creates a generic bad request error."""
    app.logger.warning("Bad Request: %s", error)
    return (
        jsonify(
            status=status.HTTP_400_BAD_REQUEST,
            error="BadRequestError",
            message=str(error),
        ),
        status.HTTP_400_BAD_REQUEST,
    )


@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """Creates a request validation error."""
    app.logger.warning("ValidationError: %s", error)
    return (
        jsonify(
            status=status.HTTP_400_BAD_REQUEST,
            error="ValidationError",
            message=str(error),
        ),
        status.HTTP_400_BAD_REQUEST,
    )


API = Api(
    app,
    version="1.0.0",
    title="Wishlists service",
    description="Wishlist server for an e-commerce site",
    default="Wishlists",
    default_label="Wishlist-Operations",
    doc="/apidocs/index.html",
    prefix="/api",
)


WISHLIST_MODEL = API.model(
    "Wishlist",
    {
        "id": fields.Integer(
            readOnly=True,
            required=True,
            example=1,
            description="The unique ID given to a wishlist.",
        ),
        "name": fields.String(
            required=True,
            example="EXAMPLE_WISHLIST",
            description="The name of the wishlist.",
        ),
        "customer_id": fields.String(
            required=True,
            min=1,
            example=1,
            description="The Unique ID of the customer who made the wishlist.",
        ),
    },
)
CREATE_WISHLIST_MODEL = API.model(
    "Wishlist",
    {
        "name": fields.String(
            required=True,
            example="EXAMPLE_WISHLIST",
            description="The name of the wishlist.",
        ),
        "customer_id": fields.String(
            required=True,
            min=1,
            example=1,
            description="The Unique ID of the customer who made the wishlist.",
        ),
    },
)

######################################################################
# Query Parsers
######################################################################

WISHLIST_QUERY_PARSER = reqparse.RequestParser()
WISHLIST_QUERY_PARSER.add_argument(
    "id", type=int, required=False, help="The ID of the wishlist"
)
WISHLIST_QUERY_PARSER.add_argument(
    "name", type=str, required=False, help="The Name of the wishlist."
)
WISHLIST_QUERY_PARSER.add_argument(
    "customer_id", type=int, required=False, help="The customer ID of the wishlist."
)

######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/healthcheck")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="Healthy"), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    app.logger.info("Request for Root URL")
    return (
        jsonify(
            name="Wishlists Demo REST API Service",
            version="1.0",
        ),
        status.HTTP_200_OK,
    )


######################################################################
# Wishlist handling
######################################################################


@API.route("/wishlists/<wishlist_id>", strict_slashes=False)
@API.param("wishlist_id", "The wishlist ID")
class WishlistResource(Resource):
    """Handles all routes for the wishlist model."""

    @API.doc("get_wishlist")
    @API.response(404, "No wishlist for the query found.")
    @API.marshal_list_with(WISHLIST_MODEL)
    def get(self, wishlist_id):
        """
        Retrieve a single wishlist
        This endpoint will return a wishlist based on it's id
        """

        app.logger.info("Request to get wishlist with id %d", wishlist_id)

        wishlist = Wishlists.find(wishlist_id)

        if not wishlist:
            API.abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist with arguments '{wishlist_id}' was not found.",
            )

        app.logger.info("Returning wishlist: %s", wishlist.name)
        return wishlist.serialize(), status.HTTP_200_OK

    @API.doc("update_wishlist")
    @API.response(404, "Wishlist not found")
    @API.response(400, "The posted wishlist is not valid")
    @API.expect(WISHLIST_MODEL)
    @API.marshal_with(WISHLIST_MODEL)
    def put(self, wishlist_id):
        """Updates a wishlist."""
        app.logger.info("Request to update wishlist %d", wishlist_id)
        wishlist = Wishlists.find(wishlist_id)

        if not wishlist:
            API.abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist with id '{wishlist_id}' was not found.",
            )
        body = request.get_json()
        app.logger.info("Got body=%s", body)
        for k, new_value in body.items():
            setattr(wishlist, k, new_value)
        wishlist.update()

        return wishlist.serialize(), status.HTTP_200_OK

    @API.doc("delete_wishlist")
    @API.response(204, "Wishlist Deleted")
    def delete(self, wishlist_id):
        """Deletes a wishlist."""
        app.logger.info("Request to delete wishlist with id: %s", wishlist_id)
        wishlist = Wishlists.find(wishlist_id)
        if wishlist:
            wishlist.delete()

        app.logger.info("Wishlist with ID [%s] delete complete.", wishlist_id)
        return "", status.HTTP_204_NO_CONTENT


@API.route("/wishlists", strict_slashes=False)
class WishlistCollection(Resource):
    """Resource for handling multiple wishlists."""

    @API.doc("create_wishlist")
    @API.expect(CREATE_WISHLIST_MODEL)
    @API.response(400, "ValueErrors: Missing either a name or a valid customer id.")
    @API.marshal_with(WISHLIST_MODEL)
    def post(self):
        """
        Creates a Wishlist
        This endpoint will create a Wishlist based the data in the body that is posted
        """
        app.logger.info("Request to create a wishlist")
        check_content_type("application/json")
        payload = request.get_json()
        if "name" not in payload or "customer_id" not in payload:
            API.abort(status.HTTP_400_BAD_REQUEST, "Missing data to create wishlist.")
        wishlist = Wishlists(
            name=payload.get("name", ""), customer_id=payload.get("customer_id", 0)
        )
        wishlist.create()

        location_url = f"{request.base_url}/wishlists/{wishlist.id}"
        app.logger.info("Wishlist with ID [%s] created.", wishlist.id)
        return wishlist.serialize(), status.HTTP_201_CREATED, {"location": location_url}

    @API.doc("list_wishlists")
    @API.marshal_list_with(WISHLIST_MODEL)
    @API.expect(WISHLIST_QUERY_PARSER,validate=True)
    def get(self):
        """Lists the wishlists."""
        app.logger.info("Request to list wishlist...")
        
        wishlist_id = request.args.get('id')
        customer_id = request.args.get('customer_id')
        name = request.args.get('name')
        wishlists = []
        if customer_id:
            wishlists = Wishlists.find_by_customer_id(customer_id)
        elif name:
            wishlists = Wishlists.find_by_name(name)
        elif wishlist_id:
            wishlists = [Wishlists.find(wishlist_id)]
        else:
            wishlists = Wishlists.all()
        wishlists = [w.serialize() for w in wishlists]
        app.logger.info("Found %d wishlists", len(wishlists))
        return wishlists, status.HTTP_200_OK


######################################################################
# CREATE A NEW ITEM TO WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items", methods=["POST"])
def create_item(wishlist_id):
    """
    Adds Item to wishlist
    This endpoint will add an item to wishlist based the data in the body that is posted
    """
    app.logger.info("Request to create a new item in a wishlist")
    check_content_type("application/json")
    item = Items()
    data = request.get_json()
    data["wishlist_id"] = wishlist_id
    item.deserialize(data)
    item.create()
    message = item.serialize()
    location_url = url_for(
        "get_items", wishlist_id=wishlist_id, item_id=item.id, _external=True
    )

    app.logger.info("Wishlist Item with ID [%s] created.", item.id)
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# RETRIEVE A WISHLIST ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["GET"])
def get_items(wishlist_id, item_id):
    """
    Retrieve a single wishlist
    This endpoint will return a wishlist based on it's id
    """
    app.logger.info("Request for items with id: %s", str(item_id))
    item = Items.find(item_id)
    if not item:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist Item with id '{item_id}' was not found.",
        )

    app.logger.info("Returning wishlist item: %s", item.name)
    return jsonify(item.serialize()), status.HTTP_200_OK


######################################################################
# LIST ALL ITEMS IN A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items", methods=["GET"])
def list_items(wishlist_id):
    """
    Retrieve a single wishlist item
    This endpoint will return a wishlist based on it's id
    """
    app.logger.info("Request for items in wishlist: %s", str(wishlist_id))
    items = Items.find_by_wishlist_id(wishlist_id)
    items_serialized = [i.serialize() for i in items]
    app.logger.info(items_serialized)
    if len(items_serialized) == 0:
        return {
            "message": "No items found for this wishlist - " + str(wishlist_id)
        }, status.HTTP_200_OK

    app.logger.info("Returning wishlist items for wishlist: %s", wishlist_id)
    return jsonify({"items": items_serialized}), status.HTTP_200_OK

######################################################################
# DELETE A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["DELETE"])
def delete_wishlists(wishlist_id):
    """
    Delete a wishlist
    This endpoint will delete a wishlist based the id specified in the path
    """
    app.logger.info("Request to delete wishlist with id: %s", wishlist_id)
    wishlist = Wishlists.find(wishlist_id)
    if wishlist:
        wishlist.delete()

    app.logger.info("Wishlist with ID [%s] delete complete.", wishlist_id)
    return "", status.HTTP_204_NO_CONTENT


@app.route("/wishlists/<int:wishlist_id>/items", methods=["DELETE"])
def clear_wishlist(wishlist_id):
    """Clears a wishlist of all items

    Args:
        wishlist_id: The wishlist to clear.
    """
    app.logger.info("Request to clear wishlist with id: %s", wishlist_id)
    wishlist = Wishlists.find(wishlist_id)

    if wishlist:
        while wishlist.items:
            item = wishlist.items[0]
            wishlist.items.remove(item)
            item.delete()

    app.logger.info("Wishlist with ID [%s] delete complete.", wishlist_id)
    return "", status.HTTP_204_NO_CONTENT


######################################################################
# DELETE A WISHLIST
######################################################################

# /wishlists/{id}/items/{id}
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["DELETE"])
def delete_items(wishlist_id, item_id):
    """
    Delete a item
    This endpoint will delete a item based the id specified in the path
    """
    app.logger.info("Request to delete item with id: %s", item_id)
    item = Items.find(item_id)
    if item:
        item.delete()

    app.logger.info("Item with ID [%s] delete complete.", item_id)
    return "", status.HTTP_204_NO_CONTENT


######################################################################
# UPDATE A PRODUCT IN A WISHLIST ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["PUT"])
def update_item(wishlist_id, item_id):
    """Updates the name of an item in a wishlist."""
    app.logger.info("Request to update product %d in wishlist %d", wishlist_id, item_id)
    wishlist = Wishlists.find(wishlist_id)

    if not wishlist:
        abort(status.HTTP_404_NOT_FOUND, f"Wishlist {wishlist_id} not found")

    wishlist_product = Items.find(item_id)

    if not wishlist_product:
        abort(status.HTTP_404_NOT_FOUND, f"Item {item_id} not found in {wishlist_id}")

    body = request.get_json()
    app.logger.info("Request body=%s", body)

    new_name = body.get("product_name", None)
    if not new_name:
        abort(status.HTTP_400_BAD_REQUEST, "No product name passed to update.")

    wishlist_product.name = new_name
    wishlist_product.update()

    return {}, status.HTTP_202_ACCEPTED


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


@app.before_first_request
def init_db():
    """Initializes the SQLAlchemy app"""
    global app
    Wishlists.init_db(app)
    Items.init_db(app)


def disconnect_db():
    Wishlists.disconnect_db()
    Items.disconnect_db()
