#include "insane_package_report.h"
#include "esphome/core/log.h"
#include "esphome/core/application.h"

namespace esphome {
namespace insane_package_report {

static const char *const TAG = "insane_package_report";

void InsanePackageReport::setup() {
  ESP_LOGCONFIG(TAG, "Setting up Insane Package Report...");

  if (api::global_api_server != nullptr) {
    api::global_api_server->add_client_connected_callback([this](const std::string &client_info) {
      this->on_client_connected_(client_info);
    });
  } else {
    ESP_LOGW(TAG, "API server not found, reports will not be sent!");
  }
}

void InsanePackageReport::loop() {
  if (!this->pending_report_) {
    return;
  }

  uint32_t now = millis();

  // Wait for initial delay
  if (now - this->report_start_time_ < this->REPORT_DELAY_MS) {
    return;
  }

  // Wait between events
  if (now - this->last_event_time_ < this->EVENT_DELAY_MS) {
    return;
  }

  if (this->current_report_index_ < this->items_.size()) {
    const auto &item = this->items_[this->current_report_index_];

    if (api::global_api_server != nullptr && api::global_api_server->is_connected()) {
      ESP_LOGD(TAG, "Sending report for %s: %s", item.type.c_str(), item.url.c_str());

      // Send event to Home Assistant
      // The payload structure is flat to keep it simple and within the 255 char limit
      // We send it as a custom JSON string in the data payload

      std::string data_json = "{";
      data_json += "\"type\":\"" + item.type + "\",";
      data_json += "\"name\":\"" + item.name + "\",";
      data_json += "\"url\":\"" + item.url + "\",";
      data_json += "\"ref\":\"" + item.ref + "\",";
      data_json += "\"path\":\"" + item.path + "\"";
      data_json += "}";

      // Fire the custom event
      api::global_api_server->send_homeassistant_event(
        "esphome.insane_package_report",
        {{"data", data_json}}
      );

      this->current_report_index_++;
      this->last_event_time_ = now;
    } else {
      // Client disconnected before we finished reporting, abort and wait for next connection
      this->pending_report_ = false;
      ESP_LOGD(TAG, "Client disconnected, aborting report.");
    }
  } else {
    // Finished reporting
    this->pending_report_ = false;
    ESP_LOGD(TAG, "Finished sending %zu reports.", this->items_.size());
  }
}

void InsanePackageReport::dump_config() {
  ESP_LOGCONFIG(TAG, "Insane Package Report:");
  ESP_LOGCONFIG(TAG, "  Total items to report: %zu", this->items_.size());
  for (const auto &item : this->items_) {
    ESP_LOGCONFIG(TAG, "    - %s: %s (ref: %s)", item.type.c_str(), item.url.c_str(), item.ref.c_str());
  }
}

void InsanePackageReport::on_client_connected_(const std::string &client_info) {
  ESP_LOGD(TAG, "API Client connected (%s), scheduling report in %u ms",
           client_info.c_str(), this->REPORT_DELAY_MS);

  if (this->items_.empty()) {
    ESP_LOGD(TAG, "No items to report.");
    return;
  }

  this->pending_report_ = true;
  this->report_start_time_ = millis();
  this->current_report_index_ = 0;
  this->last_event_time_ = 0;
}

}  // namespace insane_package_report
}  // namespace esphome
