local util = require("lib.util")

local M = {}

function M.load_tz_base()
  local path = "/app/config/runtime.env"
  for _, line in ipairs(util.read_lines(path)) do
    local key, val = line:match("^([%w_]+)=(.+)$")
    if key == "TZ_BASE" then
      return val
    end
  end
  return "UTC"
end

return M
