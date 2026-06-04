# frozen_string_literal: true

require "json"
require "rack"
require_relative "../models/rating_store"

class RatingsController
  def initialize
    @store = RatingStore.new
  end

  def split(_env)
    body = @store.split_meta.merge(schema_version: 1)
    [200, { "Content-Type" => "application/json" }, [JSON.generate(body)]]
  end
  def train_ratings(env)
    qs = Rack::Utils.parse_query(env["QUERY_STRING"])
    page = qs.fetch("page", "1")
    per = qs.fetch("per_page", @store.split_meta[:per_page].to_s)
    payload = @store.train_page(page, per)
    [200, { "Content-Type" => "application/json" }, [JSON.generate(payload)]]
  end

  def holdout(_env)
    pairs = @store.holdout_pairs
    body = { schema_version: 1, pairs: pairs }
    [200, { "Content-Type" => "application/json" }, [JSON.generate(body)]]
  end

  def predictions(env)
    raw = env["rack.input"].read
    doc = JSON.parse(raw)
    split_id = doc["split_id"]
    preds = doc.fetch("predictions", doc["items"])
    result = @store.score_predictions(preds, split_id)
    body = result.merge(schema_version: 1)
    [200, { "Content-Type" => "application/json" }, [JSON.generate(body)]]
  end
end
