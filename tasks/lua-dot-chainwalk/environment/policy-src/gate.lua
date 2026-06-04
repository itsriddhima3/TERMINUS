local M = {}

function M.phase_c(walk_ok, chain_ok, ledger_hits, window_row, severed_flag)
  local route_state = "held"
  local window_state = window_row.state or "live"
  local handoff_ok = walk_ok and chain_ok

  if walk_ok and chain_ok then
    route_state = "cleared"
    handoff_ok = true
  end

  if ledger_hits and ledger_hits > 0 then
    handoff_ok = false
  end

  if window_state == "preopen" or window_state == "expired" then
    handoff_ok = false
    if route_state == "cleared" then
      route_state = "held"
    end
  end

  local pack_rc = 0
  if severed_flag then
    pack_rc = 1
    handoff_ok = false
  end

  return route_state, window_state, handoff_ok, pack_rc
end

function M.window_from_pem(pem_path, tz_base)
  tz_base = tz_base or "UTC"
  local fh = io.popen(string.format('openssl x509 -in %s -noout -dates 2>/dev/null', pem_path))
  local raw = fh:read("*a") or ""
  fh:close()
  local nb = raw:match("notBefore=(.-)\n")
  local na = raw:match("notAfter=(.-)\n")
  local now_cmd = string.format('TZ=%s date -u +%%s', tz_base)
  local now_s = tonumber(io.popen(now_cmd):read("*a")) or os.time()
  local function parse_ossl(dt)
    if not dt then
      return nil
    end
    local mon_map = {
      Jan = 1, Feb = 2, Mar = 3, Apr = 4, May = 5, Jun = 6,
      Jul = 7, Aug = 8, Sep = 9, Oct = 10, Nov = 11, Dec = 12,
    }
    local mon, day, hh, mm, ss, yr = dt:match(
      "(%a+)%s+(%d+)%s+(%d+):(%d+):(%d+)%s+(%d+)%s+GMT"
    )
    if not mon then
      return nil
    end
    return os.time({
      year = tonumber(yr),
      month = mon_map[mon],
      day = tonumber(day),
      hour = tonumber(hh),
      min = tonumber(mm),
      sec = tonumber(ss),
    })
  end
  local nb_s = parse_ossl(nb)
  local na_s = parse_ossl(na)
  if na_s and now_s > na_s then
    return { state = "expired" }
  end
  return { state = "live" }
end

return M
