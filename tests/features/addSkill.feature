Feature: Add Skill

  Scenario: Add skills successfully
    Given the job seeker is logged in
    And is on the Edit Profile page
    When the job seeker enters one or more skills and saves the profile
    Then the system should save the skills successfully
    And display the updated skills in the profile

  Scenario: Add multiple skills
    Given the job seeker is on the Edit Profile page
    When the job seeker adds multiple skills and saves the profile
    Then the system should display all added skills in the profile

  Scenario: Save profile without adding skills
    Given the job seeker is on the Edit Profile page
    When the job seeker leaves the skills section empty and saves the profile
    Then the system should save the profile
    And indicate that no skills have been added

  Scenario: Add skills with different proficiency levels
    Given the job seeker is on the Edit Profile page
    When the job seeker adds skills with different proficiency levels
    Then the system should save all skills with their selected proficiency levels

  Scenario: Add a skill after previously having no skills
    Given the job seeker has no skills in the profile
    When the job seeker adds a new skill and saves the profile
    Then the system should display the newly added skill in the profile

  Scenario: Add duplicate skills
    Given the job seeker has already added a skill
    When the job seeker attempts to add the same skill again
    Then the system should prevent duplicate skills from being added
    And display duplicate skill validation message

  Scenario: Save skill without selecting an industry
    Given the job seeker is on the Edit Profile page
    When the job seeker leaves the industry field empty
    And saves the profile
    Then the system should display a validation message for the industry field

  Scenario: Save skill without selecting a skill category
    Given the job seeker is on the Edit Profile page
    When the job seeker leaves the skill category field empty
    And saves the profile
    Then the system should display a validation message for the skill category field

  Scenario: Save skill without selecting a skill
    Given the job seeker is on the Edit Profile page
    When the job seeker leaves the skill field empty
    And saves the profile
    Then the system should display a validation message for the skill field

  Scenario: Save skill without selecting a proficiency level
    Given the job seeker is on the Edit Profile page
    When the job seeker leaves the proficiency level field empty
    And saves the profile
    Then the system should display a validation message for the proficiency level field

  Scenario: Add an invalid skill that does not exist in the master skill list
    Given the job seeker is on the Edit Profile page
    When the job seeker attempts to add an invalid skill
    Then the system should reject the skill
    And display invalid skill validation message

  Scenario: Add a skill with an invalid industry-category combination
    Given the job seeker is on the Edit Profile page
    When the job seeker selects a skill category that does not belong to the selected industry
    Then the system should prevent the skill from being saved
    And display invalid category validation message