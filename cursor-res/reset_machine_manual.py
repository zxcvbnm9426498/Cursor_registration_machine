import os
import sys
import json
import uuid
import hashlib
import shutil
import sqlite3
import platform
import re
import tempfile
from colorama import Fore, Style, init
from typing import Tuple

# Initialize colorama
init()

# Define emoji constants
EMOJI = {
    "FILE": "📄",
    "BACKUP": "💾",
    "SUCCESS": "✅",
    "ERROR": "❌",
    "INFO": "ℹ️",
    "RESET": "🔄",
}

def get_cursor_paths(translator=None) -> Tuple[str, str]:
    """ Get Cursor related paths"""
    system = platform.system()

    paths_map = {
        "Darwin": {
            "base": "/Applications/Cursor.app/Contents/Resources/app",
            "package": "package.json",
            "main": "out/main.js",
        },
        "Windows": {
            "base": os.path.join(
                os.getenv("LOCALAPPDATA", ""), "Programs", "Cursor", "resources", "app"
            ),
            "package": "package.json",
            "main": "out/main.js",
        },
        "Linux": {
            "bases": ["/opt/Cursor/resources/app", "/usr/share/cursor/resources/app"],
            "package": "package.json",
            "main": "out/main.js",
        },
    }

    if system not in paths_map:
        raise OSError(translator.get('reset.unsupported_os', system=system) if translator else f"不支持的操作系统: {system}")

    if system == "Linux":
        for base in paths_map["Linux"]["bases"]:
            pkg_path = os.path.join(base, paths_map["Linux"]["package"])
            if os.path.exists(pkg_path):
                return (pkg_path, os.path.join(base, paths_map["Linux"]["main"]))
        raise OSError(translator.get('reset.linux_path_not_found') if translator else "在 Linux 系统上未找到 Cursor 安装路径")

    base_path = paths_map[system]["base"]
    return (
        os.path.join(base_path, paths_map[system]["package"]),
        os.path.join(base_path, paths_map[system]["main"]),
    )

def version_check(version: str, min_version: str = "", max_version: str = "", translator=None) -> bool:
    """Version number check"""
    version_pattern = r"^\d+\.\d+\.\d+$"
    try:
        if not re.match(version_pattern, version):
            print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.invalid_version_format', version=version)}{Style.RESET_ALL}")
            return False

        def parse_version(ver: str) -> Tuple[int, ...]:
            return tuple(map(int, ver.split(".")))

        current = parse_version(version)

        if min_version and current < parse_version(min_version):
            print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.version_too_low', version=version, min_version=min_version)}{Style.RESET_ALL}")
            return False

        if max_version and current > parse_version(max_version):
            print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.version_too_high', version=version, max_version=max_version)}{Style.RESET_ALL}")
            return False

        return True

    except Exception as e:
        print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.version_check_error', error=str(e))}{Style.RESET_ALL}")
        return False

def check_cursor_version(translator) -> bool:
    """Check Cursor version"""
    try:
        pkg_path, _ = get_cursor_paths(translator)
        with open(pkg_path, "r", encoding="utf-8") as f:
            version = json.load(f)["version"]
        return version_check(version, min_version="0.45.0", translator=translator)
    except Exception as e:
        print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.check_version_failed', error=str(e))}{Style.RESET_ALL}")
        return False

def modify_main_js(main_path: str, translator) -> bool:
    """Modify main.js file"""
    try:
        original_stat = os.stat(main_path)
        original_mode = original_stat.st_mode
        original_uid = original_stat.st_uid
        original_gid = original_stat.st_gid

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            with open(main_path, "r", encoding="utf-8") as main_file:
                content = main_file.read()

            patterns = {
                r"async getMachineId\(\)\{return [^??]+\?\?([^}]+)\}": r"async getMachineId(){return \1}",
                r"async getMacMachineId\(\)\{return [^??]+\?\?([^}]+)\}": r"async getMacMachineId(){return \1}",
            }

            for pattern, replacement in patterns.items():
                content = re.sub(pattern, replacement, content)

            tmp_file.write(content)
            tmp_path = tmp_file.name

        shutil.copy2(main_path, main_path + ".old")
        shutil.move(tmp_path, main_path)

        os.chmod(main_path, original_mode)
        if os.name != "nt":
            os.chown(main_path, original_uid, original_gid)

        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {translator.get('reset.file_modified')}{Style.RESET_ALL}")
        return True

    except Exception as e:
        print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.modify_file_failed', error=str(e))}{Style.RESET_ALL}")
        if "tmp_path" in locals():
            os.unlink(tmp_path)
        return False

