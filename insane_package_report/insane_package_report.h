#pragma once

#include "esphome/core/component.h"
#include <vector>
#include <string>

namespace esphome {
namespace insane_package_report {

struct Repository {
  std::string url;
  std::string ref;
  std::string type;
};

class InsanePackageReport : public Component {
 public:
  void setup() override;
  void loop() override;
  void add_repository(const std::string &url, const std::string &ref, const std::string &type);

 protected:
  std::vector<Repository> repositories_;
  bool was_connected_{false};
  void on_client_connected_();
};

}  // namespace insane_package_report
}  // namespace esphome
