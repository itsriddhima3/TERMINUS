#!/usr/bin/env lua5.4
package.path = "/app/?.lua;/app/?/init.lua;" .. package.path
require("openssl-src.bridge")
require("policy-src.gate")
if not arg[1] or arg[1] == "" then
  arg[1] = "delta"
end
dofile("/app/flow-src/run_pack.lua")
