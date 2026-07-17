Feature: View Job Applications

    Scenario: Employer views applicants for a job posting
        Given the employer has an active job posting
        And applicants have submitted applications
        When the employer opens the applicant list
        Then the system should display the list of applicants