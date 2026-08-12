Feature: Save Job Postings
  As a job seeker
  I want to save job postings
  So that I can efficiently manage and revisit potential job opportunities before submitting applications.

  Scenario: Save a job posting
    Given the job seeker is viewing a job posting
    When the job seeker selects the save option
    Then the system should add the job posting to the job seeker's saved jobs list

  Scenario: View saved job postings
    Given the job seeker has saved one or more job postings
    When the job seeker accesses the saved jobs section
    Then the system should display all saved job postings

  Scenario: Remove a saved job posting
    Given the job seeker has saved a job posting
    When the job seeker selects the remove save option
    Then the system should remove the job posting from the saved jobs list

  Scenario: Prevent duplicate saved job postings
    Given the job seeker has already saved a job posting
    When the job seeker attempts to save the same job posting again
    Then the system should prevent duplicate entries in the saved jobs list
