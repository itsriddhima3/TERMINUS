-- observability counter bump (decoy)
local lane = KEYS[1]
local delta = tonumber(ARGV[1]) or 1
return redis.call('INCRBY', lane, delta)
