Feature: Job Application Submission
As a Job Seeker
I want to submit job applications online
So that employers can review my qualifications through a secure application process.

Scenario: Job seeker submits a job application
    Given the job seeker is viewing a job posting
    When the job seeker submits an application
    Then the application should be successfully created


Scenario: Job seeker application information is saved
    Given the job seeker has submitted a job application
    When the application is processed
    Then the application details should be stored in the database