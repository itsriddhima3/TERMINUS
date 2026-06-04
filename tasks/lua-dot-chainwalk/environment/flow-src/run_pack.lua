#!/usr/bin/env lua5.4

package.path = "/app/?.lua;/app/?/init.lua;" .. package.path

local util = require("lib.util")
local json_emit = require("lib.json_emit")
local walk = require("graph-src.walk")
local bridge = require("openssl-src.bridge")
local gate = require("policy-src.gate")
local paint = require("emit-src.paint")
local pem = require("pem-src.load")

local pack_id = arg[1]
if not pack_id then
  io.stderr:write("usage: run_pack.lua <pack_id>\n")
  os.exit(2)
end

local pack_root = util.join("/app/cases", pack_id)
local sketch_path = util.join(pack_root, "layout.dot")
local g = walk.parse_sketch(sketch_path)
local anchor_id = "anchor"
for nid, node in pairs(g.nodes) do
  if node.role == "anchor" then
    anchor_id = nid
  end
end

local rows_out = {}
local rows_paint = {}
local pack_rc = 0
local severed = g.severed == "true"

for _, row_id in ipairs(pem.service_rows(g)) do
  local leaf, store, anchor_path, path_ids = pem.resolve_cert_paths(g, pack_root, row_id)
  local walk_ok, walk_path = walk.op_walk_a(g, row_id, anchor_id, nil)
  local ledger_hits = walk.count_ledger_hits(g, row_id)
  local identity_hex, chain_ok = bridge.reconcile_b(leaf, store, anchor_path, nil)
  local window_row = gate.window_from_pem(leaf, "America/Chicago")
  local route_state, window_state, handoff_ok, row_rc =
    gate.phase_c(walk_ok, chain_ok, ledger_hits, window_row, severed)
  if not handoff_ok and row_rc == 0 then
    row_rc = 1
  end
  pack_rc = row_rc
  if #walk_path > 0 then
    path_ids = walk_path
  elseif row_id == anchor_id then
    path_ids = {}
  end
  local row = {
    row_id = row_id,
    route_state = route_state,
    window_state = window_state,
    identity_hex = identity_hex,
    chain_ok = chain_ok,
    walk_ok = walk_ok,
    handoff_ok = handoff_ok,
    path_ids = path_ids,
    ledger_hits = ledger_hits,
  }
  table.insert(rows_out, row)
  rows_paint[row_id] = row
end

local marked_dir = "/app/output/marked"
os.execute("mkdir -p " .. marked_dir)
paint.paint_sketch(sketch_path, util.join(marked_dir, pack_id .. ".dot"), rows_paint)

local result_path = util.join("/app/output", ".pack_" .. pack_id .. ".json")
json_emit.write_file(result_path, {
  pack_id = pack_id,
  pack_rc = pack_rc,
  rows = rows_out,
})
os.exit(pack_rc)
