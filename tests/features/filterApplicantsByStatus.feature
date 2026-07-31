Feature: Filter Applicants by Application Status

  Scenario: Filter applicants by application status successfully
    Given the employer has received applications with different statuses
    When the employer selects an application status filter
    Then the system should display only applicants with the selected application status

  Scenario: Filter applicants by new applications
    Given the employer has applicants with a "New" status
    When the employer selects the "New" status filter
    Then the system should display all applicants whose applications are new

  Scenario: Filter applicants by shortlisted applications
    Given the employer has applicants with a "Shortlisted" status
    When the employer selects the "Shortlisted" status filter
    Then the system should display all shortlisted applicants

  Scenario: Filter applicants by rejected or offered applications
    Given the employer has applicants with different recruitment outcomes
    When the employer selects the "Rejected" or "Offered" status filter
    Then the system should display applicants matching the selected status

  Scenario: View all applicants without applying status filter
    Given the employer is on the Applicant Management page
    When the employer does not select any application status filter
    Then the system should display all applicants regardless of their status

  Scenario: No applicants found for selected status
    Given the employer applies an application status filter
    When no applicants match the selected status
    Then the system should display a "No applicants found for this application status" message

  Scenario: Update applicant list after changing status filter
    Given the employer is viewing filtered applicants
    When the employer changes the application status filter
    Then the system should refresh the applicant list
    And display applicants with the updated status criteria