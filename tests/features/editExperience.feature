Feature: Edit Experience

  Background:
    Given the job seeker has an existing experience record

  Scenario: Successfully update an experience record
    When the job seeker enters valid updated experience information
    And submits the edit experience form
    Then the experience record should be updated successfully
    And the system should redirect to the Manage Experience page

  Scenario: Job title is missing
    When the job seeker clears the job title
    And submits the edit experience form
    Then the system should display "Please enter your job title."
    And the experience record should remain unchanged

  Scenario: Company name is missing
    When the job seeker clears the company name
    And submits the edit experience form
    Then the system should display "Please enter your company name."
    And the experience record should remain unchanged

  Scenario: Employment type is missing
    When the job seeker clears the employment type
    And submits the edit experience form
    Then the system should display "Please select your employment type."
    And the experience record should remain unchanged

  Scenario: Location is missing
    When the job seeker clears the location
    And submits the edit experience form
    Then the system should display "Please enter your location."
    And the experience record should remain unchanged

  Scenario: Start date is missing
    When the job seeker clears the start date
    And submits the edit experience form
    Then the system should display "Please select your start date."
    And the experience record should remain unchanged

  Scenario: End date is missing
    Given the job seeker is not currently working
    When the job seeker clears the end date
    And submits the edit experience form
    Then the system should display "Please select your end date."
    And the experience record should remain unchanged

  Scenario: Invalid employment period
    When the job seeker enters an end date earlier than the start date
    And submits the edit experience form
    Then the system should display "Invalid employment period."
    And the experience record should remain unchanged

  Scenario: Duplicate experience record
    Given another identical experience record already exists
    When the job seeker enters duplicate experience information
    And submits the edit experience form
    Then the system should display "This experience record already exists."
    And the experience record should remain unchanged

  Scenario: Experience record not found
    Given the experience record does not exist
    When the job seeker submits the edit experience form
    Then the system should display "Experience not found."