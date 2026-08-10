Feature: View Company Jobs
  As a Job Seeker
  I want to view jobs posted by a company
  So that I can find suitable employment opportunities.

  Scenario: Job seeker opens company jobs page
    Given an active company exists for company jobs
    When the job seeker opens the company jobs page
    Then the company jobs page should be displayed

  Scenario: Company information is available on jobs page
    Given an active company exists for company jobs
    When the job seeker opens the company jobs page
    Then the company information should be available on the jobs page

  Scenario: Only active jobs are displayed
    Given the company has active and inactive jobs
    When the job seeker opens the company jobs page
    Then only active company jobs should be returned

  Scenario: Company active job count is calculated
    Given the company has active and inactive jobs
    When the job seeker opens the company jobs page
    Then the company active job count should be correct

  Scenario: Fixed salary is formatted
    Given the company has a fixed salary job
    When the job seeker opens the company jobs page
    Then the fixed salary should be formatted correctly

  Scenario: Fixed salary contains comma
    Given the company has a fixed salary stored with comma
    When the job seeker opens the company jobs page
    Then the fixed salary with comma should be formatted correctly

  Scenario: Invalid fixed salary is handled
    Given the company has an invalid fixed salary
    When the job seeker opens the company jobs page
    Then the invalid fixed salary should become negotiable

  Scenario: Salary range is formatted
    Given the company has a salary range job
    When the job seeker opens the company jobs page
    Then the salary range should be formatted correctly

  Scenario: Invalid salary range is handled
    Given the company has an invalid salary range
    When the job seeker opens the company jobs page
    Then the invalid salary range should become negotiable

  Scenario: Negotiable salary is handled
    Given the company has a negotiable salary job
    When the job seeker opens the company jobs page
    Then the salary should be negotiable

  Scenario: Unknown salary type is handled
    Given the company has a job with unknown salary type
    When the job seeker opens the company jobs page
    Then the unknown salary type should become negotiable

  Scenario: Company has no active jobs
    Given the company has no active jobs for company jobs page
    When the job seeker opens the company jobs page
    Then the company jobs list should be empty

  Scenario: Company review summary is available on jobs page
    Given the company has reviews for company jobs
    When the job seeker opens the company jobs page
    Then the company rating should be available on the jobs page

  Scenario: Company does not exist
    Given the requested company does not exist for company jobs
    When the job seeker opens the company jobs page
    Then the company jobs not found page should be displayed