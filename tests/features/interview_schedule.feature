Feature: Schedule Interview
As an Employer
I want to schedule interviews with shortlisted job seekers
So that I can evaluate their qualifications and determine their suitability for the job position.



Scenario: Employer schedules an interview
Given the employer has shortlisted a job seeker
When the employer enters the interview stage, date, time, duration, interview type, and interviewer details and submits the interview schedule
Then the interview should be created successfully

Scenario: Save interview schedule details
Given the employer has scheduled an interview
When the system processes the schedule
Then the interview details should be saved in the database

Scenario: Employer schedules an online interview
Given the employer has selected an online interview type
When the employer enters a valid meeting link and submits the interview schedule
Then the online interview details should be saved successfully

Scenario: Employer schedules a physical interview
Given the employer has selected a physical interview type
When the employer enters the interview location and submits the interview schedule
Then the physical interview details should be saved successfully

Scenario: Employer submits incomplete interview details
Given the employer is creating an interview schedule
When the employer leaves required interview details empty and submits the interview schedule
Then the system should display a validation message and the interview should not be created