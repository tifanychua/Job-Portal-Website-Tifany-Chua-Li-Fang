Feature: Update Job Seeker Skill

  Scenario: Update an existing skill successfully
    Given the job seeker has an existing skill listed in the profile
    When the job seeker edits the skill information and saves the changes
    Then the system should update the skill successfully
    And display the updated skill in the profile

  Scenario: Update the skill level successfully
    Given the job seeker has an existing skill listed in the profile
    When the job seeker changes the skill level and saves the changes
    Then the system should update the skill level successfully

  Scenario: Update multiple skills successfully
    Given the job seeker has multiple skills listed in the profile
    When the job seeker updates multiple skills
    Then the system should save all updated skills successfully

  Scenario: Change industry category and skill successfully
    Given the job seeker has an existing skill listed in the profile
    When the job seeker changes the industry category skill and saves the changes
    Then the system should display the updated skill information

  Scenario: Prevent duplicate skills during update
    Given the job seeker already has a skill listed in the profile
    When the job seeker updates another skill to the same skill
    Then the system should prevent duplicate skills from being saved
    And display an appropriate validation message

  Scenario: Update skill using an invalid document id
    Given the selected skill does not exist
    When the job seeker submits the update
    Then the system should display an error message

  Scenario: Cancel skill update
    Given the job seeker is editing an existing skill
    When the job seeker cancels the update
    Then the original skill information should remain unchanged

  Scenario: Update skill without changing any information
    Given the job seeker has an existing skill listed in the profile
    When the job seeker saves the skill without making any changes
    Then the system should keep the existing skill information

  Scenario: Update skill with an empty industry
    Given the job seeker is editing a skill
    When the job seeker submits the form without selecting an industry
    Then the system should display a validation message

  Scenario: Update skill with an empty category
    Given the job seeker is editing a skill
    When the job seeker submits the form without selecting a category
    Then the system should display a validation message

  Scenario: Update skill with an empty skill
    Given the job seeker is editing a skill
    When the job seeker submits the form without selecting a skill
    Then the system should display a validation message

  Scenario: Update skill with an empty skill level
    Given the job seeker is editing a skill
    When the job seeker submits the form without selecting a skill level
    Then the system should display a validation message