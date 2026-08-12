Feature: Remove Saved Job Postings
  As a job seeker
  I want to remove saved job postings
  So that I can maintain an organized list of relevant job opportunities and focus on positions that match my interests.

  Scenario: Remove a saved job posting
    Given the job seeker has saved one or more job postings
    When the job seeker selects the remove option for a saved job posting
    Then the system should remove the selected job posting from the saved jobs list

  Scenario: Confirm removal of saved job posting
    Given the job seeker has selected a saved job posting to remove
    When the removal action is completed
    Then the system should display a confirmation message indicating that the job posting has been removed

  Scenario: View updated saved jobs list after removal
    Given the job seeker has removed a saved job posting
    When the job seeker accesses the saved jobs section
    Then the system should display the updated list without the removed job posting

  Scenario: Attempt to remove a job posting that is not saved
    Given the job seeker has not saved the selected job posting
    When the job seeker attempts to remove the job posting from saved jobs
    Then the system should prevent the removal action and display an appropriate message
