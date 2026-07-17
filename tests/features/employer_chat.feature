Feature: Employer Chat with Job Seeker
As an Employer
I want to chat with job seekers through the platform
So that I can provide interview instructions, answer questions, and communicate throughout the hiring process.



Scenario: Employer sends a message to job seeker
    Given the employer has opened a chat conversation with a job seeker
    When the employer enters and sends a message
    Then the message should appear in the chat conversation


Scenario: Employer receives job seeker messages
    Given the job seeker has sent a message
    When the employer opens the chat conversation
    Then the job seeker's message should be displayed