Feature: Search User Accounts

  As an Admin
  I want to search for user accounts
  So that I can quickly locate specific users

  Scenario: Search for a user account by name
    Given the admin is viewing the user management section
    When the admin enters a user's name in the search field
    Then the system should display user accounts that match the entered name

  Scenario: Search for a user account by email
    Given the admin is viewing the user management section
    When the admin enters a user's email address in the search field
    Then the system should display the user account associated with the entered email address

  Scenario: No matching user accounts found
    Given the admin is viewing the user management section
    When the entered search criteria do not match any registered users
    Then the system should display a message indicating that no user accounts were found

  Scenario: Clear user account search
    Given the admin has entered search criteria and is viewing filtered results
    When the admin clears the search field
    Then the system should display the complete list of registered user accounts