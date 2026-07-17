Feature: View My Job Postings

    Scenario: Employer views all job postings
        Given the employer has created one or more job postings
        When the employer opens the Manage Jobs page
        Then the system should display all job postings created by the employer

    Scenario: Display latest job posting information
        Given the employer is viewing the Manage Jobs page
        When the job postings are loaded
        Then the latest job posting information should be displayed

    Scenario: Employer has no job postings
        Given the employer has not created any job postings
        When the employer opens the Manage Jobs page
        Then the system should display a "No jobs have been posted yet" message