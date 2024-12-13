# Script Description and Prerequisites

## Purpose

This script is designed to inject a custom system certificate into an Android device using ADB (Android Debug Bridge). It ensures that the new certificate is integrated into the system's trusted certificate store while retaining the existing certificates. The script uses ADB commands to interact with the device and performs necessary configurations, including setting permissions and updating SELinux labels.

For more details and an in-depth understanding of the underlying concepts, refer to this [guide on installing system CA certificates on Android 14+](https://httptoolkit.com/blog/android-14-install-system-ca-certificate/).

## Key Features

1. **Backup Existing Certificates**: Saves the current certificates to a temporary directory on the device.
2. **Mount Temporary Filesystem**: Creates a temporary filesystem to facilitate certificate injection.
3. **Inject Custom Certificate**: Adds the provided certificate to the system's trusted certificate directory.
4. **Preserve Original Certificates**: Restores the existing certificates after mounting the temporary filesystem.
5. **Update Permissions and Labels**: Configures ownership, file permissions, and SELinux labels for the certificates.
6. **APEX Overrides**: Injects the mount into relevant namespaces to ensure all processes recognize the updated certificates.

## Script Workflow

1. Parse the input certificate path.
2. Verify if ADB devices are connected.
3. Create a temporary directory on the device.
4. Backup the existing certificates to the temporary directory.
5. Mount a temporary filesystem over the system certificate directory.
6. Restore the original certificates to the temporary filesystem.
7. Push the new certificate to the device.
8. Move the new certificate to the system certificate directory.
9. Update the certificate ownership, permissions, and SELinux labels.
10. Handle APEX overrides by injecting the mount into zygote and app namespaces.
11. Print status messages for each step, indicating success or failure.

## Prerequisites

1. **Python Environment**: Ensure Python 3 is installed on the host system.
2. **ADB Installation**: Install ADB on the host system and ensure it is in the system's PATH. Instructions:
   - On Windows: Download the [ADB tools](https://developer.android.com/studio/releases/platform-tools) and add the extracted folder to your PATH.
   - On macOS/Linux: Use your package manager (e.g., `brew install android-platform-tools` on macOS or `sudo apt install adb` on Linux).
3. **USB Debugging**: Enable USB debugging on the Android device.
4. **Root Access**: The Android device must be rooted to perform operations requiring elevated permissions.
5. **Certificate File**: Provide the path to the custom certificate as an argument when running the script.
6. **SELinux Context**: Verify that the device supports setting SELinux contexts via `chcon`.
7. **Connected Device**: Ensure the Android device is connected and recognized by ADB.

## Example Usage

```bash
python put_cert.py /path/to/certificate.pem
```

If the certificate path is missing, the script will prompt an error with an example command:

```
Error: Certificate path is required. Please provide it as an argument.
Example: python put_cert.py /path/to/certificate.pem
```

## Notes

- The script assumes the certificate filename is in the proper format (e.g., `9a5ba575.0`) as expected by the Android system.
- If no devices are connected, the script will terminate with an error message.
- The script provides detailed status updates for each operation, indicating whether it passed or failed.

## Limitations

- This script is designed for advanced users with knowledge of Android debugging and certificate management.
- Root access is mandatory, as modifying system directories is restricted on non-rooted devices.
- Misuse of the script could lead to system instability or bricking of the device. Ensure you understand the operations before proceeding.

## Troubleshooting

### ADB Device Not Found

Ensure the device is connected and recognized by ADB. Use `adb devices` to verify:

```bash
adb devices
```

If the device does not appear, check the following:

- Ensure USB debugging is enabled.
- Verify that the correct USB drivers are installed (Windows).

### Permission Denied

Verify the device is rooted and has granted ADB root access. Use the following command to switch to root mode:

```bash
adb root
```

If the command fails, confirm that the device has been rooted correctly.

### SELinux Issues

Ensure the device supports `chcon` for setting SELinux labels. Some devices may require additional configuration to enable SELinux modifications.

### Certificate Format

The certificate filename must follow the required format (e.g., `9a5ba575.0`). You can verify or rename the file using this command:

```bash
openssl x509 -inform PEM -subject_hash_old -in certificate.pem | head -1
mv certificate.pem <output_hash>.0
```

### No Zygote Processes Found

If no zygote processes are detected, the script cannot apply APEX overrides. Ensure the device is running normally and has not restricted system-level debugging.

## Post-Script Verification

1. **Verify Certificate Presence**: Check if the certificate exists in the directory:

   ```bash
   adb shell ls /system/etc/security/cacerts
   ```

2. **Test Certificate Recognition**: Use an app or browser on the device to confirm the system recognizes the new certificate.

3. **Check Mount Points**: Ensure the APEX overrides were successfully applied:

   ```bash
   adb shell mount | grep cacerts
   ```

