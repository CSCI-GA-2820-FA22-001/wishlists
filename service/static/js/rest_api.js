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
        $("#item_list").val("Will List items here");
    }

    /// Clears all form fields
    function clear_form_data() {
        $("#wishlist_name").val("");
        $("#wishlist_id").val("");
        $("customer_id").val("");
        $("item_list").val("");
        $("#created_on").val("");
        $("#item_id").val("");
        $("#item_name").val("");
        $("#product_id").val("");
        $("#item_quantity").val("");
        $("#item_price").val("");
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
        // Update is only renaming a wishlist
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

        let ajax = $.ajax({
            type: "DELETE",
            url: `/wishlist/${wishlist_id}`,
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
            
            queryString += 'category=' + category
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
            table += '<th class="col-md-2">ID</th>'
            table += '<th class="col-md-2">Name</th>'
            table += '<th class="col-md-2">Customer ID</th>'
            table += '<th class="col-md-2">Created On</th>'
            table += '</tr></thead><tbody>'
            let firstWList = "";
            for(let i = 0; i < res.length; i++) {
                let wishlist = res[i];
                table +=  `<tr id="row_${i}"><td>${wishlist.id}</td><td>${wishlist.name}</td><td>${wishlist.customer_id}</td><td>${wishlist.created_on}</td></tr>`;
                if (i == 0) {
                    firstWList = wishlist;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // copy the first result to the form
            /*if (firstPet != "") {
                update_form_data(firstPet)
            }*/

            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

})
