Feature: View Saved Job Postings
  As a job seeker
  I want to view my saved job postings
  So that I can easily access and manage job opportunities that match my interests.

  Scenario: View saved job postings list
    Given the job seeker has saved one or more job postings
    When the job seeker accesses the saved jobs section
    Then the system should display a list of all saved job postings

  Scenario: View details of a saved job posting
    Given the job seeker is viewing the saved jobs list
    When the job seeker selects a saved job posting
    Then the system should display the complete details of the selected job posting

  Scenario: Saved jobs list is empty
    Given the job seeker has no saved job postings
    When the job seeker accesses the saved jobs section
    Then the system should display a message indicating that no saved job postings are available

  Scenario: Access saved job postings after login
    Given the job seeker has previously saved job postings
    When the job seeker logs into the system and accesses the saved jobs section
    Then the system should retrieve and display the saved job postings associated with the job seeker's account
