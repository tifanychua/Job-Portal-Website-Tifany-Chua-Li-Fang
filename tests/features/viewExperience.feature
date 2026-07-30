Feature: View Experience

  Scenario: Successfully view work experience records
    Given the job seeker has one or more work experience records
    When the job seeker opens the Manage Experience page
    Then the system should display all work experience records

  Scenario: No work experience records available
    Given the job seeker has no work experience records
    When the job seeker opens the Manage Experience page
    Then the system should display the empty work experience message
