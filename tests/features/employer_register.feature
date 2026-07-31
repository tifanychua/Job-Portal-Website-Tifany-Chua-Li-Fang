Feature: Employer Register

  As an Employer
  I want to register an account using my email address
  So that I can create an employer account and begin the company verification process.

  Scenario: Successful employer account registration
    Given the employer is on the registration page
    When the employer enters valid registration details and submits the registration form
    Then the system should create a new employer account successfully
    And the employer account status should be set to "Pending"

  Scenario: Register with an existing email address
    Given the email address is already registered
    When the employer submits the registration form using that email address
    Then the system should display an "Email address already exists" message
    And the account should not be created

  Scenario: Register with invalid or incomplete information
    Given the employer is on the registration page
    When the employer submits the registration form with missing or invalid information
    Then the system should display validation messages
    And the account should not be created

  Scenario: Passwords do not match
    Given the employer is on the registration page
    When the employer enters different values for the password and confirm password fields
    Then the system should display a "Passwords do not match" message
    And the account should not be created

  Scenario: Begin company verification after registration
    Given the employer has successfully registered an account
    When the registration process is completed
    Then the employer account status should be set to "Pending"