## Stories

### Initial Trigger: Case created

```gherkin
Given: Traffic Officer issues a citation to a party
  And: Citation has a Court Date
  And: Citation is of an eligible case category
When: Citation submitted into Case Management System
Then: Case is created in Case Management System with reminders enrolled
```

### Other Events for cases in Case Management System

Events (Format: SMS)
- Initial SMS to party(ies)
- Party receiving SMS opts out
- Party receives SMS for 7/3/1 days before court date

Events (notification format agnostic)
- Court Date rescheduled

Events (Format: Email)
- Initial Email to party(ies)
- Party receiving Email opts out
