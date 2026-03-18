#include "insane_package_report.h"
#include "esphome/core/log.h"
#include "esphome/components/api/api_server.h"
#include "esphome/core/application.h"

namespace esphome {
namespace insane_package_report {

static const char *const TAG = "insane_package_report";

void InsanePackageReport::setup() {
  if (api::global_api_server == nullptr) {
    ESP_LOGE(TAG, "API Server not found. InsanePackageReport needs API to be configured.");
  }
}

void InsanePackageReport::loop() {
  if (api::global_api_server == nullptr) return;

  bool is_connected = api::global_api_server->is_connected();
  if (is_connected && !this->api_connected_) {
    this->api_connected_ = true;
    this->on_client_connected_();
  } else if (!is_connected && this->api_connected_) {
    this->api_connected_ = false;
  }
}

void InsanePackageReport::add_repository(const std::string &url, const std::string &ref, const std::string &type) {
  this->repositories_.push_back({url, ref, type});
}

void InsanePackageReport::on_client_connected_() {
  ESP_LOGD(TAG, "API Client connected. Sending %zu package reports.", this->repositories_.size());

  // We send one event per repository with a delay to not overwhelm the connection and avoid the 255 char limit
  uint32_t delay_ms = 5000; // Start with 5 seconds delay to allow HA to finish setting up

  for (const auto &repo : this->repositories_) {
    std::string url_copy = repo.url;
    std::string ref_copy = repo.ref;
    std::string type_copy = repo.type;

    this->set_timeout(delay_ms, [this, url_copy, ref_copy, type_copy]() {
      if (api::global_api_server != nullptr && api::global_api_server->is_connected()) {
        ESP_LOGD(TAG, "Sending HA event: esphome.insane_package_report for %s", url_copy.c_str());

        this->fire_homeassistant_event("esphome.insane_package_report", {
          {"url", url_copy},
          {"ref", ref_copy},
          {"type", type_copy}
        });
      }
    });

    delay_ms += 2000; // 2 seconds between each event
  }
}

}  // namespace insane_package_report
}  // namespace esphome
