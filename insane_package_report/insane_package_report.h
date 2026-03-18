#pragma once

#include "esphome/core/component.h"
#include <vector>
#include <string>
#include "esphome/core/automation.h"

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
  void add_repository(const std::string &url, const std::string &ref, const std::string &type);
  void on_client_connected_(const std::string &client_address);

 protected:
  std::vector<Repository> repositories_;
};

class ClientConnectedAction : public Action<std::string, std::string> {
public:
  ClientConnectedAction(InsanePackageReport *parent) : parent_(parent) {}
  void play(const std::string &client_address, const std::string &client_name) override {
    this->parent_->on_client_connected_(client_address);
  }
protected:
  InsanePackageReport *parent_;
};

}  // namespace insane_package_report
}  // namespace esphome