def patch_cursor_get_machine_id(translator) -> bool:
    """Patch Cursor getMachineId function"""
    try:
        print(f"{Fore.CYAN}{EMOJI['INFO']} {translator.get('reset.start_patching')}...{Style.RESET_ALL}")
        
        # Get paths
        pkg_path, main_path = get_cursor_paths(translator)
        
        # Check file permissions
        for file_path in [pkg_path, main_path]:
            if not os.path.isfile(file_path):
                print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.file_not_found', path=file_path)}{Style.RESET_ALL}")
                return False
            if not os.access(file_path, os.W_OK):
                print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.no_write_permission', path=file_path)}{Style.RESET_ALL}")
                return False

        # Get version number
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                version = json.load(f)["version"]
            print(f"{Fore.CYAN}{EMOJI['INFO']} {translator.get('reset.current_version', version=version)}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.read_version_failed', error=str(e))}{Style.RESET_ALL}")
            return False

        # Check version
        if not version_check(version, min_version="0.45.0", translator=translator):
            print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.version_not_supported')}{Style.RESET_ALL}")
            return False

        print(f"{Fore.CYAN}{EMOJI['INFO']} {translator.get('reset.version_check_passed')}{Style.RESET_ALL}")

        # Backup file
        backup_path = main_path + ".bak"
        if not os.path.exists(backup_path):
            shutil.copy2(main_path, backup_path)
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {translator.get('reset.backup_created', path=backup_path)}{Style.RESET_ALL}")

        # Modify file
        if not modify_main_js(main_path, translator):
            return False

        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {translator.get('reset.patch_completed')}{Style.RESET_ALL}")
        return True

    except Exception as e:
        print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.patch_failed', error=str(e))}{Style.RESET_ALL}")
        return False

