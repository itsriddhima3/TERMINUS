-- read-only probe for metrics sidecar
local slot = KEYS[1]
return tonumber(redis.call('GET', slot) or '0')
