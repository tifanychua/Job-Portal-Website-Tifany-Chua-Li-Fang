Feature: Edit Education

  Background:
    Given the job seeker has an existing education record

  Scenario: Successfully update an education record
    When the job seeker enters valid updated education information
    And submits the edit education form
    Then the education record should be updated successfully
    And the system should redirect to the Manage Education page

  Scenario: Qualification is missing
    When the job seeker clears the qualification
    And submits the edit education form
    Then the system should display "Please select your qualification."
    And the education record should remain unchanged

  Scenario: Institution is missing
    When the job seeker clears the institution
    And submits the edit education form
    Then the system should display "Please enter your institution."
    And the education record should remain unchanged

  Scenario: Start date is missing
    When the job seeker clears the start date
    And submits the edit education form
    Then the system should display "Please select your start date."
    And the education record should remain unchanged

  Scenario: End date is missing
    Given the job seeker is not currently studying
    When the job seeker clears the end date
    And submits the edit education form
    Then the system should display "Please select your end date."
    And the education record should remain unchanged

  Scenario: Invalid study period
    When the job seeker enters an end date earlier than the start date
    And submits the edit education form
    Then the system should display "Invalid study period."
    And the education record should remain unchanged

  Scenario: Duplicate education record
    Given another identical education record already exists
    When the job seeker enters duplicate education information
    And submits the edit education form
    Then the system should display "This education record already exists."
    And the education record should remain unchanged

  Scenario: Education record not found
    Given the education record does not exist
    When the job seeker submits the edit education form
    Then the system should display "Education not found"