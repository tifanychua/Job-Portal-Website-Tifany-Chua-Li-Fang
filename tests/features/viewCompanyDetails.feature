Feature: View Company Details

  Scenario: Job seeker opens company details page
    Given an active company exists for company details
    When the job seeker opens the company details page
    Then the company details page should be displayed

  Scenario: Company information is displayed
    Given an active company exists for company details
    When the job seeker opens the company details page
    Then the company information should be available

  Scenario: Company location is constructed
    Given an active company exists for company details
    When the job seeker opens the company details page
    Then the company location should contain city state and country

  Scenario: Company has active jobs
    Given a company has active jobs for company details
    When the job seeker opens the company details page
    Then the active job count should be correct

  Scenario: Only latest five jobs are displayed
    Given a company has more than five active jobs
    When the job seeker opens the company details page
    Then only five latest jobs should be included on the company details page

  Scenario: Company has no active jobs
    Given a company has no active jobs for company details
    When the job seeker opens the company details page
    Then the company job count should be zero

  Scenario: Inactive jobs are excluded
    Given a company has active and inactive jobs for company details
    When the job seeker opens the company details page
    Then inactive jobs should not contribute to the company job count

  Scenario: Company has employee reviews
    Given a company has reviews for company details
    When the job seeker opens the company details page
    Then the company rating and review count should be calculated

  Scenario: Company has no reviews
    Given a company has no reviews for company details
    When the job seeker opens the company details page
    Then the company rating and review count should be zero

  Scenario: Inactive reviews are excluded
    Given a company has active and inactive reviews for company details
    When the job seeker opens the company details page
    Then only active reviews should contribute to the company rating

  Scenario: Company does not exist
    Given the requested company does not exist for company details
    When the job seeker opens the company details page
    Then the company not found page should be displayed

  Scenario: Applicant profile does not exist
    Given the applicant profile does not exist for company details
    When the job seeker opens the company details page
    Then the company details page should still be displayed safely