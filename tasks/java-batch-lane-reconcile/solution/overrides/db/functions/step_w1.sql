CREATE OR REPLACE FUNCTION step_w1()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  hdr TEXT;
  delta BIGINT := 0;
BEGIN
  IF TG_OP = 'DELETE' THEN
    SELECT h.partition_label INTO hdr FROM header_slice h WHERE h.id = OLD.header_id;
    delta := -OLD.qty;
    PERFORM 1 FROM header_slice WHERE id = OLD.header_id FOR UPDATE;
    PERFORM 1 FROM line_slice WHERE header_id = OLD.header_id FOR UPDATE;
  ELSIF TG_OP = 'UPDATE' THEN
    SELECT h.partition_label INTO hdr FROM header_slice h WHERE h.id = NEW.header_id;
    delta := NEW.qty - OLD.qty;
    PERFORM 1 FROM header_slice WHERE id = NEW.header_id FOR UPDATE;
    PERFORM 1 FROM line_slice WHERE id = NEW.id FOR UPDATE;
  ELSE
    SELECT h.partition_label INTO hdr FROM header_slice h WHERE h.id = NEW.header_id;
    delta := NEW.qty;
    PERFORM 1 FROM header_slice WHERE id = NEW.header_id FOR UPDATE;
    PERFORM 1 FROM line_slice WHERE id = NEW.id FOR UPDATE;
  END IF;
  UPDATE partition_dim SET rollup_qty = rollup_qty + delta WHERE label = hdr;
  RETURN COALESCE(NEW, OLD);
END;
$$;
