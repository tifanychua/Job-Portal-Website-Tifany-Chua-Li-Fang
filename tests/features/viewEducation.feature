Feature: View Education

  Scenario: Successfully view education records
    Given the job seeker has education records
    When the job seeker visits the Manage Education page
    Then the system should display the education records

  Scenario: No education records available
    Given the job seeker has no education records
    When the job seeker visits the Manage Education page
    Then the system should display the empty education message