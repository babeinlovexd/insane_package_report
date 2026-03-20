#pragma once

#include "esphome/core/component.h"
#include <vector>
#include <string>
#include "esphome/components/api/custom_api_device.h"

namespace esphome {
namespace insane_package_report {

struct Repository {
  std::string url;
  std::string ref;
  std::string type;
};

class InsanePackageReport : public Component, public api::CustomAPIDevice {
 public:
  void setup() override;
  void loop() override;
  void add_repository(const std::string &url, const std::string &ref, const std::string &type);
  void on_client_connected_();

 protected:
  std::vector<Repository> repositories_;
  bool api_connected_{false};
};

}
}
