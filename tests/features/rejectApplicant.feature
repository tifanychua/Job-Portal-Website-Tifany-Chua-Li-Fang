Feature: Reject Applicant

    Scenario: Employer rejects an applicant
        Given the employer has received job applications
        When the employer selects an applicant to reject
        Then the applicant status should be updated to "Rejected"

    Scenario: Save rejected applicant status
        Given the employer has rejected an applicant
        When the rejection action is completed
        Then the updated applicant status should be saved in the database