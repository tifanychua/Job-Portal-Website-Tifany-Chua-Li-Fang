Feature: Filter Applicants by Job Position

  Scenario: Filter applicants by job successfully
    Given the employer has one or more job postings with applicants
    When the employer selects a specific job position from the filter option
    Then the system should display only applicants who applied for the selected job position

  Scenario: View all applicants without applying a filter
    Given the employer is on the Applicant Management page
    When the employer does not select any job position filter
    Then the system should display all applicants from all job postings

  Scenario: Filter applicants for a job position with no applicants
    Given the employer selects a job position that has no applicants
    When the system applies the filter
    Then the system should display a "No applicants found for this job position" message

  Scenario: Update applicant list after changing job position filter
    Given the employer is viewing filtered applicants
    When the employer selects a different job position filter
    Then the system should refresh the applicant list
    And display applicants related to the newly selected job position

  Scenario: Employer views applicant details after filtering
    Given the employer has filtered applicants by job position
    When the employer selects an applicant from the filtered list
    Then the system should display the applicant's details and application information