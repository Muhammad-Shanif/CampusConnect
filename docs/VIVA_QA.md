# CampusConnect — DBMS viva questions

1. **What problem does CampusConnect solve?** It centralises student club membership, event registration, venue allocation, attendance and feedback instead of using disconnected sheets.
2. **Why MySQL?** It is a relational DBMS with transactions, constraints, triggers, stored procedures, views and event scheduling.
3. **What is the primary key?** A minimal attribute set that uniquely identifies each row. Each core table has an integer auto-increment primary key.
4. **Why are club_memberships and event_registrations needed?** They resolve many-to-many relationships between students and clubs, and students and events.
5. **What is 1NF?** Every attribute contains an atomic value and there are no repeating groups.
6. **What is 2NF?** The relation is in 1NF and every non-key attribute depends on the whole candidate key.
7. **What is 3NF?** The relation is in 2NF and non-key attributes do not depend transitively on a candidate key.
8. **Why use foreign keys?** To enforce referential integrity and prevent orphan references.
9. **What is a trigger?** A stored program automatically invoked by an INSERT, UPDATE or DELETE event.
10. **What is a stored procedure?** A named SQL program that can accept parameters and execute a multi-step operation.
11. **What is a view?** A stored SELECT definition that presents a reusable logical result set.
12. **Why is waitlist promotion in a procedure?** MySQL does not allow a trigger to modify the same table currently being changed by that trigger; the procedure can perform the cancellation and promotion as a controlled operation.
13. **How is event capacity enforced?** The registration procedure counts active registrations and chooses REGISTERED or WAITLISTED; event capacity is also checked against venue capacity.
14. **How is duplicate registration prevented?** A unique key on `(student_id,event_id)` plus trigger/procedure validation.
15. **How is feedback eligibility enforced?** Feedback is accepted only for a student/event registration marked PRESENT.
16. **What is the purpose of indexes?** They speed up common filtering and join operations at the cost of storage and write overhead.
17. **What is the role of the backend?** It exposes REST endpoints and calls parameterized SQL queries/procedures; business integrity remains in MySQL.
18. **Why avoid an ORM here?** The project demonstrates direct SQL, stored procedures, triggers and relational database concepts clearly.
19. **What is a transaction?** A logical unit of work that follows ACID properties.
20. **What does ACID stand for?** Atomicity, Consistency, Isolation and Durability.
