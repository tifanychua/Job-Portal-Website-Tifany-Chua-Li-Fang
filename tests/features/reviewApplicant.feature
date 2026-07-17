Feature: Review Applicant

    Scenario: Employer marks an application as Reviewed
        Given the employer has received job applications
        When the employer marks an application as Reviewed
        Then the application status should be updated to "Reviewed"

    Scenario: Save reviewed application status
        Given the employer has marked an application as Reviewed
        When the update process is completed
        Then the updated application status should be saved in the database