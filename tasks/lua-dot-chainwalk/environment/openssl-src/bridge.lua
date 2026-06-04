local util = require("lib.util")

local M = {}

local function fingerprint_hex(pem_path, digest_mode)
  digest_mode = digest_mode or "sha1"
  local cmd = string.format(
    'openssl x509 -in %s -noout -fingerprint -%s',
    pem_path,
    digest_mode
  )
  local raw = util.shell(cmd)
  local hex = raw:match("Fingerprint=(.+)")
  if not hex then
    return "", false
  end
  hex = hex:gsub(":", ""):lower()
  return hex, true
end

function M.reconcile_b(leaf_path, store_path, anchor_path, digest_mode)
  digest_mode = digest_mode or "sha1"
  local chain_ok = true
  local cmd
  if store_path and store_path ~= "" and util.file_exists(store_path) then
    cmd = string.format(
      "openssl verify -CAfile %s -untrusted %s %s",
      store_path,
      anchor_path,
      leaf_path
    )
  else
    cmd = string.format("openssl verify -CAfile %s %s", anchor_path, leaf_path)
  end
  local out = util.shell(cmd)
  if not out:match(": OK") then
    chain_ok = false
  end
  local identity_hex, ok = fingerprint_hex(leaf_path, digest_mode)
  if not ok then
    identity_hex = ""
    chain_ok = false
  end
  return identity_hex, chain_ok
end

return M
