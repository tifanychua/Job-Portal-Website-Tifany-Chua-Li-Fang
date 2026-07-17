Feature: Publish Job Posting

    Scenario: Employer publishes a job posting
        Given the employer has created a job posting
        When the employer submits the job posting for publication
        Then the job posting should be published successfully

    Scenario: Save published job posting
        Given the employer has published a job posting
        When the publication process is completed
        Then the job posting information should be saved in the database

    Scenario: Job seeker views published job posting
        Given the employer has published a job posting
        When a job seeker browses available jobs
        Then the published job posting should be displayed