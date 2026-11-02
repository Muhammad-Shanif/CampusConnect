USE campusconnect;
-- Basic integrity smoke checks. Run after loading seed_data.sql.
SELECT 'students' AS check_name, COUNT(*) AS rows_found FROM students
UNION ALL SELECT 'clubs',COUNT(*) FROM clubs
UNION ALL SELECT 'venues',COUNT(*) FROM venues
UNION ALL SELECT 'events',COUNT(*) FROM events;
-- Expected: each seeded table above contains at least one row.
SELECT COUNT(*) AS orphan_memberships FROM club_memberships cm LEFT JOIN students s USING(student_id) LEFT JOIN clubs c USING(club_id) WHERE s.student_id IS NULL OR c.club_id IS NULL;
SELECT COUNT(*) AS orphan_registrations FROM event_registrations r LEFT JOIN students s USING(student_id) LEFT JOIN events e USING(event_id) WHERE s.student_id IS NULL OR e.event_id IS NULL;
