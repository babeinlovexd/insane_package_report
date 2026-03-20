// https://github.com/babeinlovexd

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

  uint32_t delay_ms = 5000;
  int index = 0;

  // Clear old timeout names if any to prevent unbounded growth,
  // though typically this is only called once per connection.
  for (const auto &name : this->timeout_names_) {
    this->cancel_timeout(name.c_str());
  }
  this->timeout_names_.clear();
  this->timeout_names_.reserve(this->repositories_.size());

  for (const auto &repo : this->repositories_) {
    std::string url_copy = repo.url;
    std::string ref_copy = repo.ref;
    std::string type_copy = repo.type;

    this->timeout_names_.push_back("insane_report_" + std::to_string(index++));
    const char *timeout_name_ptr = this->timeout_names_.back().c_str();

    this->set_timeout(timeout_name_ptr, delay_ms, [this, url_copy, ref_copy, type_copy]() {
      if (api::global_api_server != nullptr && api::global_api_server->is_connected()) {
        ESP_LOGD(TAG, "Sending HA event: esphome.insane_package_report for %s", url_copy.c_str());

        this->fire_homeassistant_event("esphome.insane_package_report", {
          {"url", url_copy},
          {"ref", ref_copy},
          {"type", type_copy}
        });
      }
    });

    delay_ms += 2000;
  }
}

}
}
