Feature: View Skill

  Scenario: View listed skills
    Given the job seeker is logged in
    And the job seeker has added one or more skills to the profile
    When the job seeker opens the Skills section
    Then the system should display all skills listed in the job seeker's profile


  Scenario: Display updated skills information
    Given the job seeker has modified their skills
    When the job seeker views the Skills section
    Then the system should display the latest saved skills information


  Scenario: Job seeker has no listed skills
    Given the job seeker has not added any skills to the profile
    When the job seeker opens the Skills section
    Then the system should display a "No skills have been added yet" message


  Scenario: View skills from profile page
    Given the job seeker is viewing their profile
    When the profile information is loaded
    Then the system should display the listed skills as part of the profile details