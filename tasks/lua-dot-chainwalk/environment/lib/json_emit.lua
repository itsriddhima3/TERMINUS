local util = require("lib.util")

local M = {}

local function escape_str(s)
  return '"' .. s:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n') .. '"'
end

local function emit_value(v, indent)
  indent = indent or 0
  local pad = string.rep("  ", indent)
  local t = type(v)
  if t == "nil" then
    return "null"
  elseif t == "boolean" then
    return v and "true" or "false"
  elseif t == "number" then
    return tostring(v)
  elseif t == "string" then
    return escape_str(v)
  elseif t == "table" then
    if next(v) == nil then
      return "[]"
    end
    if #v > 0 and v[1] ~= nil then
      local parts = {}
      for i = 1, #v do
        table.insert(parts, pad .. "  " .. emit_value(v[i], indent + 1))
      end
      return "[\n" .. table.concat(parts, ",\n") .. "\n" .. pad .. "]"
    end
    local keys = util.sorted_keys(v)
    local parts = {}
    for _, k in ipairs(keys) do
      table.insert(
        parts,
        pad .. "  " .. escape_str(k) .. ": " .. emit_value(v[k], indent + 1)
      )
    end
    return "{\n" .. table.concat(parts, ",\n") .. "\n" .. pad .. "}"
  end
  return "null"
end

function M.encode(tbl)
  return emit_value(tbl, 0)
end

function M.write_file(path, tbl)
  util.write_text(path, emit_value(tbl, 0) .. "\n")
end

return M
