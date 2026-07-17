Feature: View Applicant Resume

    Scenario: Employer views applicant resume
        Given the employer has received a job application
        When the employer accesses the applicant's resume
        Then the resume should be displayed securely

    Scenario: Restrict unauthorized resume access
        Given a user is not the employer who received the application
        When the user attempts to access the applicant's resume
        Then access to the resume should be denied