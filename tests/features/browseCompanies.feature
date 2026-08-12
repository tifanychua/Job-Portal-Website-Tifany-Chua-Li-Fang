Feature: View Company List

  Scenario: Job seeker opens the company list
    Given the job seeker is logged into the system
    When the job seeker opens the browse companies page
    Then the system should display the browse companies page

  Scenario: Display active companies
    Given active companies exist
    When the job seeker opens the browse companies page
    Then the active companies should be displayed

  Scenario: Do not display inactive companies
    Given active and inactive companies exist
    When the job seeker opens the browse companies page
    Then inactive companies should not be displayed

  Scenario: Display company information
    Given active companies exist
    When the job seeker opens the browse companies page
    Then each company should display its company name industry location rating review count and job count

  Scenario: Display company logo
    Given an active company contains a logo
    When the job seeker opens the browse companies page
    Then the company logo should be available

  Scenario: Company has no logo
    Given an active company does not contain a logo
    When the job seeker opens the browse companies page
    Then the missing company logo should be handled safely

  Scenario: Display company available job count
    Given an active company has available jobs
    When the job seeker opens the browse companies page
    Then the number of available jobs should be displayed

  Scenario: Display company with no available jobs
    Given an active company has no available jobs
    When the job seeker opens the browse companies page
    Then the company job count should display zero

  Scenario: Display company rating
    Given an active company has company reviews
    When the job seeker opens the browse companies page
    Then the company rating and review count should be displayed

  Scenario: Display company with no reviews
    Given an active company has no company reviews
    When the job seeker opens the browse companies page
    Then the company rating and review count should display zero

  Scenario: No active companies available
    Given no active companies exist
    When the job seeker opens the browse companies page
    Then the system should display an empty company list without crashing