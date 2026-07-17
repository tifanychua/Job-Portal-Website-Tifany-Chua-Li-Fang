Feature: Accept Interview

    As a Job Seeker
    I want to accept an interview invitation
    So that I can confirm my attendance to the employer.


    Scenario: Job seeker accepts an interview invitation
        Given the job seeker has received an interview invitation
        When the job seeker accepts the interview
        Then the interview status should be updated to "Accepted"


    Scenario: Save accepted interview status
        Given the job seeker has accepted an interview
        When the system processes the request
        Then the updated interview status should be saved in the database