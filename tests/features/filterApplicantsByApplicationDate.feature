Feature: Filter Applicants by Application Date


  Scenario: Filter applicants by a specific application date
    Given the employer has received applications for one or more job postings
    When the employer selects a specific application date filter
    Then the system should display only applicants who submitted applications on the selected date

  Scenario: Filter applicants within a date range
    Given the employer is viewing the Applicant Management page
    When the employer selects a start date and end date for filtering
    Then the system should display applicants who applied within the selected date range

  Scenario: View all applicants without applying a date filter
    Given the employer is on the Applicant Management page
    When the employer does not apply any application date filter
    Then the system should display all applicants regardless of application date

  Scenario: No applicants found for selected date
    Given the employer applies an application date filter
    When no applicants match the selected date or date range
    Then the system should display a "No applicants found for this date range" message

  Scenario: Update applicant list after changing date filter
    Given the employer is viewing filtered applicants
    When the employer changes the application date filter
    Then the system should refresh the applicant list
    And display applicants matching the new date criteria