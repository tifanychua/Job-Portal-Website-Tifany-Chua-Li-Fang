Feature: View Employer Conversation List


Scenario: View conversation list

Given the employer is logged in and has existing conversations with job seekers
When the employer opens the Messages page
Then the system should display the list of conversations with job seekers



Scenario: Display latest conversation information

Given the employer is viewing the conversation list
When the conversations are loaded
Then the system should display the latest message and conversation details



Scenario: No conversations available

Given the employer has no conversations with job seekers
When the employer opens the Messages page
Then the system should display a "No conversations available" message