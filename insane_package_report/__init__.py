import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_TYPE
from esphome.core import CORE
import logging

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ["api"]
AUTO_LOAD = ["api"]

insane_package_report_ns = cg.esphome_ns.namespace("insane_package_report")
InsanePackageReport = insane_package_report_ns.class_("InsanePackageReport", cg.Component)

CONF_TYPE_PACKAGES = "packages"
CONF_TYPE_EXTERNAL_COMPONENTS = "external_components"
CONF_TYPE_ALL = "all"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(InsanePackageReport),
        cv.Optional(CONF_TYPE, default=CONF_TYPE_ALL): cv.one_of(
            CONF_TYPE_PACKAGES, CONF_TYPE_EXTERNAL_COMPONENTS, CONF_TYPE_ALL, lower=True
        ),
    }
).extend(cv.COMPONENT_SCHEMA)

def get_github_source(source_dict):
    """Extract github source information from a source dict."""
    if not isinstance(source_dict, dict):
        return None

    if "github" in source_dict:
        url = source_dict["github"]
        ref = source_dict.get("ref", "")
        path = source_dict.get("path", "")
        return {
            "source": "github",
            "url": url,
            "ref": ref,
            "path": path
        }
    return None

def extract_packages(raw_config):
    """Extract package information from raw config."""
    packages_data = []

    # In esphome, packages are top-level
    if "packages" in raw_config:
        packages = raw_config["packages"]
        if isinstance(packages, dict):
            # dict format: package_name: url
            for pkg_name, pkg_source in packages.items():
                if isinstance(pkg_source, str) and pkg_source.startswith("github://"):
                    # Format: github://user/repo/path/to/file@ref
                    parts = pkg_source.replace("github://", "").split("@")
                    url_path = parts[0]
                    ref = parts[1] if len(parts) > 1 else ""

                    # Split url_path into user/repo and path
                    url_parts = url_path.split("/")
                    if len(url_parts) >= 2:
                        url = f"{url_parts[0]}/{url_parts[1]}"
                        path = "/".join(url_parts[2:]) if len(url_parts) > 2 else ""
                        packages_data.append({
                            "type": "package",
                            "name": pkg_name,
                            "source": "github",
                            "url": url,
                            "ref": ref,
                            "path": path
                        })
        elif isinstance(packages, list):
            # list format: - url
            for pkg_source in packages:
                if isinstance(pkg_source, str) and pkg_source.startswith("github://"):
                    parts = pkg_source.replace("github://", "").split("@")
                    url_path = parts[0]
                    ref = parts[1] if len(parts) > 1 else ""

                    url_parts = url_path.split("/")
                    if len(url_parts) >= 2:
                        url = f"{url_parts[0]}/{url_parts[1]}"
                        path = "/".join(url_parts[2:]) if len(url_parts) > 2 else ""
                        packages_data.append({
                            "type": "package",
                            "name": "unknown",
                            "source": "github",
                            "url": url,
                            "ref": ref,
                            "path": path
                        })

    return packages_data

def extract_external_components(raw_config):
    """Extract external components information from raw config."""
    ext_comps_data = []

    if "external_components" in raw_config:
        ext_comps = raw_config["external_components"]
        if not isinstance(ext_comps, list):
            ext_comps = [ext_comps]

        for comp in ext_comps:
            if isinstance(comp, dict) and "source" in comp:
                source = comp["source"]
                if isinstance(source, str) and source.startswith("github://"):
                    # string shorthand
                    parts = source.replace("github://", "").split("@")
                    url_path = parts[0]
                    ref = parts[1] if len(parts) > 1 else ""

                    url_parts = url_path.split("/")
                    if len(url_parts) >= 2:
                        url = f"{url_parts[0]}/{url_parts[1]}"
                        path = "/".join(url_parts[2:]) if len(url_parts) > 2 else ""
                        ext_comps_data.append({
                            "type": "external_component",
                            "name": comp.get("components", "all"),
                            "source": "github",
                            "url": url,
                            "ref": ref,
                            "path": path
                        })
                elif isinstance(source, dict):
                    # explicit dict
                    github_src = get_github_source(source)
                    if github_src:
                        ext_comps_data.append({
                            "type": "external_component",
                            "name": comp.get("components", "all"),
                            "source": github_src["source"],
                            "url": github_src["url"],
                            "ref": github_src["ref"],
                            "path": github_src["path"]
                        })

    return ext_comps_data

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    report_type = config[CONF_TYPE]
    raw_config = CORE.raw_config

    items_to_report = []

    if report_type in [CONF_TYPE_PACKAGES, CONF_TYPE_ALL]:
        packages = extract_packages(raw_config)
        items_to_report.extend(packages)

    if report_type in [CONF_TYPE_EXTERNAL_COMPONENTS, CONF_TYPE_ALL]:
        ext_comps = extract_external_components(raw_config)
        items_to_report.extend(ext_comps)

    _LOGGER.info(f"Found {len(items_to_report)} items to report via insane_package_report")

    # Add items to C++ component
    for item in items_to_report:
        # We only support github right now
        if item["source"] == "github":
            # Pass as: type, name, url, ref, path
            cg.add(var.add_item(
                item["type"],
                str(item["name"]) if isinstance(item["name"], list) else item["name"],
                item["url"],
                item["ref"],
                item["path"]
            ))
