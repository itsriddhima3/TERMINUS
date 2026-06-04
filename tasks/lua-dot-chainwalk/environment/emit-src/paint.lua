local util = require("lib.util")

local M = {}

local function style_token(row)
  if row.route_state == "blocked" or (row.ledger_hits or 0) > 0 then
    return "deny_fill"
  end
  if row.route_state == "cleared" then
    return "cleared_fill"
  end
  if row.window_state == "live" then
    return "live_fill"
  end
  return "live_fill"
end

function M.paint_sketch(src_path, dst_path, rows_by_id)
  local lines = util.read_lines(src_path)
  local out = {}
  for _, line in ipairs(lines) do
    local painted = false
    if not line:find("->") then
      local nid, attrs = line:match('([%w_]+)%s*%[(.-)%]')
      if nid and rows_by_id[nid] then
        local token = style_token(rows_by_id[nid])
        if attrs:match("fillcolor=") then
          attrs = attrs:gsub('fillcolor="[^"]*"', 'fillcolor="' .. token .. '"')
        else
          attrs = attrs .. ', fillcolor="' .. token .. '"'
        end
        table.insert(out, string.format("  %s [%s];", nid, attrs))
        painted = true
      end
    end
    if not painted then
      table.insert(out, line)
    end
  end
  util.write_text(dst_path, table.concat(out, "\n") .. "\n")
end

return M
