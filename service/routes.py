"""
My Service
Describe what your service does here
"""


# from email.mime import application
from flask import jsonify, request, url_for, abort
from flask_restx import Api, Resource, fields, reqparse, inputs
from service.models import Wishlists, Items
from .common import status  # HTTP Status Codes

# Import Flask application
from . import app


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
            paths=url_for("create_wishlists", _external=True),
        ),
        status.HTTP_200_OK,
    )

######################################################################
# CONFIGURING MODELS
######################################################################

WISHLISTS_MODEL = api.model(
    "WISHLISTS",
    {
        "id": fields.Integer(
            required=True,
            example=1,
            description="The unique ID given to a Wishlist."
        ),
        "name": fields.String(
            required=True,
            example="EXAMPLE_WISHLIST",
            description="The name of the wishlist.",
        ),
        "customer_id": fields.Integer(
            required=True,
            example=1,
            description="The Unique ID of the customer who has created the wishlist."
        )
    }
)

Create_Wishlist_Item_Model = api.model('Create Wishlist Items', {
    'id': fields.Integer(required=True,
                                 description='ID number of the item.'),
    'name': fields.String(required=True,
                                  description='Name of the item.')
})

Wishlist_Item_Model = api.model('Wishlist Product', {
    'wishlist_id': fields.Integer(readOnly=True,
                                  description='Wishlist unique ID'),
    'id': fields.Integer(required=True,
                                 description='ID of the item.'),
    'name': fields.String(required=True,
                                  description='Name of the item.')
})


ITEMS_MODEL = api.model(
    "Items",
    {
        "id": fields.Integer(
            required=True,
            example=1,
            description="The unique ID given to an Item."
        ),
        "name": fields.String(
            required=True,
            example="EXAMPLE_ITEM",
            description="The name of the item."
        ),
        "wishlist_id": fields.Integer(
            required=True,
            example=1,
            description="The Unique ID of the wishlist in which item is added."
        ),
        "product_id": fields.Integer(
            required=True,
            example=1,
            description="The Unique ID of the product."
        ),
        "rank": fields.Integer(
            required=True,
            example=1,
            description="Order in the wishlist."
        ),
        "quantity": fields.Integer(
            required=True,
            example=1,
            description="Quantity of the item."
        ),
        "price": fields.Integer(
            required=True,
            example='$20',
            description="Price of the item."
        )
    }
)

# query string arguments
wishlist_args = reqparse.RequestParser()
wishlist_args.add_argument('name', type=str, location='args', required=False, help='List wishlist by name')
wishlist_args.add_argument('customer_id', type=str, location='args', required=False, help='List wishlists by customer id')

item_args = reqparse.RequestParser()
item_args.add_argument('name', type=str, required=False,
                                help='List name of the item in the wishlist.')
item_args.add_argument('product_id', type=int, required=False,
                                help='List Wishlists Items by Product id')


######################################################################
# Authorization Decorator
######################################################################

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'X-Api-Key' in request.headers:
            token = request.headers['X-Api-Key']

        if app.config.get('API_KEY') and app.config['API_KEY'] == token:
            return f(*args, **kwargs)
        else:
            return {'message': 'Invalid or missing token'}, 401
    return decorated

######################################################################
# CREATE A NEW WISHLIST
######################################################################
@app.route("/wishlists", methods=["POST"])
@api.doc('Create Wishlist')
@api.expect(WISHLISTS_MODEL)
@api.response(400, 'Errors: "Missing name" or \
                  "Wrong customer_id. Number should be greater than 0."')
@api.marshal_with(WISHLISTS_MODEL, code=201)
def create_wishlists():
    """
    Creates a Wishlist
    This endpoint will create a Wishlist based the data in the body that is posted
    """
    app.logger.info("Request to create a wishlist")
    check_content_type("application/json")
    wishlist = Wishlists()
    wishlist.deserialize(request.get_json())
    wishlist.create()
    message = wishlist.serialize()
    location_url = url_for("get_wishlists", wishlist_id=wishlist.id, _external=True)
    app.logger.info("Wishlist with ID [%s] created.", wishlist.id)
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


@app.route("/wishlists/<int:wishlist_id>", methods=["GET"])
@api.doc('list_wishlist')
@api.expect(wishlist_args)
@api.response(404, 'No wishlist does not exist.')
@api.marshal_list_with(WISHLISTS_MODEL)
def get_wishlists(wishlist_id):
    """
    Retrieve a single wishlist
    This endpoint will return a wishlist based on it's id
    """
    app.logger.info("Request for wishlist with id: %s", wishlist_id)
    wishlist = Wishlists.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    app.logger.info("Returning wishlist: %s", wishlist.name)
    return jsonify(wishlist.serialize()), status.HTTP_200_OK


