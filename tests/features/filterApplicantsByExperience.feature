Feature: Filter Applicants by Experience Level

  Scenario: Filter applicants by experience level successfully
    Given the employer has received applications from candidates with different experience levels
    When the employer selects an experience level filter
    Then the system should display only applicants who match the selected experience level

  Scenario: Filter applicants by minimum years of experience
    Given the employer is viewing the Applicant Management page
    When the employer selects a minimum years of experience requirement
    Then the system should display applicants who meet or exceed the selected experience level

  Scenario: View all applicants without applying experience filter
    Given the employer is on the Applicant Management page
    When the employer does not select any experience level filter
    Then the system should display all applicants regardless of their experience level

  Scenario: No applicants found for selected experience level
    Given the employer applies an experience level filter
    When no applicants match the selected experience requirement
    Then the system should display a "No applicants found for this experience level" message

  Scenario: Update applicant list after changing experience filter
    Given the employer is viewing filtered applicants
    When the employer changes the experience level filter
    Then the system should refresh the applicant list
    And display applicants who match the updated experience criteria