Feature: Accept Applicant

    Scenario: Employer accepts an applicant
        Given the employer has received job applications
        When the employer selects an applicant to accept
        Then the applicant status should be updated to "Offered"

    Scenario: Save accepted applicant status
        Given the employer has accepted an applicant
        When the acceptance action is completed
        Then the updated applicant status should be saved in the database