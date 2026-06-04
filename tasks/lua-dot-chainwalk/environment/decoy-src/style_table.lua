local M = {}

M.bands = {
  critical = "#8b0000",
  warning = "#ff8c00",
  notice = "#4682b4",
  info = "#708090",
}

function M.band_for_score(score)
  if score >= 90 then
    return "critical", M.bands.critical
  elseif score >= 70 then
    return "warning", M.bands.warning
  elseif score >= 40 then
    return "notice", M.bands.notice
  end
  return "info", M.bands.info
end

return M
