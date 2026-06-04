const fs = require("fs");

function allowDiskEnabled() {
  const policy = JSON.parse(
    fs.readFileSync("/app/config/invoke_policy.json", "utf8")
  );
  const invokeSrc = fs.readFileSync("/app/r7/h3v_invoke.js", "utf8");
  return (
    policy.spine_defaults.allow_disk_use === true ||
    /allowDiskUse\s*:\s*true/.test(invokeSrc)
  );
}

module.exports = { allowDiskEnabled };
