local util = require("lib.util")

local M = {}

local function credential_node_for_row(g, row_id)
  local node = g.nodes[row_id]
  if not node then
    return row_id
  end
  if node.cert and node.cert ~= "" then
    return row_id
  end
  if node.row ~= "true" and node.row ~= "1" then
    return row_id
  end
  for _, e in ipairs(g.edges or {}) do
    if e.family == "serves" and e.from == row_id then
      return e.to
    end
  end
  return row_id
end

function M.resolve_cert_paths(g, pack_root, row_id)
  local cred_id = credential_node_for_row(g, row_id)
  local node = g.nodes[cred_id]
  if not node or not node.cert then
    return nil, nil, nil, {}
  end
  local leaf = util.join(pack_root, node.cert)
  local anchor_id = "anchor"
  for nid, n in pairs(g.nodes) do
    if n.role == "anchor" then
      anchor_id = nid
    end
  end
  local anchor_node = g.nodes[anchor_id]
  local anchor_path = anchor_node and util.join(pack_root, anchor_node.cert) or nil
  local store_path = ""
  local path_ids = {}
  local cur = cred_id
  local seen = {}
  while cur and not seen[cur] do
    seen[cur] = true
    table.insert(path_ids, 1, cur)
    local parent = nil
    for _, e in ipairs(g.edges or {}) do
      if e.family == "trusts" and e.from == cur then
        parent = e.to
        break
      end
    end
    cur = parent
  end
  if row_id ~= cred_id then
    table.insert(path_ids, 1, row_id)
  end
  if #path_ids >= 2 then
    local inter_id = path_ids[#path_ids - 1]
    local inter = g.nodes[inter_id]
    if inter and inter.cert then
      store_path = util.join(pack_root, inter.cert)
    end
  end
  return leaf, store_path, anchor_path, path_ids
end

function M.service_rows(g)
  local rows = {}
  for nid, node in pairs(g.nodes) do
    if node.row == "true" or node.row == "1" then
      table.insert(rows, nid)
    end
  end
  table.sort(rows)
  return rows
end

return M
