# frozen_string_literal: true

require "sqlite3"
require "json"

class RatingStore
  DB_PATH = File.expand_path("../../db/ratings.db", __dir__)

  def initialize
    @db = SQLite3::Database.new(DB_PATH)
    @db.results_as_hash = true
  end

  def split_meta
    row = @db.get_first_row("SELECT * FROM split_meta LIMIT 1")
    raise "split_meta missing" unless row

    {
      split_id: row["split_id"],
      n_users: row["n_users"],
      n_items: row["n_items"],
      n_train: row["n_train"],
      n_holdout: row["n_holdout"],
      rmse_threshold: row["rmse_threshold"],
      per_page: row["per_page"],
      fit_seed: row["fit_seed"],
      n_factors: row["n_factors"],
      fit_epochs: row["fit_epochs"],
      lr_base: row["lr_base"],
      lr_decay: row["lr_decay"],
    }
  end

  def train_page(page, per_page)
    page = [page.to_i, 1].max
    per_page = [per_page.to_i, 1].max
    meta = split_meta
    total_pages = (meta[:n_train].to_f / per_page).ceil
    offset = (page - 1) * per_page
    rows = @db.execute(
      "SELECT user_id, item_id, score FROM ratings WHERE is_holdout = 0 " \
      "ORDER BY user_id, item_id LIMIT ? OFFSET ?",
      [per_page, offset],
    ).map { |r| { user_id: r["user_id"], item_id: r["item_id"], score: r["score"] } }
    { ratings: rows, page: page, per_page: per_page, total_pages: total_pages }
  end

  def holdout_pairs
    @db.execute(
      "SELECT user_id, item_id FROM ratings WHERE is_holdout = 1 ORDER BY user_id, item_id",
    ).map { |r| { user_id: r["user_id"], item_id: r["item_id"] } }
  end

  def score_predictions(preds, split_id)
    meta = split_meta
    unless split_id == meta[:split_id]
      return { rmse: 99.0, accepted: false, n_scored: 0, schema_version: 1 }
    end

    truth = {}
    @db.execute("SELECT user_id, item_id, score FROM holdout_truth").each do |r|
      truth[[r["user_id"], r["item_id"]]] = r["score"]
    end
    se = 0.0
    n = 0
    preds.each do |p|
      key = [p["user_id"], p["item_id"]]
      next unless truth.key?(key)

      diff = p["score"].to_f - truth[key]
      se += diff * diff
      n += 1
    end
    rmse = n.positive? ? Math.sqrt(se / n) : 99.0
    accepted = rmse <= meta[:rmse_threshold]
    { rmse: rmse.round(6), accepted: accepted, n_scored: n }
  end
end
