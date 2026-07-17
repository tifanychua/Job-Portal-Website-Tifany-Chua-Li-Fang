Feature: Job Seeker Chat with Employer
As a Job Seeker
I want to chat with employers through the platform
So that I can ask questions, clarify job details, and communicate about the recruitment process securely.

Scenario: Job seeker sends a message to employer
    Given the job seeker has opened a chat conversation with an employer
    When the job seeker enters and sends a message
    Then the message should appear in the chat conversation

Scenario: Job seeker receives employer messages
    Given the employer has sent a message
    When the job seeker opens the chat conversation
    Then the employer's message should be displayed