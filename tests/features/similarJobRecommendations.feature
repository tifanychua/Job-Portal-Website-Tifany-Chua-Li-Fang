Feature: Similar Job Recommendations
  As a Job Seeker
  I want the system to recommend similar jobs based on the job I am viewing
  So that I can easily find other opportunities that fit my preferences.

  Scenario: Display similar job recommendations
    Given the job seeker is viewing a job posting
    When the job details page is loaded
    Then the system should display a list of similar job recommendations based on the selected job posting

  Scenario: Recommend jobs based on job attributes
    Given the job seeker is viewing a job posting
    When the system generates job recommendations
    Then the system should recommend jobs with similar attributes such as job position, category or location

  Scenario: View details of recommended jobs
    Given the system has displayed similar job recommendations
    When the job seeker selects a recommended job posting
    Then the system should display the details of the selected job posting

  Scenario: No similar jobs available
    Given the job seeker is viewing a job posting with no matching opportunities
    When the system generates job recommendations
    Then the system should display a message indicating that no similar jobs are currently available
