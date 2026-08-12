Feature: View Registered User Accounts

  As an Admin
  I want to view registered user accounts
  So that I can monitor platform usage and manage user information

  Scenario: View list of registered user accounts
    Given the admin is logged into the admin dashboard
    When the admin accesses the user management section
    Then the system should display a list of all registered user accounts

  Scenario: View user account details
    Given the admin is viewing the registered user accounts list
    When the registered user accounts are displayed
    Then the system should display each user's account details
    And the details should include the user's personal information and account status

  Scenario: Filter registered user accounts
    Given the admin is viewing the user management section
    When the admin filters the accounts by user type or account status
    Then the system should display only the user accounts that match the selected criteria

  Scenario: Search registered user accounts
    Given the admin is viewing the user management section
    When the admin enters a user's name or email address in the search field
    Then the system should display the user accounts that match the search criteria