class MachineIDResetter:
    def __init__(self, translator=None):
        self.translator = translator

        # Check operating system
        if sys.platform == "win32":  # Windows
            appdata = os.getenv("APPDATA")
            if appdata is None:
                raise EnvironmentError("APPDATA Environment Variable Not Set")
            self.db_path = os.path.join(
                appdata, "Cursor", "User", "globalStorage", "storage.json"
            )
            self.sqlite_path = os.path.join(
                appdata, "Cursor", "User", "globalStorage", "state.vscdb"
            )
        elif sys.platform == "darwin":  # macOS
            self.db_path = os.path.abspath(os.path.expanduser(
                "~/Library/Application Support/Cursor/User/globalStorage/storage.json"
            ))
            self.sqlite_path = os.path.abspath(os.path.expanduser(
                "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb"
            ))
        elif sys.platform == "linux":  # Linux
            self.db_path = os.path.abspath(os.path.expanduser(
                "~/.config/Cursor/User/globalStorage/storage.json"
            ))
            self.sqlite_path = os.path.abspath(os.path.expanduser(
                "~/.config/Cursor/User/globalStorage/state.vscdb"
            ))
        else:
            raise NotImplementedError(f"Not Supported OS: {sys.platform}")

    def generate_new_ids(self):
        """Generate new machine ID"""
        # Generate new UUID
        dev_device_id = str(uuid.uuid4())

        # Generate new machineId (64 characters of hexadecimal)
        machine_id = hashlib.sha256(os.urandom(32)).hexdigest()

        # Generate new macMachineId (128 characters of hexadecimal)
        mac_machine_id = hashlib.sha512(os.urandom(64)).hexdigest()

        # Generate new sqmId
        sqm_id = "{" + str(uuid.uuid4()).upper() + "}"

        return {
            "telemetry.devDeviceId": dev_device_id,
            "telemetry.macMachineId": mac_machine_id,
            "telemetry.machineId": machine_id,
            "telemetry.sqmId": sqm_id,
            "storage.serviceMachineId": dev_device_id,  # Add storage.serviceMachineId
        }

    def update_sqlite_db(self, new_ids):
        """Update machine ID in SQLite database"""
        try:
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('reset.updating_sqlite')}...{Style.RESET_ALL}")
            
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ItemTable (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            updates = [
                (key, value) for key, value in new_ids.items()
            ]

            for key, value in updates:
                cursor.execute("""
                    INSERT OR REPLACE INTO ItemTable (key, value) 
                    VALUES (?, ?)
                """, (key, value))
                print(f"{EMOJI['INFO']} {Fore.CYAN} {self.translator.get('reset.updating_pair')}: {key}{Style.RESET_ALL}")

            conn.commit()
            conn.close()
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('reset.sqlite_success')}{Style.RESET_ALL}")
            return True

        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('reset.sqlite_error', error=str(e))}{Style.RESET_ALL}")
            return False

    def update_system_ids(self, new_ids):
        """Update system-level IDs"""
        try:
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('reset.updating_system_ids')}...{Style.RESET_ALL}")
            
            if sys.platform.startswith("win"):
                self._update_windows_machine_guid()
            elif sys.platform == "darwin":
                self._update_macos_platform_uuid(new_ids)
                
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('reset.system_ids_updated')}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('reset.system_ids_update_failed', error=str(e))}{Style.RESET_ALL}")
            return False

    def _update_windows_machine_guid(self):
        """Update Windows MachineGuid"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                "SOFTWARE\\Microsoft\\Cryptography",
                0,
                winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
            )
            new_guid = str(uuid.uuid4())
            winreg.SetValueEx(key, "MachineGuid", 0, winreg.REG_SZ, new_guid)
            winreg.CloseKey(key)
            print("Windows MachineGuid updated successfully")
        except PermissionError:
            print("Permission denied: Run as administrator to update Windows MachineGuid")
            raise
        except Exception as e:
            print(f"Failed to update Windows MachineGuid: {e}")
            raise

    def _update_macos_platform_uuid(self, new_ids):
        """Update macOS Platform UUID"""
        try:
            uuid_file = "/var/root/Library/Preferences/SystemConfiguration/com.apple.platform.uuid.plist"
            if os.path.exists(uuid_file):
                # Use sudo to execute plutil command
                cmd = f'sudo plutil -replace "UUID" -string "{new_ids["telemetry.macMachineId"]}" "{uuid_file}"'
                result = os.system(cmd)
                if result == 0:
                    print("macOS Platform UUID updated successfully")
                else:
                    raise Exception("Failed to execute plutil command")
        except Exception as e:
            print(f"Failed to update macOS Platform UUID: {e}")
            raise

    def reset_machine_ids(self):
        """Reset machine ID and backup original file"""
        try:
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('reset.checking')}...{Style.RESET_ALL}")

            if not os.path.exists(self.db_path):
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('reset.not_found')}: {self.db_path}{Style.RESET_ALL}")
                return False

            if not os.access(self.db_path, os.R_OK | os.W_OK):
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('reset.no_permission')}{Style.RESET_ALL}")
                return False

            print(f"{Fore.CYAN}{EMOJI['FILE']} {self.translator.get('reset.reading')}...{Style.RESET_ALL}")
            with open(self.db_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            backup_path = self.db_path + ".bak"
            if not os.path.exists(backup_path):
                print(f"{Fore.YELLOW}{EMOJI['BACKUP']} {self.translator.get('reset.creating_backup')}: {backup_path}{Style.RESET_ALL}")
                shutil.copy2(self.db_path, backup_path)
            else:
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('reset.backup_exists')}{Style.RESET_ALL}")

            print(f"{Fore.CYAN}{EMOJI['RESET']} {self.translator.get('reset.generating')}...{Style.RESET_ALL}")
            new_ids = self.generate_new_ids()

            # Update configuration file
            config.update(new_ids)

            print(f"{Fore.CYAN}{EMOJI['FILE']} {self.translator.get('reset.saving_json')}...{Style.RESET_ALL}")
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)

            # Update SQLite database
            self.update_sqlite_db(new_ids)

            # Update system IDs
            self.update_system_ids(new_ids)

            # Check Cursor version and perform corresponding actions
            greater_than_0_45 = check_cursor_version(self.translator)
            if greater_than_0_45:
                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('reset.detecting_version')} >= 0.45.0，{self.translator.get('reset.patching_getmachineid')}{Style.RESET_ALL}")
                patch_cursor_get_machine_id(self.translator)
            else:
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('reset.version_less_than_0_45')}{Style.RESET_ALL}")

            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('reset.success')}{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}{self.translator.get('reset.new_id')}:{Style.RESET_ALL}")
            for key, value in new_ids.items():
                print(f"{EMOJI['INFO']} {key}: {Fore.GREEN}{value}{Style.RESET_ALL}")

            return True

        except PermissionError as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('reset.permission_error', error=str(e))}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('reset.run_as_admin')}{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('reset.process_error', error=str(e))}{Style.RESET_ALL}")
            return False

def run(translator=None):
    """Convenient function for directly calling the reset function"""
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['RESET']} {translator.get('reset.title')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")

    resetter = MachineIDResetter(translator)  # Correctly pass translator
    resetter.reset_machine_ids()

    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    input(f"{EMOJI['INFO']} {translator.get('reset.press_enter')}...")

if __name__ == "__main__":
    from main import translator as main_translator
    run(main_translator)