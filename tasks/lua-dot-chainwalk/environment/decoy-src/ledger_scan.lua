-- Layout metrics helper: scans deny edges for reporting only (not used in closure).
local M = {}

function M.scan_deny_sources(g)
  local out = {}
  for _, e in ipairs(g.edges or {}) do
    if e.family == "deny" then
      table.insert(out, e.from)
    end
  end
  return out
end

return M
