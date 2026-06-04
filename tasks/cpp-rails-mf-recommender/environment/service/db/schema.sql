PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS split_meta (
  split_id TEXT PRIMARY KEY,
  n_users INTEGER NOT NULL,
  n_items INTEGER NOT NULL,
  n_train INTEGER NOT NULL,
  n_holdout INTEGER NOT NULL,
  rmse_threshold REAL NOT NULL,
  per_page INTEGER NOT NULL,
  fit_seed INTEGER NOT NULL,
  n_factors INTEGER NOT NULL,
  fit_epochs INTEGER NOT NULL,
  lr_base REAL NOT NULL,
  lr_decay REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS ratings (
  user_id INTEGER NOT NULL,
  item_id INTEGER NOT NULL,
  score REAL NOT NULL,
  is_holdout INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, item_id)
);

CREATE TABLE IF NOT EXISTS holdout_truth (
  user_id INTEGER NOT NULL,
  item_id INTEGER NOT NULL,
  score REAL NOT NULL,
  PRIMARY KEY (user_id, item_id)
);
