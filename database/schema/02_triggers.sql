USE campusconnect;
DELIMITER $$
CREATE TRIGGER trg_event_validate_insert BEFORE INSERT ON events FOR EACH ROW
BEGIN
 DECLARE v_capacity INT;
 SELECT capacity INTO v_capacity FROM venues WHERE venue_id=NEW.venue_id;
 IF NEW.capacity > v_capacity THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51003, MESSAGE_TEXT='Event capacity exceeds venue capacity'; END IF;
 IF NEW.event_date < CURDATE() AND COALESCE(@cc_seed_mode,0) <> 1 THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51003, MESSAGE_TEXT='Event date must be today or later'; END IF;
 IF NOT EXISTS(SELECT 1 FROM clubs WHERE club_id=NEW.club_id AND status='ACTIVE') THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51003, MESSAGE_TEXT='Club must be active'; END IF;
END$$
CREATE TRIGGER trg_event_validate_update BEFORE UPDATE ON events FOR EACH ROW
BEGIN
 DECLARE v_capacity INT;
 SELECT capacity INTO v_capacity FROM venues WHERE venue_id=NEW.venue_id;
 IF NEW.capacity > v_capacity THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51003, MESSAGE_TEXT='Event capacity exceeds venue capacity'; END IF;
END$$
CREATE TRIGGER trg_registration_validate BEFORE INSERT ON event_registrations FOR EACH ROW
BEGIN
 DECLARE v_deadline DATETIME;
 SELECT registration_deadline INTO v_deadline FROM events WHERE event_id=NEW.event_id;
 IF NOW() > v_deadline THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51003, MESSAGE_TEXT='Registration deadline has passed'; END IF;
 IF EXISTS(SELECT 1 FROM event_registrations WHERE student_id=NEW.student_id AND event_id=NEW.event_id AND registration_status <> 'CANCELLED') THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51002, MESSAGE_TEXT='Student already registered'; END IF;
END$$
CREATE TRIGGER trg_feedback_validate BEFORE INSERT ON event_feedback FOR EACH ROW
BEGIN
 IF NOT EXISTS(SELECT 1 FROM event_registrations WHERE student_id=NEW.student_id AND event_id=NEW.event_id AND attendance_status='PRESENT') THEN SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO=51003, MESSAGE_TEXT='Only attendees can submit feedback'; END IF;
END$$
DELIMITER ;
