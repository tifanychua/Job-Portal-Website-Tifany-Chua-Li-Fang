Feature: Cancel Scheduled Interview
As an Employer
I want to cancel a scheduled interview with a job seeker
So that I can remove interviews that are no longer needed or relevant.

Scenario: Employer cancels an interview
Given the employer has a scheduled interview
When the employer selects the cancel interview option
Then the interview status should be updated to "Cancelled"

Scenario: Save cancelled interview status
Given the employer has cancelled an interview
When the cancellation process is completed
Then the updated interview status should be saved in the database