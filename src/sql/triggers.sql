CREATE OR REPLACE FUNCTION sync_datetime_human()
RETURNS TRIGGER AS $$
BEGIN
  NEW."startDateTimeHuman" = TO_TIMESTAMP(NEW."startDateTime");
  NEW."endDateTimeHuman"   = TO_TIMESTAMP(NEW."endDateTime");
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_sync_datetime_human
BEFORE INSERT OR UPDATE ON match_details
FOR EACH ROW
EXECUTE FUNCTION sync_datetime_human();