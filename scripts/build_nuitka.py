#!/usr/bin/env python3
"""
build_nuitka.py - Build markitdown binaries using Nuitka

This script:
1. Detects the current platform
2. Runs Nuitka to compile the Python code to a standalone binary
3. Copies the binary to the appropriate bin/<platform>-nuitka/ directory
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path


def get_platform():
    """Detect the current platform and return platform identifier."""
    system = platform.system().lower()
    if system == "windows":
        return "win32"
    elif system == "darwin":
        return "darwin"
    elif system == "linux":
        return "linux"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def get_binary_name(plat):
    """Get the appropriate binary name for the platform."""
    if plat == "win32":
        return "markitdown.exe"
    else:
        return "markitdown.bin"


def main():
    # Get paths
    script_dir = Path(__file__).parent.resolve()
    root_dir = script_dir.parent
    entry_point = root_dir / "build" / "specs" / "entry_point.py"
    build_dir = root_dir / "build"

    # Detect platform
    plat = get_platform()
    binary_name = get_binary_name(plat)

    print(f"=== Building markitdown binary with Nuitka for {plat} ===")
    print(f"Root directory: {root_dir}")
    print(f"Entry point: {entry_point}")
    print(f"Platform: {plat}")
    print(f"Binary name: {binary_name}")
    print()

    # Check if entry point exists
    if not entry_point.exists():
        print(f"Error: Entry point not found at {entry_point}")
        sys.exit(1)

    # Change to build directory
    os.chdir(build_dir)

    # Clean previous build artifacts
    print("Cleaning previous Nuitka build artifacts...")
    nuitka_build_dir = build_dir / "nuitka_build"
    if nuitka_build_dir.exists():
        shutil.rmtree(nuitka_build_dir)
    nuitka_build_dir.mkdir(exist_ok=True)
    print()

    # Prepare Nuitka command
    print("Running Nuitka compilation...")

    # Base Nuitka command
    cmd = [
        sys.executable,
        "-m", "nuitka",
        "--standalone",
        "--onefile",
        # Follow imports only for markitdown package specifically
        "--follow-import-to=markitdown",
        # Include data files for packages that need them
        "--include-package-data=magika",
        "--include-package-data=onnxruntime",
        # Don't follow imports to test modules
        "--nofollow-import-to=*.tests",
        "--nofollow-import-to=*.test",
        # Progress and download options
        "--show-progress",
        "--assume-yes-for-downloads",
        # Output configuration
        "--output-dir=" + str(nuitka_build_dir),
        # Disable LTO to speed up compilation (can be enabled later for production)
        "--lto=no",
        str(entry_point)
    ]

    # Add platform-specific options
    if plat == "darwin":
        # macOS specific options - no app bundle needed for CLI tool
        pass
    elif plat == "linux":
        # Linux specific options
        pass
    elif plat == "win32":
        # Windows specific options
        pass

    print(f"Command: {' '.join(cmd)}")
    print()

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Nuitka compilation failed with exit code {e.returncode}")
        sys.exit(1)

    print()
    print("Nuitka compilation completed successfully")
    print()

    # Find the built binary
    # Nuitka creates the binary with the same name as the entry point
    built_binary_name = "entry_point.bin" if plat != "win32" else "entry_point.exe"
    built_binary = nuitka_build_dir / built_binary_name

    # Also check for the binary without extension
    if not built_binary.exists():
        built_binary = nuitka_build_dir / "entry_point"

    # Search in subdirectories if not found
    if not built_binary.exists():
        print(f"Searching for built binary in {nuitka_build_dir}...")
        for item in nuitka_build_dir.rglob("entry_point*"):
            if item.is_file() and not item.suffix in ['.build', '.dist', '.onefile-build']:
                built_binary = item
                print(f"Found binary at: {built_binary}")
                break

    if not built_binary.exists():
        print(f"Error: Built binary not found at {built_binary}")
        print(f"Contents of {nuitka_build_dir}:")
        if nuitka_build_dir.exists():
            for item in nuitka_build_dir.iterdir():
                print(f"  - {item}")
        sys.exit(1)

    # Create output directory (separate from PyInstaller builds)
    output_dir = root_dir / "bin" / f"{plat}-nuitka"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy binary to output directory
    output_binary = output_dir / binary_name
    print(f"Copying binary to {output_binary}...")
    shutil.copy2(built_binary, output_binary)

    # Make binary executable on Unix-like systems
    if plat in ["darwin", "linux"]:
        os.chmod(output_binary, 0o755)

    # Get binary size
    size_mb = output_binary.stat().st_size / (1024 * 1024)

    print()
    print("=== Nuitka build complete ===")
    print(f"Binary location: {output_binary}")
    print(f"Binary size: {size_mb:.2f} MB")
    print()
    print("You can now test the binary with:")
    print(f"  {output_binary} --help")
    print()


if __name__ == "__main__":
    main()
