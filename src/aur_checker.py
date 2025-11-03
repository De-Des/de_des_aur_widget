import subprocess
from re import A
from typing import Dict, List


class AURChecker:
    def __init__(self):
        self.official_updates: List[Dict] = []
        self.aur_updates: List[Dict] = []

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
        except subprocess.CalledProcessError:
            # No updates available
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
                    if len(parts) >= 4 and parts[2] == "->":
                        self.aur_updates.append(
                            {
                                "name": parts[0],
                                "current": parts[1],
                                "new": parts[3],
                                "type": "aur",
                            }
                        )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # No AUR updates or yay not installed
            pass
        except Exception as e:
            print(f"Error checking AUR updates: {e}")

    def get_all_updates(self) -> None:
        """Get both official and AUR updates"""
        self.get_official_updates()
        self.get_aur_updates()

    def get_total_updates(self) -> int:
        return len(self.official_updates) + len(self.aur_updates)

    def print_updates(self) -> None:
        """Print all available updates in a formatted way"""
        if self.official_updates:
            print("\nOfficial Repository Updates:")
            for pkg in self.official_updates:
                print(f"  {pkg['name']}: {pkg['current']} → {pkg['new']}")

        if self.aur_updates:
            print("\nAUR Updates:")
            for pkg in self.aur_updates:
                print(f"  {pkg['name']}: {pkg['current']} → {pkg['new']}")

        print(f"\nTotal updates available: {self.get_total_updates()}")
        print(f"  - Official: {len(self.official_updates)}")
        print(f"  - AUR: {len(self.aur_updates)}")

    def waybar_output(self) -> Dict:
        """Get update and return formatted for waybar"""

        self.get_official_updates()

        self.get_aur_updates()
        total_updates: int = len(self.official_updates) + len(self.aur_updates)
        # Waybar JSON output
        waybar_output = {
            "text": f"🔄 {total_updates}",
            "alt": f"Updates: {total_updates}",
            "tooltip": self._format_tooltip(),
            "class": "has-updates" if total_updates > 0 else "no-updates",
        }

        return waybar_output

    def _format_tooltip(self) -> str:
        """Format tooltip with update details"""
        tooltip_lines = []

        if self.official_updates:
            tooltip_lines.append("📦 Official Updates:")
            tooltip_lines.extend(
                # Show first 10
                [f"  • {pkg}" for pkg in self.official_updates[:10]]
            )
            if len(self.official_updates) > 10:
                tooltip_lines.append(
                    f"  ... and {len(self.official_updates) - 10} more"
                )

        if self.aur_updates:
            if tooltip_lines:
                tooltip_lines.append("")
            tooltip_lines.append("🌟 AUR Updates:")
            tooltip_lines.extend(
                # Show first 10
                [f"  • {pkg}" for pkg in self.aur_updates[:10]]
            )
            if len(self.aur_updates) > 10:
                tooltip_lines.append(f"  ... and {len(self.aur_updates) - 10} more")

        if not tooltip_lines:
            tooltip_lines.append("✅ System is up to date")

        return "\n".join(tooltip_lines)



