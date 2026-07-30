Feature: View Profile

  Scenario: View profile information
    Given the job seeker is logged in
    When the job seeker opens the Profile page
    Then the system should display the job seeker's profile information

  Scenario: Display the latest profile information
    Given the job seeker is viewing the Profile page
    When the profile information is loaded
    Then the system should display the latest saved profile details

  Scenario: Profile contains no optional information
    Given the job seeker has not completed all optional profile fields
    When the job seeker opens the Profile page
    Then the system should display the available profile information
    And indicate any empty optional fields