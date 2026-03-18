#pragma once

#include "esphome/core/component.h"
#include "esphome/components/api/api_server.h"
#include <vector>
#include <string>

namespace esphome {
namespace insane_package_report {

struct ReportItem {
  std::string type;
  std::string name;
  std::string url;
  std::string ref;
  std::string path;
};

class InsanePackageReport : public Component {
 public:
  void setup() override;
  void loop() override;
  void dump_config() override;

  float get_setup_priority() const override { return setup_priority::LATE; }

  void add_item(const std::string &type, const std::string &name, const std::string &url, const std::string &ref, const std::string &path) {
    this->items_.push_back({type, name, url, ref, path});
  }

 protected:
  void on_client_connected_(const std::string &client_info);

  std::vector<ReportItem> items_;
  bool pending_report_{false};
  uint32_t report_start_time_{0};
  size_t current_report_index_{0};

  // Wait 5 seconds after connection before sending events
  const uint32_t REPORT_DELAY_MS = 5000;
  // Delay between events to avoid overflowing the queue
  const uint32_t EVENT_DELAY_MS = 100;
  uint32_t last_event_time_{0};
};

}  // namespace insane_package_report
}  // namespace esphome
