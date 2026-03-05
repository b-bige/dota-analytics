ALTER TABLE match_details 
ADD COLUMN "startDateTimeHuman" TIMESTAMP;

ALTER TABLE match_details 
ADD COLUMN "endDateTimeHuman" TIMESTAMP;

BEGIN;
UPDATE match_details SET "startDateTimeHuman" = TO_TIMESTAMP("startDateTime");
UPDATE match_details SET "endDateTimeHuman" = TO_TIMESTAMP("endDateTime");
ROLLBACK;
COMMIT;