@app.route("/wishlists/<int:wishlist_id>", methods=["PUT"])
def update_wishlist(wishlist_id):
    """Renames a wishlist to a name specified by the "name" field in the body
    of the request.

    Args:
        wishlist_id: The id of the wishlist to update.
    """
    app.logger.info("Request to update wishlist %d", wishlist_id)
    wishlist = Wishlists.find(wishlist_id)

    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    body = request.get_json()
    app.logger.info("Got body=%s", body)

    new_name = body.get("name", None)
    if new_name is None:
        abort(
            status.HTTP_400_BAD_REQUEST,
            f"No name was specified to update {wishlist_id}",
        )

    wishlist.name = new_name
    wishlist.update()
    return wishlist.serialize(), status.HTTP_200_OK


######################################################################
# CREATE A NEW ITEM TO WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items", methods=["POST"])
@api.doc('Create a New Item in Wishlist')
@api.expect(Create_Wishlist_Item_Model)
@api.response(404, 'Wishlist with id \'wishlist_id\' does not exist.')
@api.marshal_list_with(Wishlist_Item_Model)
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
@api.expect(item_args)
@api.response(404, 'Item not found in the list.')
@api.marshal_list_with(Wishlist_Item_Model)
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
@api.response(404, 'Wishlist does not exist.')
@api.marshal_list_with(ITEMS_MODEL)
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
# LIST ALL THE WISHLISTS / FOR A CUSTOMER
######################################################################
@app.route("/wishlists", methods=["GET"])
def list_all_wishlists():
    """
    Retrieve all wishlists
    This endpoint will return all wishlists
    """

    if request.args:
        args = request.args
        customer_id = args.get("customer_id", type=int)
        app.logger.info("Request for wishlists with customer_id: %s", str(customer_id))
        wishlists = Wishlists.find_by_customer_id(customer_id)
        wishlists_serialized = [w.serialize() for w in wishlists]
        app.logger.info(wishlists_serialized)
        if len(wishlists_serialized) == 0:
            return {
                "message": "No wishlists found for the customer id - "
                + str(customer_id)
            }, status.HTTP_200_OK
        # app.logger.info("Returning wishlist:", wishlists)
        return jsonify({"wishlists": wishlists_serialized}), status.HTTP_200_OK
    else:
        app.logger.info("Request for all wishlists")
        wishlists = Wishlists.all()

        wishlists_serialized = [w.serialize() for w in wishlists]
        app.logger.info(wishlists_serialized)
        if len(wishlists_serialized) == 0:
            return {"message": "No wishlists found"}, status.HTTP_200_OK
        return jsonify({"wishlists": wishlists_serialized}), status.HTTP_200_OK


######################################################################
# LIST ALL WISHLISTS FOR A CUSTOMER
######################################################################
@app.route("/wishlists/customer/<int:customer_id>", methods=["GET"])
@api.response(404, 'Customer does not exist.')
def list_wishlists(customer_id):
    """
    Retrieve a single wishlist
    This endpoint will return a wishlist based on it's id
    """
    app.logger.info("Request for wishlists with customer_id: %s", str(customer_id))
    wishlists = Wishlists.find_by_customer_id(customer_id)

    wishlists_serialized = [w.serialize() for w in wishlists]
    app.logger.info(wishlists_serialized)
    if len(wishlists_serialized) == 0:
        return {
            "message": "No wishlists found for this customer - " + str(customer_id)
        }, status.HTTP_200_OK
    # app.logger.info("Returning wishlist:", wishlists)
    return jsonify({"wishlists": wishlists_serialized}), status.HTTP_200_OK
    # return  jsonify("wishlists found for this customer - "+ customer_id), status.HTTP_200_OK


######################################################################
# DELETE A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["DELETE"])
@api.response(204, 'Wishlist Removed')
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
# DELETE A ITEM FROM WISHLIST
######################################################################

# /wishlists/{id}/items/{id}
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["DELETE"])
@api.response(204, 'Item removed from wishlist.')
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
@api.doc('Update an Item')
@api.response(404, 'Wishlist or Item does not exist')
@api.expect(Wishlist_Item_Model)
@api.marshal_with(Wishlist_Item_Model)
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


def init_db():
    """Initializes the SQLAlchemy app"""
    global app
    Wishlists.init_db(app)
    Items.init_db(app)
