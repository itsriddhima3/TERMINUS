#!/usr/bin/env lua5.4
package.path = "/app/?.lua;/app/?/init.lua;" .. package.path
require("graph-src.walk")
require("openssl-src.bridge")
if not arg[1] or arg[1] == "" then
  arg[1] = "gamma"
end
dofile("/app/flow-src/run_pack.lua")
