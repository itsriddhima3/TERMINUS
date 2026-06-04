local M = {}

function M.phase_c(walk_ok, chain_ok, ledger_hits, window_row, severed_flag)
  local route_state = "held"
  local window_state = window_row.state or "live"
  local handoff_ok = false
  local pack_rc = 0

  if ledger_hits and ledger_hits > 0 then
    route_state = "blocked"
    handoff_ok = false
  elseif not walk_ok or not chain_ok then
    route_state = "held"
    handoff_ok = false
  elseif window_state == "preopen" or window_state == "expired" then
    route_state = "held"
    handoff_ok = false
  else
    route_state = "cleared"
    handoff_ok = true
  end

  if severed_flag then
    pack_rc = 1
    handoff_ok = false
    route_state = "held"
  elseif not handoff_ok then
    pack_rc = 1
  end

  return route_state, window_state, handoff_ok, pack_rc
end

function M.window_from_pem(pem_path, tz_base)
  local util = require("lib.util")
  tz_base = tz_base or "UTC"
  local raw = util.shell(string.format("openssl x509 -in %s -noout -dates", pem_path))
  local nb = raw:match("notBefore=([^\n]+)")
  local na = raw:match("notAfter=([^\n]+)")
  local function epoch_gmt(dt)
    if not dt then
      return nil
    end
    local clean = dt:gsub(" GMT", "")
    local out = util.shell(string.format("date -u -d %q +%%s", clean))
    return tonumber(out)
  end
  local now_s = tonumber(util.shell(string.format("TZ=%s date +%%s", tz_base)))
  local nb_s = epoch_gmt(nb)
  local na_s = epoch_gmt(na)
  if na_s and now_s and now_s > na_s then
    return { state = "expired" }
  end
  if nb_s and now_s and now_s < nb_s then
    return { state = "preopen" }
  end
  return { state = "live" }
end

return M
