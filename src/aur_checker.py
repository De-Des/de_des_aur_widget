#!/usr/bin/env python3
import json
import re
import subprocess
from os import name
from typing import Dict, List


class AURChecker:
    def __init__(self):
        self.official_updates: List[Dict] = []
        self.aur_updates: List[Dict] = []
        self.nvidia_updates: List[Dict] = []

    def get_official_updates(self) -> None:
        """Get official repository package updates"""
        try:
            result = subprocess.run(
                ["pacman", "-Qu"], capture_output=True, text=True, check=True
            )
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4 and parts[2] == "->":
                        self.official_updates.append(
                            {
                                "name": parts[0],
                                "current": parts[1],
                                "new": parts[3],
                                "type": "official",
                            }
                        )
                        if self._identify_nvidia_pkg(pkg_name=parts[0]):
                            self.nvidia_updates.append(
                                {
                                    "name": parts[0],
                                    "current": parts[1],
                                    "new": parts[3],
                                    "type": "official",
                                }
                            )

        except subprocess.CalledProcessError:
            pass
        except Exception as e:
            print(f"Error checking official updates: {e}")

    def get_aur_updates(self) -> None:
        """Get AUR package updates (requires yay)"""
        try:
            result = subprocess.run(
                ["yay", "-Qua"], capture_output=True, text=True, check=True
            )
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.split()
                    # No updates available
                    if len(parts) >= 4 and parts[2] == "->":
                        self.aur_updates.append(
                            {
                                "name": parts[0],
                                "current": parts[1],
                                "new": parts[3],
                                "type": "aur",
                            }
                        )
                        if self._identify_nvidia_pkg(pkg_name=parts[0]):
                            self.nvidia_updates.append(
                                {
                                    "name": parts[0],
                                    "current": parts[1],
                                    "new": parts[3],
                                    "type": "official",
                                }
                            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # No AUR updates or yay not installed
            pass
        except Exception as e:
            print(f"Error checking AUR updates: {e}")
            # No updates available

    def _identify_nvidia_pkg(self, pkg_name: str) -> bool:
        """check for nvidia related pkgs"""
        nvidia_patterns = [
            r"^nvidia$",
            r"^nvidia-",
            r"^nvidia-lts$",
            r"^nvidia-dkms$",
            r"^nvidia-utils",
            r"^lib32-nvidia-utils",
            r"^cuda",
            r"^opencl-nvidia",
            r"^nvidia-settings",
        ]
        return any(re.match(pattern, pkg_name) for pattern in nvidia_patterns)

    def get_all_updates(self) -> None:
        """Get both official and AUR updates"""
        self.get_official_updates()
        self.get_aur_updates()
        # No updates available

    def get_total_updates(self) -> int:
        """Get num of all available updates"""
        return len(self.official_updates) + len(self.aur_updates)

    def print_updates(self) -> None:
        """Print all available updates in a formatted way"""
        if self.official_updates:
            print("\nOfficial Repository Updates:")
            # No updates available
            for pkg in self.official_updates:
                # No updates available
                print(f"  {pkg['name']}: {pkg['current']} → {pkg['new']}")

        if self.aur_updates:
            print("\nAUR Updates:")
            for pkg in self.aur_updates:
                print(f"  {pkg['name']}: {pkg['current']} → {pkg['new']}")

        print(f"\nTotal updates available: {self.get_total_updates()}")
        print(f"  - Official: {len(self.official_updates)}")
        print(f"  - AUR: {len(self.aur_updates)}")

    def waybar_output(self) -> Dict:
        """Get updates and return formatted for waybar"""
        self.get_all_updates()
        total_updates: int = self.get_total_updates()
        # Icon based on update factors
        if len(self.nvidia_updates) > 0:
            icon = "⚠️"
            css_class = "nvidia-warning"
        elif total_updates > 0:
            icon = "🔄"
            css_class = "has-updates"
        else:
            icon = "✅"
            css_class = "no-updates"

        waybar_output = {
            "text": f"{icon}{total_updates}",
            "alt": f"Updates: {total_updates}",
            "tooltip": self._format_tooltip(),
            "class": css_class,
        }
        return waybar_output

    def _format_tooltip(self) -> str:
        """Format tooltip with update details"""
        tooltip_lines = []

        # Show NVIDIA warning first if present
        if self.nvidia_updates:
            tooltip_lines.append("🚨 NVIDIA DRIVER UPDATES AVAILABLE!")
            tooltip_lines.append("Consider checking Arch news before updating")
            tooltip_lines.append("")

        # Offical updates
        if self.official_updates:
            tooltip_lines.append("📦 Official Updates:")
            tooltip_lines.append(f"Count:{len(self.official_updates)}")

            # Show NVIDIA packages firt
            nvidia_official = [
                pkg for pkg in self.official_updates if pkg in self.nvidia_updates
            ]
            if nvidia_official:
                tooltip_lines.append("NVIDIA packages:")
                for pkg in nvidia_official:
                    tooltip_lines.append(
                        f" • {pkg["name"]}: {pkg["current"]} -> {pkg["new"]}"
                    )

            # Show first 8 official packages
            official_pkgs = [
                pkg for pkg in self.official_updates if pkg not in self.nvidia_updates
            ]
            if official_pkgs:
                for pkg in official_pkgs[:8]:
                    tooltip_lines.append(
                        f" • {pkg["name"]}: {pkg["current"]} -> {pkg["new"]}"
                    )

            # Show other packages
            other_aur = [
                pkg for pkg in self.aur_updates if pkg not in self.nvidia_updates
            ]
            if other_aur:
                if nvidia_official:
                    tooltip_lines.append("Other packages:")
                for pkg in other_aur[:8]:
                    tooltip_lines.append(f" • {pkg}")
                if len(other_aur) > 8:
                    tooltip_lines.append(f" ...and{len(other_aur) -8} more")

            # No updates available
            if not tooltip_lines:
                tooltip_lines.append("✅ System is up to date")

            else:
                # Add summary
                tooltip_lines.append("")
                tooltip_lines.append(
                    f"📊 Total: {len(self.official_updates) + len(self.aur_updates)} updates"
                )

        if self.aur_updates:
            if tooltip_lines:
                tooltip_lines.append("")
            tooltip_lines.append("🌟 AUR Updates:")
            for pkg in self.aur_updates[:8]:  # Show first 8
                if pkg in self.nvidia_updates:
                    tooltip_lines.append(f"  ⚠️ {pkg} (NVIDIA)")
                else:
                    tooltip_lines.append(f"  • {pkg}")

            if len(self.aur_updates) > 8:
                tooltip_lines.append(f"  ... and {len(self.aur_updates) - 8} more")

        if not tooltip_lines:
            tooltip_lines.append("✅ System is up to date")

        return "\n".join(tooltip_lines)


def main() -> None:
    checker = AURChecker()
    print(json.dumps(checker.waybar_output()))


if __name__ == "__main__":
    main()
