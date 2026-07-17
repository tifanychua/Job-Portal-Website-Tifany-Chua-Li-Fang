Feature: Update Job Posting

    Scenario: Employer updates a job posting
        Given the employer has an existing job posting
        When the employer edits the job posting information
        Then the job posting should be updated successfully

    Scenario: Save updated job posting information
        Given the employer has updated a job posting
        When the update process is completed
        Then the updated job information should be saved in the database

    Scenario: Job seeker views updated job information
        Given the employer has updated a job posting
        When the job seeker views the job posting
        Then the latest job information should be displayed