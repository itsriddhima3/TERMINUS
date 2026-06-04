local M = {}

function M.trim(s)
  return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

function M.split_csv(line)
  local out = {}
  for part in string.gmatch(line, "[^,]+") do
    table.insert(out, M.trim(part))
  end
  return out
end

function M.read_lines(path)
  local fh = assert(io.open(path, "r"))
  local lines = {}
  for line in fh:lines() do
    table.insert(lines, line)
  end
  fh:close()
  return lines
end

function M.read_text(path)
  local fh = assert(io.open(path, "r"))
  local data = fh:read("*a")
  fh:close()
  return data
end

function M.write_text(path, data)
  local fh = assert(io.open(path, "w"))
  fh:write(data)
  fh:close()
end

function M.file_exists(path)
  local fh = io.open(path, "r")
  if fh then
    fh:close()
    return true
  end
  return false
end

function M.dirname(path)
  return path:match("^(.*)/[^/]+$") or "."
end

function M.basename(path)
  return path:match("([^/]+)$") or path
end

function M.join(a, b)
  if a:sub(-1) == "/" then
    return a .. b
  end
  return a .. "/" .. b
end

function M.sorted_keys(t)
  local keys = {}
  for k in pairs(t) do
    table.insert(keys, k)
  end
  table.sort(keys)
  return keys
end

function M.shell(cmd)
  local fh = io.popen(cmd .. " 2>/dev/null")
  local out = fh:read("*a") or ""
  fh:close()
  return M.trim(out)
end

function M.run_id()
  local seed = os.time()
  return string.format("%016x", seed % 0x10000000000000000)
end

return M
