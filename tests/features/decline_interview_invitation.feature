Feature: Decline Interview Invitation
As a Job Seeker
I want to decline an interview invitation
So that I can inform the employer that I am unable to attend.

Scenario: Job seeker declines an interview invitation
Given the job seeker has received an interview invitation
When the job seeker declines the interview
Then the interview status should be updated to "Declined"

Scenario: Save declined interview status
Given the job seeker has declined the interview
When the system processes the request
Then the updated interview status should be saved in the database