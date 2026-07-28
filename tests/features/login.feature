Feature: Job Seeker Login

  As a Job Seeker
  I want to log in to my account securely
  So that I can access my profile, search for job opportunities, and manage my applications.

  Scenario: Login successfully with valid credentials
    Given the job seeker has a registered account
    When the job seeker enters a valid email address and password
    Then the system should authenticate the user successfully
    And redirect the job seeker to the dashboard

  Scenario: Login with invalid credentials
    Given the job seeker has entered incorrect login credentials
    When the job seeker attempts to log in
    Then the system should display an error message
    And prevent access to the account

  Scenario: Login with empty required fields
    Given the job seeker is on the login page
    When the job seeker leaves the email address or password field empty
    And attempts to log in
    Then the system should display validation messages
    And request the job seeker to complete the required fields

  Scenario: Access account features after login
    Given the job seeker has logged in successfully
    When the job seeker accesses the platform
    Then the system should allow access to profile and job search features