"""
My Service
Describe what your service does here
"""


# from email.mime import application
from flask import jsonify, request, url_for, abort
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
# CREATE A NEW WISHLIST
######################################################################
@app.route("/wishlists", methods=["POST"])
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
def rename_wishlist(wishlist_id):
    """Renames a wishlist to a name specified by the "name" field in the body
    of the request.

    Args:
        wishlist_id: The id of the wishlist to rename.
    """
    app.logger.info("Request to rename wishlist %d", wishlist_id)
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
            f"No name was specified to rename {wishlist_id}",
        )

    wishlist.name = new_name
    wishlist.update()
    return wishlist.serialize(), status.HTTP_200_OK


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
        return {"message": "No items found for this wishlist - " + str(wishlist_id)}, status.HTTP_200_OK

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

   
    if (request.args):
        args = request.args
        customer_id = args.get("customer_id", type=int)
        app.logger.info("Request for wishlists with customer_id: %s", str(customer_id))
        wishlists = Wishlists.find_by_customer_id(customer_id)
        wishlists_serialized = [w.serialize() for w in wishlists]
        app.logger.info(wishlists_serialized)
        if len(wishlists_serialized) == 0:
            return {"message": "No wishlists found for the customer id - " + str(customer_id)}, status.HTTP_200_OK
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
        return {"message": "No wishlists found for this customer - " + str(customer_id)}, status.HTTP_200_OK
    # app.logger.info("Returning wishlist:", wishlists)
    return jsonify({"wishlists": wishlists_serialized}), status.HTTP_200_OK
    # return  jsonify("wishlists found for this customer - "+ customer_id), status.HTTP_200_OK


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
def update_product(wishlist_id, item_id):
    """Updates the name of a product in a wishlist."""
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
        abort(status.HTTP_400_BAD_REQUEST, "No product name passed to rename.")

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
