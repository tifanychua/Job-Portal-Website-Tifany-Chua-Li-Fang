Feature: Browse Companies
  As a Job Seeker
  I want to browse and search companies
  So that I can discover potential employers and view their available jobs and ratings.

  Scenario: Job seeker opens the browse companies page
    Given the job seeker is logged into the system
    When the job seeker opens the browse companies page
    Then the system should display the browse companies page

  Scenario: Job seeker views active companies
    Given the job seeker is viewing the browse companies page
    When the company records are loaded
    Then only active companies should be displayed

  Scenario: Inactive companies are not displayed
    Given active and inactive companies exist
    When the job seeker views the browse companies page
    Then inactive companies should not be displayed

  Scenario: Company information is displayed
    Given the job seeker is viewing the browse companies page
    When the company records are loaded
    Then the company name industry location rating review count and job count should be available

  Scenario: Company logo is available
    Given a company contains a logo
    When the company records are loaded
    Then the company logo should be included

  Scenario: Company has no logo
    Given a company does not contain a logo
    When the company records are loaded
    Then the system should handle the missing company logo safely

  Scenario: Job seeker searches by company name
    Given the job seeker is viewing the browse companies page
    When the job seeker searches using a company name
    Then matching companies should be displayed

  Scenario: Job seeker searches by partial company name
    Given the job seeker is viewing the browse companies page
    When the job seeker searches using a partial company name
    Then companies containing the partial company name should be displayed

  Scenario: Company search is case insensitive
    Given the job seeker is viewing the browse companies page
    When the job seeker searches using lowercase company name
    Then the company search should be case insensitive

  Scenario: Company search ignores extra spaces
    Given the job seeker is viewing the browse companies page
    When the job seeker searches with extra spaces
    Then the extra spaces should be ignored

  Scenario: Job seeker searches by city
    Given the job seeker is viewing the browse companies page
    When the job seeker searches using a city
    Then companies from the matching city should be displayed

  Scenario: Job seeker searches by state
    Given the job seeker is viewing the browse companies page
    When the job seeker searches using a state
    Then companies from the matching state should be displayed

  Scenario: Job seeker searches by industry
    Given the job seeker is viewing the browse companies page
    When the job seeker searches using an industry
    Then companies from the matching industry should be displayed

  Scenario: Search returns no company
    Given the job seeker is viewing the browse companies page
    When the job seeker searches for a company that does not exist
    Then the system should return an empty company result without crashing

  Scenario: Empty search displays all active companies
    Given the job seeker is viewing the browse companies page
    When the job seeker searches without entering a keyword
    Then all active companies should remain available

  Scenario: Company active job count is calculated
    Given a company has active and inactive job postings
    When the company records are loaded
    Then only active jobs should contribute to the company job count

  Scenario: Company has no active jobs
    Given a company has no active job postings
    When the company records are loaded
    Then the company job count should be zero

  Scenario: Company average rating is calculated
    Given a company has multiple reviews
    When the company rating is calculated
    Then the average company rating should be correct

  Scenario: Company rating is rounded to one decimal place
    Given a company has reviews producing a decimal average
    When the company rating is calculated
    Then the company rating should be rounded to one decimal place

  Scenario: Company has no reviews
    Given a company has no reviews
    When the company rating is calculated
    Then the company rating and review count should be zero

  Scenario: Companies are sorted by highest rating
    Given companies have different ratings
    When the company records are loaded
    Then the company with the highest rating should be displayed first

  Scenario: Companies with same rating are sorted by review count
    Given companies have the same rating but different review counts
    When the company records are loaded
    Then the company with more reviews should be displayed first

  Scenario: Fewer than twelve companies are available
    Given fewer than twelve active companies exist
    When the job seeker views the first company page
    Then only one company page should be required

  Scenario: Exactly twelve companies are available
    Given exactly twelve active companies exist
    When the job seeker views the company list
    Then only one company page should be required

  Scenario: Thirteen companies are available
    Given thirteen active companies exist
    When the job seeker views the company list
    Then two company pages should be required

  Scenario: Job seeker views second company page
    Given more than twelve active companies exist
    When the job seeker opens company page two
    Then the remaining companies should be displayed

  Scenario: No active companies exist
    Given no active companies exist
    When the job seeker views the browse companies page
    Then the system should handle the empty company list successfully

  Scenario: Applicant profile does not exist
    Given the logged in applicant profile does not exist
    When the job seeker opens the browse companies page
    Then the company page should still be displayed safely