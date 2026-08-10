Feature: Saved Jobs All and Applied Sections
  As a job seeker
  I want to view my saved jobs under All and Applied sections
  So that I can easily identify the jobs I have already applied for.

  Scenario: View all saved jobs
    Given the job seeker has saved both applied and not-applied jobs
    When the job seeker opens the All section
    Then the system should display all jobs saved by the job seeker

  Scenario: View applied saved jobs
    Given the job seeker has saved jobs with different application statuses
    When the job seeker opens the Applied section
    Then the system should display only saved jobs that the job seeker has applied for

  Scenario: Exclude not-applied jobs from Applied section
    Given the job seeker has saved a job but has not applied for it
    When the job seeker opens the Applied section
    Then the saved job should not appear in the Applied section
    And it should remain available in the All section

  Scenario: Display application status
    Given the job seeker has applied for a saved job
    When the job seeker views the saved-job list
    Then the system should display a clear applied-status indicator for that job

  Scenario: Update Applied section after application submission
    Given the job seeker has saved a job
    And the job has not been applied for
    When the job seeker successfully submits an application for the job
    Then the saved job should appear in the Applied section
    And the job should display an applied-status indicator

  Scenario: Switch between All and Applied sections
    Given the job seeker is viewing the saved-jobs page
    When the job seeker switches between the All and Applied sections
    Then the system should update the displayed saved-job list correctly
    And clearly highlight the selected section

  Scenario: Remove a job from the saved list
    Given the job seeker has a saved job displayed in the All or Applied section
    When the job seeker removes the job from the saved list
    Then the job should be removed from both the All and Applied sections

  Scenario: No applied saved jobs available
    Given the job seeker has saved jobs but has not applied for any of them
    When the job seeker opens the Applied section
    Then the system should display a message indicating that there are no applied saved jobs

  Scenario: No saved jobs available
    Given the job seeker has not saved any jobs
    When the job seeker opens the saved-jobs page
    Then the system should display an appropriate empty-state message

  Scenario: Prevent access to another job seeker's saved jobs
    Given saved jobs belong to another job seeker
    When the current job seeker views the saved-jobs page
    Then the system should not display the other job seeker's saved jobs or application information
