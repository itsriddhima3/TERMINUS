# Ratings service overview

Local Rack service listens on port 4567. Split metadata lives at `/api/v1/split`. Training rows paginate through `/api/v1/train_ratings`. Holdout pairs are listed at `/api/v1/holdout`. Batch scoring posts to `/api/v1/predictions`.

The C++ operator CLI is `/app/bin/ratectl`.
