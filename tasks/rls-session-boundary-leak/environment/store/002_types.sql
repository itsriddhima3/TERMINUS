DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ledger_status') THEN
    CREATE TYPE ledger_status AS ENUM ('open', 'closed', 'pending');
  END IF;
END$$;
