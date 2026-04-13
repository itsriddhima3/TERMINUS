#include "api/engine.hpp"
#include "reference_model.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp>

namespace {

void write_report(const std::filesystem::path& p, const nlohmann::json& j) {
  std::ofstream o(p);
  o << j.dump(2) << '\n';
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 3) {
    std::cerr << "usage: trace_driver <scenario.json> <report.json>\n";
    return 2;
  }

  std::ifstream scenario_in(argv[1]);
  if (!scenario_in) {
    return 2;
  }

  nlohmann::json scenario = nlohmann::json::parse(scenario_in);
  ts::Engine eng;
  eng.reset_for_test();

  nlohmann::json report;
  report["scenario_id"] = scenario.value("scenario_id", std::string("unknown"));
  report["aligned"] = true;
  report["first_mismatch_index"] = nullptr;
  report["first_mismatch_kind"] = "";
  report["expected"] = "";
  report["actual"] = "";

  const nlohmann::json& ops = scenario.at("ops");
  for (std::size_t i = 0; i < ops.size(); ++i) {
    const nlohmann::json& op = ops[i];
    const std::string name = op.at("op").get<std::string>();

    if (name == "put") {
      eng.put(op.at("key").get<std::string>(), op.at("value").get<std::string>());
    } else if (name == "obliterate") {
      eng.obliterate(op.at("key").get<std::string>());
    } else if (name == "flush") {
      eng.flush();
    } else if (name == "merge") {
      eng.merge();
    } else if (name == "open_pin") {
      eng.open_pin();
    } else if (name == "close_pin") {
      eng.close_pin();
    } else if (name == "crash_truncate_journal") {
      eng.crash_truncate_journal(static_cast<std::size_t>(op.at("keep_bytes").get<int>()));
    } else if (name == "restart") {
      eng.restart();
    } else if (name == "partial_layout_bump") {
      eng.partial_layout_bump(op.at("delta").get<int>());
    } else if (name == "get") {
      ts::ReferenceFromWal ref;
      ref.replay(eng.journal_path());
      const std::string key = op.at("key").get<std::string>();
      const std::string want = ref.get(key);
      const std::string got = eng.get(key);
      if (want != got) {
        report["aligned"] = false;
        if (report["first_mismatch_index"].is_null()) {
          report["first_mismatch_index"] = i;
          report["first_mismatch_kind"] = "get";
          report["expected"] = want;
          report["actual"] = got;
        }
      }
    } else if (name == "scan") {
      ts::ReferenceFromWal ref;
      ref.replay(eng.journal_path());
      const std::string start = op.at("start").get<std::string>();
      const std::string end = op.at("end").get<std::string>();
      const std::string want = ref.scan(start, end);
      const std::string got = eng.scan(start, end);
      if (want != got) {
        report["aligned"] = false;
        if (report["first_mismatch_index"].is_null()) {
          report["first_mismatch_index"] = i;
          report["first_mismatch_kind"] = "scan";
          report["expected"] = want;
          report["actual"] = got;
        }
      }
    } else if (name == "check_structure") {
      ts::ReferenceFromWal ref;
      ref.replay(eng.journal_path());
      const nlohmann::json want = ref.structure_snapshot();
      const nlohmann::json got = eng.structure_snapshot();
      if (want != got) {
        report["aligned"] = false;
        if (report["first_mismatch_index"].is_null()) {
          report["first_mismatch_index"] = i;
          report["first_mismatch_kind"] = "structure";
          report["expected"] = want.dump();
          report["actual"] = got.dump();
        }
      }
    }
  }

  write_report(argv[2], report);
  return 0;
}
