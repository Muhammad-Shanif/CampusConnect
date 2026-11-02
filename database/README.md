# Database setup

MySQL 8.0 database: `campusconnect`. Execute schema files in numeric order, then load `seeds/seed_data.sql`. The database contains seven core tables: `students`, `clubs`, `club_memberships`, `venues`, `events`, `event_registrations`, and `event_feedback`.

The associative tables `club_memberships` and `event_registrations` resolve the two many-to-many relationships in the ER diagram: students↔clubs and students↔events. Foreign keys enforce referential integrity; unique keys prevent duplicate membership, registration and feedback pairs. The database layer also contains triggers for event/registration/feedback validation, stored procedures for multi-step business operations, reporting views, and a scheduled event for event status synchronization.
