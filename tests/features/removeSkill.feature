Feature: Remove Job Seeker Skill

  As a Job Seeker
  I want to remove outdated or irrelevant skills from my profile
  So that my skill information remains accurate and relevant to potential employers.

  Scenario: Remove an existing skill successfully
    Given the job seeker has one or more skills listed in the profile
    When the job seeker removes a skill
    Then the system should remove the selected skill successfully
    And update the skill list displayed in the profile

  Scenario: Remove multiple skills successfully
    Given the job seeker has multiple skills listed in the profile
    When the job seeker removes multiple skills one by one
    Then the system should remove all selected skills successfully
    And display the remaining skills in the profile

  Scenario: Cancel skill removal
    Given the job seeker selects a skill to remove
    When the job seeker cancels the removal confirmation
    Then the system should keep the skill unchanged in the profile

  Scenario: Remove the last remaining skill
    Given the job seeker has only one skill listed
    When the job seeker removes the skill
    Then the system should remove the skill successfully
    And display a "No skills have been added yet" message

  Scenario: Remove a skill using an invalid document ID
    Given the document ID does not exist
    When the job seeker submits the delete request
    Then the system should display an error message