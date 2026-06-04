-- decoy commit body (registry entry m2p) — exercises DECRBY on cold paths only
local slot = KEYS[1]
local want = tonumber(ARGV[1])
if want == nil or want <= 0 then
  return 0
end
return redis.call('DECRBY', slot, want)
