USE campusconnect;
DELIMITER $$
CREATE PROCEDURE sp_join_club(IN p_student INT UNSIGNED, IN p_club INT UNSIGNED)
BEGIN
 INSERT INTO club_memberships(student_id,club_id,membership_role,membership_status) VALUES(p_student,p_club,'MEMBER','ACTIVE')
 ON DUPLICATE KEY UPDATE membership_status='ACTIVE', joined_at=CURDATE();
 SELECT * FROM club_memberships WHERE student_id=p_student AND club_id=p_club;
END$$
CREATE PROCEDURE sp_leave_club(IN p_membership INT UNSIGNED)
BEGIN
 IF NOT EXISTS(SELECT 1 FROM club_memberships WHERE membership_id=p_membership) THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51001, MESSAGE_TEXT='Membership not found'; END IF;
 UPDATE club_memberships SET membership_status='LEFT', membership_role='MEMBER' WHERE membership_id=p_membership;
 SELECT * FROM club_memberships WHERE membership_id=p_membership;
END$$
CREATE PROCEDURE sp_assign_officer(IN p_club INT UNSIGNED, IN p_student INT UNSIGNED, IN p_role VARCHAR(30))
BEGIN
 IF p_role NOT IN ('PRESIDENT','VICE_PRESIDENT','SECRETARY','TREASURER') THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51003, MESSAGE_TEXT='Invalid officer role'; END IF;
 IF NOT EXISTS(SELECT 1 FROM club_memberships WHERE club_id=p_club AND student_id=p_student AND membership_status='ACTIVE') THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51003, MESSAGE_TEXT='Student must be an active member'; END IF;
 UPDATE club_memberships SET membership_role='MEMBER' WHERE club_id=p_club AND membership_role=p_role;
 UPDATE club_memberships SET membership_role=p_role WHERE club_id=p_club AND student_id=p_student;
 SELECT cm.membership_id,s.student_id,s.name,cm.membership_role FROM club_memberships cm JOIN students s USING(student_id) WHERE cm.club_id=p_club AND cm.membership_role<>'MEMBER';
END$$
CREATE PROCEDURE sp_register_for_event(IN p_student INT UNSIGNED, IN p_event INT UNSIGNED)
BEGIN
 DECLARE v_capacity INT; DECLARE v_count INT; DECLARE v_status VARCHAR(20);
 SELECT capacity INTO v_capacity FROM events WHERE event_id=p_event FOR UPDATE;
 SELECT COUNT(*) INTO v_count FROM event_registrations WHERE event_id=p_event AND registration_status='REGISTERED';
 SET v_status=IF(v_count < v_capacity,'REGISTERED','WAITLISTED');
 INSERT INTO event_registrations(student_id,event_id,registration_status) VALUES(p_student,p_event,v_status)
 ON DUPLICATE KEY UPDATE registration_status=VALUES(registration_status), attendance_status='PENDING', registered_at=CURRENT_TIMESTAMP;
 SELECT * FROM event_registrations WHERE student_id=p_student AND event_id=p_event;
END$$
CREATE PROCEDURE sp_cancel_registration(IN p_registration INT UNSIGNED)
BEGIN
 DECLARE v_event INT UNSIGNED; DECLARE v_next INT UNSIGNED;
 IF NOT EXISTS(SELECT 1 FROM event_registrations WHERE registration_id=p_registration) THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51001, MESSAGE_TEXT='Registration not found'; END IF;
 SELECT event_id INTO v_event FROM event_registrations WHERE registration_id=p_registration;
 UPDATE event_registrations SET registration_status='CANCELLED' WHERE registration_id=p_registration;
 SELECT registration_id INTO v_next FROM event_registrations WHERE event_id=v_event AND registration_status='WAITLISTED' ORDER BY registered_at,registration_id LIMIT 1;
 IF v_next IS NOT NULL THEN UPDATE event_registrations SET registration_status='REGISTERED' WHERE registration_id=v_next; END IF;
 SELECT r.*, (SELECT student_id FROM event_registrations WHERE registration_id=v_next) AS promoted_student_id FROM event_registrations r WHERE r.registration_id=p_registration;
END$$
CREATE PROCEDURE sp_mark_attendance(IN p_registration INT UNSIGNED, IN p_attendance VARCHAR(20))
BEGIN
 IF NOT EXISTS(SELECT 1 FROM event_registrations WHERE registration_id=p_registration) THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51001, MESSAGE_TEXT='Registration not found'; END IF;
 IF p_attendance NOT IN ('PENDING','PRESENT','ABSENT') THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51003, MESSAGE_TEXT='Invalid attendance status'; END IF;
 UPDATE event_registrations SET attendance_status=p_attendance WHERE registration_id=p_registration AND registration_status='REGISTERED';
 SELECT * FROM event_registrations WHERE registration_id=p_registration;
END$$
CREATE PROCEDURE sp_complete_event(IN p_event INT UNSIGNED)
BEGIN
 IF NOT EXISTS(SELECT 1 FROM events WHERE event_id=p_event) THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51001, MESSAGE_TEXT='Event not found'; END IF;
 UPDATE event_registrations SET attendance_status='ABSENT' WHERE event_id=p_event AND registration_status='REGISTERED' AND attendance_status='PENDING';
 UPDATE events SET event_status='COMPLETED' WHERE event_id=p_event;
 SELECT event_id,event_status FROM events WHERE event_id=p_event;
END$$
CREATE PROCEDURE sp_cancel_event(IN p_event INT UNSIGNED)
BEGIN
 IF NOT EXISTS(SELECT 1 FROM events WHERE event_id=p_event) THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51001, MESSAGE_TEXT='Event not found'; END IF;
 UPDATE events SET event_status='CANCELLED' WHERE event_id=p_event;
 UPDATE event_registrations SET registration_status='CANCELLED' WHERE event_id=p_event AND registration_status IN ('REGISTERED','WAITLISTED');
 SELECT event_id,event_status FROM events WHERE event_id=p_event;
END$$
CREATE PROCEDURE sp_event_summary(IN p_event INT UNSIGNED)
BEGIN
 SELECT e.event_id,e.event_name,e.capacity,COUNT(CASE WHEN r.registration_status='REGISTERED' THEN 1 END) AS registered_count,
 COUNT(CASE WHEN r.registration_status='WAITLISTED' THEN 1 END) AS waitlisted_count,
 COUNT(CASE WHEN r.attendance_status='PRESENT' THEN 1 END) AS present_count,
 ROUND(100*COUNT(CASE WHEN r.attendance_status='PRESENT' THEN 1 END)/NULLIF(COUNT(CASE WHEN r.registration_status='REGISTERED' THEN 1 END),0),2) AS attendance_percentage
 FROM events e LEFT JOIN event_registrations r USING(event_id) WHERE e.event_id=p_event GROUP BY e.event_id;
END$$
CREATE PROCEDURE sp_submit_feedback(IN p_student INT UNSIGNED, IN p_event INT UNSIGNED, IN p_rating TINYINT UNSIGNED, IN p_comments TEXT)
BEGIN
 INSERT INTO event_feedback(student_id,event_id,rating,comments) VALUES(p_student,p_event,p_rating,p_comments)
 ON DUPLICATE KEY UPDATE rating=VALUES(rating),comments=VALUES(comments),submitted_at=CURRENT_TIMESTAMP;
 SELECT * FROM event_feedback WHERE student_id=p_student AND event_id=p_event;
END$$
DELIMITER ;
