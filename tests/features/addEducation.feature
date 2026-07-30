Feature: Add Education

  Background:
    Given the job seeker is on the Manage Education page

  Scenario: Successfully add a new education record
    When the job seeker enters valid education information
    And submits the education form
    Then the education record should be saved successfully
    And the system should redirect to the Manage Education page

  Scenario: Qualification is missing
    When the job seeker leaves the qualification empty
    And submits the education form
    Then the system should display "Please select your qualification."
    And the education record should not be saved

  Scenario: Institution is missing
    When the job seeker leaves the institution empty
    And submits the education form
    Then the system should display "Please enter your institution."
    And the education record should not be saved

  Scenario: Start date is missing
    When the job seeker leaves the start date empty
    And submits the education form
    Then the system should display "Please select your start date."
    And the education record should not be saved

  Scenario: End date is missing
    Given the job seeker is not currently studying
    When the job seeker leaves the end date empty
    And submits the education form
    Then the system should display "Please select your end date."
    And the education record should not be saved

  Scenario: Invalid study period
    When the job seeker enters an end date earlier than the start date
    And submits the education form
    Then the system should display "Invalid study period."
    And the education record should not be saved

  Scenario: Duplicate education record
    Given an identical education record already exists
    When the job seeker enters the same education information
    And submits the education form
    Then the system should display "This education record already exists."
    And the education record should not be duplicated