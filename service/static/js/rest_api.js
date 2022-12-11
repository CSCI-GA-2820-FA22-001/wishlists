$(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#wishlist_id").val(res.id);
        $("#wishlist_name").val(res.name);
        $("#customer_id").val(res.customer_id);
        $("#wishlist_created").val(res.created_on);
        $("#item_list").val(res.items);
    }

    // Updates the form with data from the Item response
    function update_form_data_item(res) {
        $("#wishlist_id").val(res.wishlist_id);
        $("#item_id").val(res.id);
        $("#item_name").val(res.name);
        $("#product_id").val(res.product_id);
        $("#item_quantity").val(res.quantity);
        $("#item_price").val(res.price);    
        $("#item_created").val(res.created_on);
    }

    /// Clears all form fields
    function clear_form_data() {
        $("#wishlist_name").val("");
        $("#wishlist_id").val("");
        $("#customer_id").val("");
        $("#item_list").val("");
        $("#wishlist_created").val("");
        $("#item_id").val("");
        $("#item_name").val("");
        $("#item_created").val("");
        $("#product_id").val("");
        $("#item_quantity").val("");
        $("#item_price").val("");
        $("#search_results").empty();
        $("#search_item_results").empty();
    }

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // ****************************************
    // Create a Wishlist
    // ****************************************

    $("#create-btn").click(function () {

        let id = $("#wishlist_id").val();
        let name = $("#wishlist_name").val();
        let customer_id = $("#customer_id").val();
        let created_on = new Date();

        let data = {
            "name": name,
            "customer_id": parseInt(customer_id),
            "created_on": created_on
        };

        $("#flash_message").empty();
        
        let ajax = $.ajax({
            type: "POST",
            url: "/wishlists",
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });
    });


    // ****************************************
    // Update a Wishlist
    // ****************************************

    $("#update-btn").click(function () {


        let wishlist_id = $("#wishlist_id").val();
        let name = $("#wishlist_name").val();
        // Update is only renaming a wishlist, since you cant change items between different customers
        // let customer_id = $("#customer_id").val();

        let data = {
            "name": name,
        };

        $("#flash_message").empty();

        let ajax = $.ajax({
                type: "PUT",
                url: `/wishlists/${wishlist_id}`,
                contentType: "application/json",
                data: JSON.stringify(data)
            })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Retrieve a Wishlist
    // ****************************************

    $("#retrieve-btn").click(function () {

        let wishlist_id = $("#wishlist_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/wishlists/${wishlist_id}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Delete a Wishlist
    // ****************************************

    $("#delete-btn").click(function () {

        let wishlist_id = $("#wishlist_id").val();

        $("#flash_message").empty();

        $.ajax({
            type: "DELETE",
            url: `/wishlists/${wishlist_id}/items`,
            contentType: "application/json",
            data: '',
        })

        let ajax = $.ajax({
            type: "DELETE",
            url: `/wishlists/${wishlist_id}`,
            contentType: "application/json",
            data: '',
        })

        ajax.done(function(res){
            clear_form_data()
            flash_message("Wishlist has been Deleted!")
        });

        ajax.fail(function(res){
            flash_message("Server error!")
        });
    });

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        $("#wishlist_id").val("");
        $("#item_id").val("");
        $("#flash_message").empty();
        clear_form_data()
    });


    // ****************************************
    // Search for a Wishlist
    // ****************************************

    $("#search-btn").click(function () {

        let id = $("#wishlist_id").val();
        // Customer ID will be empty, since wishlist_id is unique for any wishlist
        let customer_id = $("#customer_id").val();

        let queryString = ""
        
        if (id) {
           get_url = `/wishlists/${id}`
        }
        else if (customer_id){
            
            queryString += 'customer_id=' + customer_id
            get_url = `/wishlists?${queryString}`
        }
        else {
            get_url = `/wishlists`
        }
        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: get_url,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            $("#search_results").empty();
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-1">Wishlist ID</th>'
            table += '<th class="col-md-4">Name</th>'
            table += '<th class="col-md-4">Customer ID</th>'
            table += '<th class="col-md-3">Created On</th>'
            table += '</tr></thead><tbody>'
            let firstWList = "";
            if(id){
                let wishlist = res;
                table +=  `<tr id="row_0"><td>${wishlist.id}</td><td>${wishlist.name}</td><td>${wishlist.customer_id}</td><td>${wishlist.created_on}</td></tr>`;
                firstWList = wishlist
            }
            else{
                res = res.wishlists
                for(let i = 0; i < res.length; i++) {
                    let wishlist = res[i];
                    table +=  `<tr id="row_${i}"><td>${wishlist.id}</td><td>${wishlist.name}</td><td>${wishlist.customer_id}</td><td>${wishlist.created_on}</td></tr>`;
                    if (i == 0) {
                        firstWList = wishlist;
                    }
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // copy the first result to the form
            if (firstWList != "") {
                update_form_data(firstWList)
            }

            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Add Item to a Wishlist
    // ****************************************

    $("#create-item-btn").click(function () {

        let id = $("#item_id").val();
        let wishlist_id = $("#wishlist_id").val();
        let name = $("#item_name").val();
        let product_id = $("#product_id").val();
        let item_quantity;
        if( ($("#item_quantity").val()) == ""){
            item_quantity = 1;
        } else{
            item_quantity = $("#item_quantity").val();
        }
        let item_price;
        if( ($("#item_price").val()) == ""){
            item_price = 100;
        } else{
            item_price = $("#item_price").val();
        }
        
        let created_on = new Date();

        let data = {
            "name": name,
            "product_id": parseInt(product_id),
            "quantity": parseInt(item_quantity),
            "price": parseInt(item_price)
        };

        $("#flash_message").empty();
        
        let ajax = $.ajax({
            type: "POST",
            url: `/wishlists/${wishlist_id}/items`,
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            update_form_data_item(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });
    });

    // ****************************************
    // Retrieve an Item
    // ****************************************

    $("#retrieve-item-btn").click(function () {

        let item_id = $("#item_id").val();
        // doesn't matter
        let wishlist_id = 1;

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/wishlists/${item_id}/items/${item_id}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            update_form_data_item(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Delete an Item
    // ****************************************

    $("#delete-item-btn").click(function () {

        let item_id = $("#item_id").val();
        // doesn't matter
        let wishlist_id = 1;

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "DELETE",
            url: `/wishlists/${item_id}/items/${item_id}`,
            contentType: "application/json",
            data: '',
        })

        ajax.done(function(res){
            clear_form_data()
            flash_message("Item has been Deleted!")
        });

        ajax.fail(function(res){
            flash_message("Server error!")
        });
    });

    // ****************************************
    // Update a Wishlist Item
    // ****************************************

    $("#update-item-btn").click(function () {


        let wishlist_id = $("#wishlist_id").val();
        let item_id = $("#item_id").val();
        let name = $("#item_name").val();
        let quantity = $("#item_quantity").val();
        // Update is only renaming a wishlist, since you cant change items between different customers
        // let customer_id = $("#customer_id").val();

        let data = {
            "product_name": name,
            "quantity": quantity
        };

        $("#flash_message").empty();

        let ajax = $.ajax({
                type: "PUT",
                url: `/wishlists/${wishlist_id}/items/${item_id}`,
                contentType: "application/json",
                data: JSON.stringify(data)
            })

        ajax.done(function(res){
            update_form_data_item(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });


    // ****************************************
    // Search for a Wishlist Item
    // ****************************************

    $("#search-item-btn").click(function () {

        let wishlist_id = $("#wishlist_id").val();
        let item_id = $("#item_id").val();
        let item_name = $("#item_name").val();

        let queryString = ""

        if(item_id){
            get_url = `/wishlists/${item_id}/items/${item_id}`
        } else if (item_name){
            // have to implement this in route
            // delaying to write test as well
            queryString += 'name=' + item_name
            get_url = `/wishlists/${wishlist_id}/items?${queryString}`
        } else{
            get_url = `/wishlists/${wishlist_id}/items`
        }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: get_url,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            $("#search_item_results").empty();
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-1">Item ID</th>'
            table += '<th class="col-md-3">Name</th>'
            table += '<th class="col-md-1">Product ID</th>'
            table += '<th class="col-md-1">Quantity</th>'
            table += '<th class="col-md-2">Price</th>'
            table += '<th class="col-md-5">Created On</th>'
            table += '</tr></thead><tbody>'
            let firstIList = "";
            if(item_id){
                let item = res;
                table +=  `<tr id="row_0"><td>${item.id}</td><td>${item.name}</td><td>${item.product_id}</td><td>${item.quantity}</td>
                <td>${item.price}</td><td>${item.created_on}</td></tr>`;
                firstIList = item;
            }
            else{
                res = res.items;
                for(let i = 0; i < res.length; i++) {
                    let item = res[i];
                    table +=  `<tr id="row_${i}"><td>${item.id}</td><td>${item.name}</td><td>${item.product_id}</td><td>${item.quantity}</td>
                    <td>${item.price}</td><td>${item.created_on}</td></tr>`;
                    if (i == 0) {
                        firstIList = item;
                    }
                }
            }

            table += '</tbody></table>';
            $("#search_item_results").append(table);

            // copy the first result to the form
            if (firstIList != "") {
                update_form_data_item(firstIList)
            }

            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    

})
