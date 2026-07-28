Feature: Administrator Login

  As an Admin
  I want to log in securely to the system
  So that I can access administrative features and manage the platform efficiently.

  Scenario: Login successfully with valid admin credentials
    Given the admin has a registered administrator account
    When the admin enters a valid email address and password
    Then the system should authenticate the admin successfully
    And redirect the admin to the administration dashboard

  Scenario: Login with invalid credentials
    Given the admin has entered incorrect login credentials
    When the admin attempts to log in
    Then the system should display an error message
    And prevent access to administrative features

  Scenario: Login with empty required fields
    Given the admin is on the login page
    When the admin leaves the email address or password field empty
    And attempts to log in
    Then the system should display validation messages
    And request the admin to complete the required fields

  Scenario: Access administrative features after login
    Given the admin has logged in successfully
    When the admin accesses the system
    Then the system should allow access to platform management features