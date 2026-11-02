# Database design explanation

## ER model to relations
- **STUDENTS** (`student_id` PK): student identity and academic details.
- **CLUBS** (`club_id` PK): club name, description, category, founding date and status.
- **CLUB_MEMBERSHIPS** (`membership_id` PK; `student_id`, `club_id` FKs): resolves the Student–Club M:N relationship and stores role, membership status and join date.
- **VENUES** (`venue_id` PK): room/building, capacity and venue type.
- **EVENTS** (`event_id` PK; `club_id`, `venue_id` FKs): an event belongs to one club and is assigned one venue.
- **EVENT_REGISTRATIONS** (`registration_id` PK; `student_id`, `event_id` FKs): resolves the Student–Event M:N relationship and stores registration and attendance state.
- **EVENT_FEEDBACK** (`feedback_id` PK; `student_id`, `event_id` FKs): one feedback record per student/event pair, with rating and comments.

## Normalization notes (3NF)
Each table represents one entity or associative relationship. Attributes are atomic (1NF). Non-key attributes depend on the whole candidate key: the associative tables use surrogate primary keys plus unique constraints on their natural pairs (2NF). Descriptive club, student and venue attributes are kept in their own relations rather than copied into event or membership rows, avoiding transitive dependencies (3NF). Derived reporting values such as member counts and attendance percentages are calculated in views rather than redundantly stored.

## Integrity and business logic
- PK/FK/UNIQUE/CHECK constraints enforce identity, relationship and domain rules.
- Triggers validate event capacity, club state, registration deadlines/duplicates and feedback eligibility.
- Stored procedures perform join/leave, officer assignment, event registration, waitlist promotion, attendance, event completion/cancellation and feedback submission.
- Views provide reusable dashboard and report queries.
