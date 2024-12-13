import subprocess
import os
import argparse

# Parse arguments
parser = argparse.ArgumentParser(description="Inject a system certificate into an Android device.")
parser.add_argument("certificate_path", nargs="?", help="Path to the certificate to be injected.")
args = parser.parse_args()

CERTIFICATE_PATH = args.certificate_path

if not CERTIFICATE_PATH:
    script_name = os.path.basename(__file__)
    print(f"Error: Certificate is required. Please provide it as an argument.\nExample: python {script_name} <cert_name>.0")
    exit(1)

# Helper function to execute ADB commands
def adb_command(command, description):
    print(f"Running: {description}...", end=" ")
    try:
        result = subprocess.run(
            ["adb"] + command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print("FAIL")
            raise RuntimeError(f"Command failed: {result.stderr.strip()}")
        print("PASS")
        return result.stdout.strip()
    except Exception as e:
        print("FAIL")
        print(f"Error executing command '{command}': {e}")
        exit(1)

# Check if ADB device is connected
devices_output = adb_command("devices", "Checking ADB devices")
if not any(line.strip() and not line.startswith("List of devices attached") for line in devices_output.splitlines()):
    print("Error: No ADB devices connected.")
    exit(1)

# Create a temporary directory on the device
adb_command("shell mkdir -p -m 700 /data/local/tmp/tmp-ca-copy", "Creating temporary directory on device")

# Copy existing certificates to the temporary directory
adb_command("shell cp /apex/com.android.conscrypt/cacerts/* /data/local/tmp/tmp-ca-copy/", "Backing up existing certificates")

# Mount tmpfs over the system certificate directory
adb_command("shell mount -t tmpfs tmpfs /system/etc/security/cacerts", "Mounting tmpfs over system cert directory")

# Copy back the original certificates
adb_command("shell mv /data/local/tmp/tmp-ca-copy/* /system/etc/security/cacerts/", "Restoring original certificates")

# Push the new certificate to the device
adb_command(f"push {CERTIFICATE_PATH} /data/local/tmp/{CERTIFICATE_PATH}", "Pushing new certificate to device")

# Move the new certificate into the system certificates directory
adb_command(f"shell mv /data/local/tmp/{CERTIFICATE_PATH} /system/etc/security/cacerts/", "Moving new certificate into cert directory")

# Update permissions and SELinux labels
adb_command("shell chown root:root /system/etc/security/cacerts/*", "Updating certificate ownership")
adb_command("shell chmod 644 /system/etc/security/cacerts/*", "Setting certificate permissions")
adb_command("shell chcon u:object_r:system_file:s0 /system/etc/security/cacerts/*", "Setting SELinux labels")

# Handle the APEX overrides
zygote_pids = adb_command("shell pidof zygote || true", "Getting zygote PIDs").split()
zygote64_pids = adb_command("shell pidof zygote64 || true", "Getting zygote64 PIDs").split()
all_zygote_pids = zygote_pids + zygote64_pids

if not all_zygote_pids:
    print("Error: No zygote processes found.")
    exit(1)

for z_pid in all_zygote_pids:
    adb_command(
        f"shell nsenter --mount=/proc/{z_pid}/ns/mnt -- " +
        f"/bin/mount --bind /system/etc/security/cacerts /apex/com.android.conscrypt/cacerts",
        f"Injecting mount into zygote PID {z_pid}"
    )

# Inject the mount into all running app namespaces
zygote_pid_str = " ".join(all_zygote_pids)
app_pids_output = adb_command(
    f"shell echo \"{zygote_pid_str}\" | xargs -n1 ps -o 'PID' -P | grep -v PID",
    "Getting app PIDs from zygote"
)
app_pids = app_pids_output.split()

if not app_pids:
    print("Warning: No app processes found to inject the mount.")

for pid in app_pids:
    adb_command(
        f"shell nsenter --mount=/proc/{pid}/ns/mnt -- " +
        f"/bin/mount --bind /system/etc/security/cacerts /apex/com.android.conscrypt/cacerts",
        f"Injecting mount into app PID {pid}"
    )

print("System certificate injected")

