# frozen_string_literal: true

require_relative "../app/controllers/ratings_controller"

def build_app
  ctrl = RatingsController.new
  proc do |env|
    case [env["REQUEST_METHOD"], env["PATH_INFO"]]
    when ["GET", "/api/v1/split"]
      ctrl.split(env)
    when ["GET", "/api/v1/train_ratings"]
      ctrl.train_ratings(env)
    when ["GET", "/api/v1/holdout"]
      ctrl.holdout(env)
    when ["POST", "/api/v1/predictions"]
      ctrl.predictions(env)
    else
      [404, { "Content-Type" => "application/json" }, ['{"error":"not found"}']]
    end
  end
end
