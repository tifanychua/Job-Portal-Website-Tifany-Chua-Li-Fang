Feature: Shortlist Applicant

    Scenario: Employer shortlists an applicant
        Given the employer has received job applications
        When the employer selects an applicant to shortlist
        Then the applicant status should be updated to "Shortlisted"

    Scenario: Save shortlisted applicant status
        Given the employer has shortlisted an applicant
        When the shortlist action is completed
        Then the updated applicant status should be saved in the database