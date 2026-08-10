Feature: View Company Reviews
  As a Job Seeker
  I want to view company employee reviews
  So that I can understand employee experiences before applying.

  Scenario: Job seeker opens company reviews page
    Given an active company exists for company reviews
    When the job seeker opens the company reviews page
    Then the company reviews page should be displayed

  Scenario: Only active reviews are displayed
    Given the company has active and inactive reviews
    When the job seeker opens the company reviews page
    Then only active company reviews should be returned

  Scenario: Overall rating is calculated
    Given the company has multiple active reviews
    When the job seeker opens the company reviews page
    Then the overall company rating should be correct

  Scenario: Review count is calculated
    Given the company has multiple active reviews
    When the job seeker opens the company reviews page
    Then the company review count should be correct

  Scenario: Work environment average is calculated
    Given the company has multiple active reviews
    When the job seeker opens the company reviews page
    Then the work environment average should be correct

  Scenario: Management average is calculated
    Given the company has multiple active reviews
    When the job seeker opens the company reviews page
    Then the management average should be correct

  Scenario: Career growth average is calculated
    Given the company has multiple active reviews
    When the job seeker opens the company reviews page
    Then the career growth average should be correct

  Scenario: Work life balance average is calculated
    Given the company has multiple active reviews
    When the job seeker opens the company reviews page
    Then the work life balance average should be correct

  Scenario: Benefits average is calculated
    Given the company has multiple active reviews
    When the job seeker opens the company reviews page
    Then the benefits average should be correct

  Scenario: Company culture average is calculated
    Given the company has multiple active reviews
    When the job seeker opens the company reviews page
    Then the company culture average should be correct

  Scenario: Learning opportunities average is calculated
    Given the company has multiple active reviews
    When the job seeker opens the company reviews page
    Then the learning opportunities average should be correct

  Scenario: Five star reviews are counted
    Given reviews with all star ratings exist
    When the job seeker opens the company reviews page
    Then the five star review count should be correct

  Scenario: Four star reviews are counted
    Given reviews with all star ratings exist
    When the job seeker opens the company reviews page
    Then the four star review count should be correct

  Scenario: Three star reviews are counted
    Given reviews with all star ratings exist
    When the job seeker opens the company reviews page
    Then the three star review count should be correct

  Scenario: Two star reviews are counted
    Given reviews with all star ratings exist
    When the job seeker opens the company reviews page
    Then the two star review count should be correct

  Scenario: One star reviews are counted
    Given reviews with all star ratings exist
    When the job seeker opens the company reviews page
    Then the one star review count should be correct

  Scenario: Company has no reviews
    Given the company has no active reviews
    When the job seeker opens the company reviews page
    Then all company review summary values should be zero

  Scenario: Missing review category values are handled
    Given an active review contains missing category ratings
    When the job seeker opens the company reviews page
    Then missing category ratings should be treated safely

  Scenario: Company active job count is available on reviews page
    Given the company has active jobs for company reviews
    When the job seeker opens the company reviews page
    Then the company job count should be available on the reviews page

  Scenario: Company does not exist
    Given the requested company does not exist for company reviews
    When the job seeker opens the company reviews page
    Then the company reviews not found page should be displayed