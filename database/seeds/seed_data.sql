USE campusconnect;
SET @cc_seed_mode=1;
INSERT IGNORE INTO students(student_id,name,email,phone,department,year_of_study,enrollment_date) VALUES
(1,'Aarav Sharma','aarav.sharma@uvce.edu.in','9876500001','Information Science',3,'2024-08-01'),
(2,'Diya Rao','diya.rao@uvce.edu.in','9876500002','Computer Science',2,'2025-08-01'),
(3,'Ishaan Nair','ishaan.nair@uvce.edu.in','9876500003','Electronics',3,'2024-08-01'),
(4,'Meera Kulkarni','meera.k@uvce.edu.in','9876500004','Information Science',2,'2025-08-01'),
(5,'Kabir Shetty','kabir.s@uvce.edu.in','9876500005','Mechanical',4,'2023-08-01');
INSERT IGNORE INTO clubs(club_id,club_name,description,category,date_founded,status) VALUES
(1,'MARVEL','A student-led technology and innovation club.','TECHNICAL','2012-08-15','ACTIVE'),
(2,'Aikya','Arts, culture and campus events.','CULTURAL','2015-01-10','ACTIVE'),
(3,'CodeChef UVCE','Competitive programming community.','TECHNICAL','2018-06-01','ACTIVE'),
(4,'Prathibha','Literary and debate society.','LITERARY','2014-09-01','ACTIVE');
INSERT IGNORE INTO venues(venue_id,venue_name,building,room_number,capacity,venue_type) VALUES
(1,'Dr. Ambedkar Auditorium','Main Block','AUD-01',500,'AUDITORIUM'),
(2,'ISE Seminar Hall','ISE Block','SH-02',120,'SEMINAR_HALL'),
(3,'Innovation Lab','Innovation Centre','LAB-01',60,'LAB'),
(4,'Quadrangle','Central Campus','OPEN',300,'OTHER');
INSERT IGNORE INTO club_memberships(membership_id,student_id,club_id,membership_role,membership_status,joined_at) VALUES
(1,1,1,'PRESIDENT','ACTIVE','2025-08-10'),(2,2,1,'MEMBER','ACTIVE','2025-08-11'),(3,3,2,'SECRETARY','ACTIVE','2025-08-12'),(4,4,3,'PRESIDENT','ACTIVE','2025-08-13'),(5,5,1,'MEMBER','ACTIVE','2025-08-14'),(6,2,4,'MEMBER','ACTIVE','2025-08-15');
INSERT IGNORE INTO events(event_id,club_id,venue_id,event_name,description,event_date,start_time,end_time,capacity,registration_deadline,event_status) VALUES
(1,1,2,'Build with AI','A hands-on introduction to applied AI and prototyping.','2026-11-20','10:00:00','13:00:00',100,'2026-11-19 23:59:00','UPCOMING'),
(2,3,3,'CodeSprint','A fast-paced competitive programming contest.','2026-11-24','14:00:00','17:00:00',50,'2026-11-23 23:59:00','UPCOMING'),
(3,2,1,'Samskruthi','An evening celebrating campus culture.','2026-12-02','16:00:00','20:00:00',400,'2026-12-01 23:59:00','UPCOMING');
INSERT IGNORE INTO event_registrations(registration_id,student_id,event_id,registration_status,attendance_status) VALUES
(1,1,1,'REGISTERED','PENDING'),(2,2,1,'REGISTERED','PENDING'),(3,3,1,'REGISTERED','PENDING'),(4,4,2,'REGISTERED','PENDING'),(5,5,2,'REGISTERED','PENDING');
SET @cc_seed_mode=0;
