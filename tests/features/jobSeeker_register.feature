Feature: Job Seeker Register

  As a Job Seeker
  I want to register an account using my email address
  So that I can securely access the job portal and utilize features such as browsing and applying for job opportunities.

  Scenario: Successful account registration
    Given the job seeker is on the registration page
    When the job seeker enters valid registration information
    Then the system should create a new job seeker account successfully

  Scenario: Register with an existing email address
    Given the email address is already registered
    When the job seeker submits the registration form using that email address
    Then the system should display an "Email address already exists" message
    And the account should not be created

  Scenario: Register with invalid or incomplete information
    Given the job seeker is on the registration page
    When the job seeker submits the registration form with missing or invalid information
    Then the system should display appropriate validation messages
    And the account should not be created

  Scenario: Passwords do not match
    Given the job seeker is on the registration page
    When the job seeker enters different values for the password and confirm password fields
    Then the system should display a "Passwords do not match" message
    And the account should not be created

  Scenario: Registration completed successfully
    Given the job seeker has successfully registered an account
    When the registration process is completed
    Then the system should allow the job seeker to proceed to login