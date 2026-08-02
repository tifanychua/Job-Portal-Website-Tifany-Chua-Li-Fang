Feature: Approve Company Registration Requests

    As an Admin
    I want to approve company registration requests
    So that verified companies can access employer features.


    Scenario: View pending company registration requests
        Given there are pending company registration requests
        When the admin opens the company registration management page
        Then the system should display the list of pending registration requests


    Scenario: Approve a valid company registration request
        Given the admin is reviewing a pending company registration request
        When the admin approves the company registration
        Then the system should update the company status to "Active"
        And allow the company to access employer features
