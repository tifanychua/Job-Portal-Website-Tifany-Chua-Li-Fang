Feature: Upload Resume
As a job seeker
I want to upload my resume 
So that employers can view my qualifications when I apply for jobs.

Scenario: Job seeker uploads a resume
    Given the job seeker is on the resume upload page
    When the job seeker selects and uploads a resume file
    Then the resume should be uploaded successfully

Scenario: Store uploaded resume information
    Given the job seeker has uploaded a resume
    When the upload process is completed
    Then the resume information should be saved in the database