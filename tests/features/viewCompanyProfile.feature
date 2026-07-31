Feature: View Company Profile

  Scenario: View company profile information
    Given the employer is logged in
    When the employer opens the Company Profile page
    Then the system should display the company profile information

  Scenario: Display the latest company profile information
    Given the employer is viewing the Company Profile page
    When the company profile information is loaded
    Then the system should display the latest saved company profile details

  Scenario: Company profile contains no optional information
    Given the employer has not completed all optional company profile fields
    When the employer opens the Company Profile page
    Then the system should display the available company profile information
    And indicate any empty optional fields