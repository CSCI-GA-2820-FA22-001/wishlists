"""
My Service

Describe what your service does here
"""

from flask import Flask, jsonify, request, url_for, make_response, abort
from .common import status  # HTTP Status Codes
from service.models import Wishlists,Items
from flask import request, jsonify
import json

# Import Flask application
from . import app


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """ Root URL response """
    return (
        "Reminder",
        status.HTTP_200_OK,
    )

@app.route("/wishlists", methods=["POST"])
def create_wishlist():
    data = json.loads(request.data)
    try:
        name = data['name']
        customer_id = data['customer_id'] 
        wishlist = Wishlists(name=name,customer_id=customer_id)
        wishlist.create()
        return (wishlist.serialize(),
        status.HTTP_200_OK,
    )

    except KeyError as e:
        pass




######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def init_db():
    """ Initializes the SQLAlchemy app """
    global app
    Wishlists.init_db(app)
    Items.init_db(app)
