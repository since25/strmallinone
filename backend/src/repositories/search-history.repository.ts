import { db } from '../db/database';

const insertStmt = db.prepare(`
  INSERT INTO search_history (keyword, driver, result_count, created_at)
  VALUES (@keyword, @driver, @resultCount, @createdAt)
`);

export class SearchHistoryRepository {
  create(input: { keyword: string; driver: string; resultCount: number }): void {
    insertStmt.run({
      ...input,
      createdAt: new Date().toISOString(),
    });
  }
}
