#!/usr/bin/env lua5.4
package.path = "/app/?.lua;/app/?/init.lua;" .. package.path
require("graph-src.walk")
if not arg[1] or arg[1] == "" then
  arg[1] = "epsilon"
end
dofile("/app/flow-src/run_pack.lua")
