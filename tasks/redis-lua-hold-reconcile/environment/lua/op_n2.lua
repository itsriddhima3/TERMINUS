local slot = KEYS[1]
local want = tonumber(ARGV[1])
local baseline = tonumber(ARGV[2])
if want == nil or want <= 0 then
  return 0
end
if baseline == nil then
  baseline = tonumber(redis.call('GET', slot) or '0')
end
if baseline < want then
  return 0
end
redis.call('SET', slot, baseline - want)
return want
