local util = require("lib.util")

local M = {}

local function edges_for_family(g, family)
  local out = {}
  for _, e in ipairs(g.edges or {}) do
    if e.family == family then
      table.insert(out, e)
    end
  end
  return out
end

local function with_serves_as_trusts(g, edges)
  for _, e in ipairs(g.edges or {}) do
    if e.family == "serves" then
      local from_node = g.nodes[e.from]
      if from_node and (from_node.row == "true" or from_node.row == "1") then
        table.insert(edges, { from = e.from, to = e.to, family = "trusts" })
      end
    end
  end
  return edges
end

local function build_adj(edges)
  local adj = {}
  for _, e in ipairs(edges) do
    adj[e.from] = adj[e.from] or {}
    table.insert(adj[e.from], e.to)
  end
  return adj
end

function M.op_walk_a(g, start_id, anchor_id, edge_family)
  edge_family = edge_family or "issued_by"
  if g.severed == "true" then
    return false, {}
  end
  if start_id == anchor_id then
    return true, {}
  end
  local edges = edges_for_family(g, edge_family)
  if edge_family == "trusts" then
    edges = with_serves_as_trusts(g, edges)
  end
  local adj = build_adj(edges)
  local seen = {}
  local path = {}
  local function dfs(node)
    if seen[node] then
      return false
    end
    seen[node] = true
    table.insert(path, node)
    if node == anchor_id then
      return true
    end
    for _, nxt in ipairs(adj[node] or {}) do
      if dfs(nxt) then
        return true
      end
    end
    table.remove(path)
    return false
  end
  local ok = dfs(start_id)
  if ok then
    return true, path
  end
  return false, {}
end

function M.count_ledger_hits(g, row_id)
  local hits = 0
  for _, e in ipairs(g.edges or {}) do
    if e.family == "deny" and e.from == row_id then
      hits = hits + 1
    end
  end
  return hits
end

function M.parse_sketch(path)
  local lines = util.read_lines(path)
  local g = { nodes = {}, edges = {} }
  for _, line in ipairs(lines) do
    if line:match("severed%s*=%s*true") then
      g.severed = "true"
    end
    if not line:find("->") then
    local nid, attrs = line:match('([%w_]+)%s*%[(.-)%]')
    if nid and attrs then
      local node = { id = nid }
      for k, val in attrs:gmatch('(%w+)="([^"]*)"') do
        node[k] = val
      end
      for k, val in attrs:gmatch('(%w+)=([%w_.%-]+)') do
        if node[k] == nil then
          node[k] = val
        end
      end
      g.nodes[nid] = node
    end
    end
    local from, to, fam = line:match('([%w_]+)%s*%-%>%s*([%w_]+)%s*%[label="([^"]+)"%]')
    if from and to and fam then
      table.insert(g.edges, { from = from, to = to, family = fam })
    end
  end
  return g
end

return M
