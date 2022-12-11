Feature: The wishlists service back-end
    As a Wishlists Service Owner
    I need a RESTful catalog service
    So that I can keep track of all my wishlists and items in them

Background:
    Given the following wishlists
        | name      | customer_id |
        | wish_1    | 3    | 
        | wish_2    | 3    | 
        | wish_3    | 4    |
        | wish_4    | 5    |

    Given the following wishlist items
        | name      | wishlist_name | product_id | quantity | price |
        | item_1    | wish_1    | 3 | 5 | 100 |
        | item_2    | wish_1    | 4 | 2 | 250 |
        | item_3    | wish_2    | 5 | 3 | 150 |
        | item_4    | wish_4    | 6 | 1 | 200 |

Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Wishlists Demo REST API Service" in the title
    And I should not see "404 Not Found"

Scenario: Create a Wishlist
    When I visit the "Home Page"
    And I set the "Wishlist Name" to "wish_5"
    And I set the "Customer Id" to "5"
    And I press the "Create" button
    Then I should see the message "Success"
    When I copy the "Wishlist Id" field
    And I press the "Clear" button
    Then the "Wishlist Id" field should be empty
    And the "Wishlist Name" field should be empty
    And the "Customer Id" field should be empty
    When I paste the "Wishlist Id" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "wish_5" in the "Wishlist Name" field
    And I should see "5" in the "Customer Id" field

# Scenario: List all pets
#     When I visit the "Home Page"
#     And I press the "Search" button
#     Then I should see the message "Success"
#     And I should see "fido" in the results
#     And I should see "kitty" in the results
#     And I should not see "leo" in the results

# Scenario: Search for dogs
#     When I visit the "Home Page"
#     And I set the "Category" to "dog"
#     And I press the "Search" button
#     Then I should see the message "Success"
#     And I should see "fido" in the results
#     And I should not see "kitty" in the results
#     And I should not see "leo" in the results

# Scenario: Search for available
#     When I visit the "Home Page"
#     And I select "True" in the "Available" dropdown
#     And I press the "Search" button
#     Then I should see the message "Success"
#     And I should see "fido" in the results
#     And I should see "kitty" in the results
#     And I should see "sammy" in the results
#     And I should not see "leo" in the results

Scenario: Update a Wishlist
    When I visit the "Home Page"
    And I set the "Wishlist Name" to "wish_1"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "wish_1" in the "Wishlist Name" field
    And I should see "3" in the "Customer Id" field
    When I change "Wishlist Name" to "wish_1_rename"
    And I press the "Update" button
    Then I should see the message "Success"
    When I copy the "Wishlist Id" field
    And I press the "Clear" button
    And I paste the "Wishlist Id" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "wish_1_rename" in the "Wishlist Name" field
    When I press the "Clear" button
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "wish_1_rename" in the results
    And I should not see "wish_1" in the results

# Scenario: Delete a Pet
#     When I visit the "Home Page"
#     And I set the "Name" to "fido"
#     And I press the "Search" button
#     Then I should see the message "Success"
#     And I should see "fido" in the "Name" field
#     And I should see "dog" in the "Category" field
#     When I press the "Delete" button
#     Then I should see the message "Pet has been Deleted!"
#     When I press the "Clear" button
#     And I press the "Search" button
#     Then I should see the message "Success"
#     And I should see "kitty" in the results
#     And I should not see "fido" in the results