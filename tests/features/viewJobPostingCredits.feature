Feature: View Job Posting Credits

  Scenario: View current job posting credit balance
    Given the employer is logged into the system
    When the employer accesses the credit management page
    Then the system should display the employer's available job posting credits

  Scenario: View credit usage details
    Given the employer has used job posting credits for published vacancies
    When the employer views credit information
    Then the system should display the number of credits used and remaining credits

  Scenario: Employer has insufficient job posting credits
    Given the employer has no available job posting credits
    When the employer attempts to create a new job posting
    Then the system should notify the employer that additional credits are required before publishing a job vacancy