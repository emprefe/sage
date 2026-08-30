PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS vendors (
  id INTEGER PRIMARY KEY,
  vendor_key TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  documentation_url TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','retired','test')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS participants (
  id INTEGER PRIMARY KEY,
  participant_id TEXT NOT NULL UNIQUE CHECK (length(participant_id) BETWEEN 1 AND 64),
  display_name TEXT NOT NULL,
  documentation_url TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','retired','test')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS vendor_participants (
  vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
  participant_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
  PRIMARY KEY (vendor_id, participant_id)
);
