Feature: Write Company Review
  As a Job Seeker
  I want to write and submit a company review
  So that I can share my employment experience with other job seekers.

  Scenario: Job seeker opens the write company review page
    Given a job seeker is logged in
    And the company exists
    When the job seeker opens the write company review page
    Then the write company review page should be displayed

  Scenario: Company information is available on the review page
    Given a job seeker is logged in
    And the company exists
    When the job seeker opens the write company review page
    Then the company information should be available

  Scenario: Applicant information is available on the review page
    Given a job seeker is logged in
    And the applicant profile exists
    And the company exists
    When the job seeker opens the write company review page
    Then the applicant information should be available

  Scenario: Missing applicant profile is handled safely
    Given a job seeker is logged in
    And the applicant profile does not exist
    And the company exists
    When the job seeker opens the write company review page
    Then the review page should still be displayed safely

  Scenario: Company does not exist when opening review page
    Given a job seeker is logged in
    And the requested company does not exist
    When the job seeker opens the write company review page expecting an error
    Then company not found should be returned

  Scenario: Job seeker submits a complete company review
    Given a job seeker is logged in
    And the company exists
    When the job seeker submits a complete company review
    Then the company review should be saved
    And the saved review should contain the correct company and applicant IDs
    And the review status should be active
    And the job seeker should be redirected to the company reviews page

  Scenario: Overall rating is saved
    Given a job seeker is logged in
    And the company exists
    When the job seeker submits a complete company review
    Then the overall rating should be saved correctly

  Scenario: Employment information is saved
    Given a job seeker is logged in
    And the company exists
    When the job seeker submits a complete company review
    Then the employment information should be saved correctly

  Scenario: Review content is saved
    Given a job seeker is logged in
    And the company exists
    When the job seeker submits a complete company review
    Then the review title recommendation pros cons and comments should be saved correctly

  Scenario: Category ratings are saved
    Given a job seeker is logged in
    And the company exists
    When the job seeker submits a complete company review
    Then all category ratings should be saved correctly

  Scenario: Current employee is stored as still working
    Given a job seeker is logged in
    And the company exists
    When the job seeker submits a review as a current employee
    Then still working should be true

  Scenario: Former employee is stored as not still working
    Given a job seeker is logged in
    And the company exists
    When the job seeker submits a review as a former employee
    Then still working should be false

  Scenario: Optional review fields may be empty
    Given a job seeker is logged in
    And the company exists
    When the job seeker submits a review with empty optional fields
    Then the optional review fields should be saved as empty values

  Scenario: Review creation time is recorded
    Given a job seeker is logged in
    And the company exists
    When the job seeker submits a complete company review
    Then the review creation time should be recorded

  Scenario: Company does not exist when submitting review
    Given a job seeker is logged in
    And the requested company does not exist
    When the job seeker submits a company review expecting an error
    Then company not found should be returned

  Scenario: Non job seeker cannot access review page
    Given the user is not a job seeker
    When the user tries to open the write company review page
    Then access denied should be returned

  Scenario: Job seeker without applicant ID cannot access review page
    Given the user session is job seeker without applicant ID
    When the user tries to open the write company review page
    Then login required should be returned
