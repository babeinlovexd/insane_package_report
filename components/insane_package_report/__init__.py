import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import CONF_ID
from esphome.core import CORE

DEPENDENCIES = ["api"]

insane_package_report_ns = cg.esphome_ns.namespace("insane_package_report")
InsanePackageReport = insane_package_report_ns.class_("InsanePackageReport", cg.Component)

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(InsanePackageReport),
}).extend(cv.COMPONENT_SCHEMA)

def extract_github_info(data, item_type):
    repos = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                if "github" in value:
                    url = value["github"]
                    if not url.startswith("https://") and not url.startswith("github://"):
                        url = f"https://github.com/{url}"
                    ref = value.get("ref", "")
                    repos.append({"url": url, "ref": ref, "type": item_type})
                elif "url" in value and "github.com" in value["url"]:
                    url = value["url"]
                    ref = value.get("ref", "")
                    repos.append({"url": url, "ref": ref, "type": item_type})
            elif isinstance(value, str):
                if value.startswith("github://"):
                    parts = value.replace("github://", "").split("@")
                    url = f"https://github.com/{parts[0]}"
                    ref = parts[1] if len(parts) > 1 else ""
                    repos.append({"url": url, "ref": ref, "type": item_type})
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                source = item.get("source", {})
                if isinstance(source, dict):
                    if "type" in source and source["type"] == "git":
                        url = source.get("url", "")
                        if "github.com" in url:
                            ref = source.get("ref", "")
                            repos.append({"url": url, "ref": ref, "type": item_type})
                    elif "github" in source:
                        url = source["github"]
                        if not url.startswith("https://") and not url.startswith("github://"):
                            url = f"https://github.com/{url}"
                        ref = source.get("ref", "")
                        repos.append({"url": url, "ref": ref, "type": item_type})
                elif isinstance(source, str):
                    if source.startswith("github://"):
                        parts = source.replace("github://", "").split("@")
                        url = f"https://github.com/{parts[0]}"
                        ref = parts[1] if len(parts) > 1 else ""
                        repos.append({"url": url, "ref": ref, "type": item_type})
    return repos

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    repos = []

    if hasattr(CORE, "raw_config"):
        if "packages" in CORE.raw_config:
            repos.extend(extract_github_info(CORE.raw_config["packages"], "packages"))

        if "external_components" in CORE.raw_config:
            repos.extend(extract_github_info(CORE.raw_config["external_components"], "external_components"))

    for repo in repos:
        cg.add(var.add_repository(repo["url"], repo["ref"], repo["type"]))
