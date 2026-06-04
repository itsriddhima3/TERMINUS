#include <fstream>
#include <string>

namespace vx {
namespace decoy {

void append_epoch_note(int frame, int epoch) {
    std::ofstream out("/tmp/velox_epoch.trace", std::ios::app);
    out << frame << ' ' << epoch << '\n';
}

}  // namespace decoy
}  // namespace vx
