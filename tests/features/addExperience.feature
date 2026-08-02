Feature: Add Experience

  Background:
    Given the job seeker is on the Manage Experience page

  Scenario: Successfully add a new experience record
    When the job seeker enters valid experience information
    And submits the experience form
    Then the experience record should be saved successfully
    And the system should redirect to the Manage Experience page

  Scenario: Job title is missing
    When the job seeker leaves the job title empty
    And submits the experience form
    Then the system should display "Please enter your job title."
    And the experience record should not be saved

  Scenario: Company name is missing
    When the job seeker leaves the company name empty
    And submits the experience form
    Then the system should display "Please enter your company name."
    And the experience record should not be saved

  Scenario: Employment type is missing
    When the job seeker leaves the employment type empty
    And submits the experience form
    Then the system should display "Please select your employment type."
    And the experience record should not be saved

  Scenario: Location is missing
    When the job seeker leaves the location empty
    And submits the experience form
    Then the system should display "Please enter your location."
    And the experience record should not be saved

  Scenario: Start date is missing
    When the job seeker leaves the start date empty
    And submits the experience form
    Then the system should display "Please select your start date."
    And the experience record should not be saved

  Scenario: End date is missing
    Given the job seeker is not currently working
    When the job seeker leaves the end date empty
    And submits the experience form
    Then the system should display "Please select your end date."
    And the experience record should not be saved

  Scenario: Invalid employment period
    When the job seeker enters an end date earlier than the start date
    And submits the experience form
    Then the system should display "Invalid employment period."
    And the experience record should not be saved

  Scenario: Duplicate experience record
    Given an identical experience record already exists
    When the job seeker enters the same experience information
    And submits the experience form
    Then the system should display "This experience record already exists."
    And the experience record should not be duplicated