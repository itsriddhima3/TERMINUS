#!/usr/bin/env lua5.4
package.path = "/app/?.lua;/app/?/init.lua;" .. package.path
require("policy-src.gate")
require("pem-src.load")
if not arg[1] or arg[1] == "" then
  arg[1] = "zeta"
end
dofile("/app/flow-src/run_pack.lua")
