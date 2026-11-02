USE campusconnect;
SET GLOBAL event_scheduler = ON;
DELIMITER $$
CREATE EVENT IF NOT EXISTS ev_sync_event_status ON SCHEDULE EVERY 1 MINUTE DO
BEGIN
 UPDATE events SET event_status='ONGOING' WHERE event_status='UPCOMING' AND event_date=CURDATE() AND CURRENT_TIME BETWEEN start_time AND end_time;
 UPDATE events SET event_status='COMPLETED' WHERE event_status='ONGOING' AND (event_date<CURDATE() OR (event_date=CURDATE() AND CURRENT_TIME>end_time));
END$$
DELIMITER ;
