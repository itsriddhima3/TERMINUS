local walk = require("graph-src.walk")

local M = {}

function M.enumerate_labels(sketch_path)
  local g = walk.parse_sketch(sketch_path)
  local nodes = {}
  local edges = {}
  for nid in pairs(g.nodes) do
    table.insert(nodes, nid)
  end
  table.sort(nodes)
  for _, e in ipairs(g.edges) do
    table.insert(edges, e.from .. "->" .. e.to .. ":" .. e.family)
  end
  table.sort(edges)
  return nodes, edges
end

return M
