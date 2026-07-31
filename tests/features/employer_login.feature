Feature: Employer Login
  As an Employer
  I want to log in to my account securely
  So that I can manage job postings, applications, and recruitment

  Scenario: Login successfully with valid credentials
    Given the employer has a registered company account
    When the employer enters a valid email address and password
    Then the system should authenticate the employer successfully
    And redirect the employer to the employer dashboard

  Scenario: Login with invalid credentials
    Given the employer has entered incorrect login credentials
    When the employer attempts to log in
    Then the system should display an error message
    And prevent access to the account

  Scenario: Access employer features after login
    Given the employer has logged in successfully
    When the employer accesses the platform
    Then the system should allow access to job posting, applicant management, and recruitment features

  Scenario: Login with rejected or deactivated company account
    Given the employer account status is "Rejected" or "Deactive"
    When the employer attempts to log in with valid credentials
    Then the system should block the login
    And display an account status error message