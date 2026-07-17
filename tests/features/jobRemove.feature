Feature: Remove Job Posting

    Scenario: Employer removes a job posting
        Given the employer has an existing job posting
        When the employer selects the remove job posting option
        Then the job posting should be removed successfully

    Scenario: Update job posting status after removal
        Given the employer has removed a job posting
        When the removal process is completed
        Then the job posting status should be updated in the database

    Scenario: Job seeker cannot view removed job postings
        Given the employer has removed a job posting
        When a job seeker browses available jobs
        Then the removed job posting should not be displayed