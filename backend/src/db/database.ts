import fs from 'node:fs';
import path from 'node:path';
import Database from 'better-sqlite3';
import { env } from '../config/env';

const dataDir = path.dirname(env.DATABASE_PATH);
fs.mkdirSync(dataDir, { recursive: true });

export const db = new Database(env.DATABASE_PATH);
db.pragma('journal_mode = WAL');

db.exec(`
  CREATE TABLE IF NOT EXISTS transfer_tasks (
    id TEXT PRIMARY KEY,
    keyword TEXT NOT NULL,
    provider TEXT NOT NULL,
    resource_title TEXT NOT NULL,
    resource_payload TEXT NOT NULL,
    status TEXT NOT NULL,
    transfer_status TEXT NOT NULL,
    strm_status TEXT NOT NULL,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    driver TEXT NOT NULL,
    result_count INTEGER NOT NULL,
    created_at TEXT NOT NULL
  );
`);
