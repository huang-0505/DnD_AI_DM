#!/usr/bin/env python3
"""
CLI tool for running CI/CD operations locally.
Mimics the GitHub Actions pipeline for local development and testing.

Usage:
    python cli.py [command] [options]

Commands:
    build       - Build the Docker test image
    lint        - Run linting and formatting checks
    test        - Run tests (unit, integration, system, or all)
    coverage    - Generate coverage reports
    ci          - Run full CI pipeline locally
    help        - Show this help message

Examples:
    python cli.py build
    python cli.py lint
    python cli.py test unit
    python cli.py test integration
    python cli.py test system
    python cli.py test all
    python cli.py coverage
    python cli.py ci
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Project configuration
PROJECT_ROOT = Path(__file__).parent.absolute()
DOCKERFILE = PROJECT_ROOT / "tests" / "Dockerfile"
IMAGE_NAME = "dnd-test-runner"
IMAGE_TAG = "local"


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command and return the result."""
    print(f"🔧 Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        check=check,
        capture_output=capture_output,
        text=True
    )
    if capture_output:
        return result.stdout.strip()
    return result


def build_image():
    """Build the Docker test image."""
    print("📦 Building Docker test image...")
    cmd = [
        "docker", "build",
        "-t", f"{IMAGE_NAME}:{IMAGE_TAG}",
        "-f", str(DOCKERFILE),
        str(PROJECT_ROOT)
    ]
    run_command(cmd)
    print("✅ Docker image built successfully!")


def run_lint():
    """Run linting and formatting checks."""
    print("🔍 Running linting and formatting checks...")
    
    # Check Black formatting
    print("\n📝 Checking code formatting with Black...")
    cmd = [
        "docker", "run", "--rm",
        f"{IMAGE_NAME}:{IMAGE_TAG}",
        "uv", "run", "--directory", "/app/tests",
        "black", "--check", "--line-length", "120", "src/"
    ]
    try:
        run_command(cmd)
        print("✅ Black formatting check passed!")
    except subprocess.CalledProcessError:
        print("❌ Black formatting check failed!")
        print("💡 Run 'python cli.py format' to auto-fix formatting issues")
        return False
    
    # Run Flake8 linter
    print("\n🔎 Running Flake8 linter...")
    cmd = [
        "docker", "run", "--rm",
        f"{IMAGE_NAME}:{IMAGE_TAG}",
        "uv", "run", "--directory", "/app/tests",
        "flake8", "--max-line-length=120", "--extend-ignore=E203,W503,E501", "src/"
    ]
    try:
        run_command(cmd)
        print("✅ Flake8 linting passed!")
    except subprocess.CalledProcessError:
        print("⚠️  Flake8 found some issues (non-blocking)")
    
    return True


def format_code():
    """Auto-format code with Black."""
    print("🎨 Auto-formatting code with Black...")
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{PROJECT_ROOT}/src:/app/src",
        f"{IMAGE_NAME}:{IMAGE_TAG}",
        "uv", "run", "--directory", "/app/tests",
        "black", "--line-length", "120", "src/"
    ]
    run_command(cmd)
    print("✅ Code formatted successfully!")


def run_tests(test_type="all"):
    """Run tests based on type."""
    test_types = {
        "unit": ("tests/unit/", "-m unit"),
        "integration": ("tests/integration/", "-m integration"),
        "system": ("tests/system/", "-m system"),
        "all": ("tests/unit/ tests/integration/", "")
    }
    
    if test_type not in test_types:
        print(f"❌ Unknown test type: {test_type}")
        print(f"Available types: {', '.join(test_types.keys())}")
        return False
    
    test_path, marker = test_types[test_type]
    
    print(f"🧪 Running {test_type} tests...")
    
    if test_type == "system":
        # System tests require a running server
        print("⚠️  System tests require a running server.")
        print("💡 Starting server container...")
        
        # Start server
        server_cmd = [
            "docker", "run", "-d",
            "--name", "api-server",
            "-p", "9000:9000",
            "-e", "DEV=1",
            "-e", "GCP_PROJECT=test-project",
            "-e", "OPENAI_API_KEY=test-key",
            f"{IMAGE_NAME}:{IMAGE_TAG}",
            "uv", "run", "--directory", "/app/tests",
            "uvicorn", "src.orchestrator.app:app", "--host", "0.0.0.0", "--port", "9000"
        ]
        
        try:
            run_command(server_cmd)
            print("⏳ Waiting for server to start...")
            import time
            time.sleep(10)
            
            # Run tests with host network
            test_cmd = [
                "docker", "run", "--rm", "--network", "host",
                f"{IMAGE_NAME}:{IMAGE_TAG}",
                "uv", "run", "--directory", "/app/tests",
                "pytest", test_path, "-v", "--tb=short", marker
            ]
            run_command(test_cmd)
            
        finally:
            # Cleanup
            print("🧹 Cleaning up server container...")
            subprocess.run(["docker", "stop", "api-server"], capture_output=True)
            subprocess.run(["docker", "rm", "api-server"], capture_output=True)
    else:
        # Unit and integration tests
        cmd = [
            "docker", "run", "--rm",
            f"{IMAGE_NAME}:{IMAGE_TAG}",
            "uv", "run", "--directory", "/app/tests",
            "pytest", test_path, "-v", "--tb=short", marker
        ]
        run_command(cmd)
    
    print(f"✅ {test_type.capitalize()} tests passed!")
    return True


def generate_coverage():
    """Generate coverage reports."""
    print("📊 Generating coverage report...")
    
    # Create coverage directory
    coverage_dir = PROJECT_ROOT / "htmlcov"
    coverage_dir.mkdir(exist_ok=True)
    
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{coverage_dir}:/app/htmlcov",
        "-v", f"{PROJECT_ROOT}/coverage.xml:/app/coverage.xml",
        f"{IMAGE_NAME}:{IMAGE_TAG}",
        "uv", "run", "--directory", "/app/tests",
        "pytest", "tests/unit/",
        "--cov=src/backend/api",
        "--cov=src/rule_agent",
        "--cov=src/orchestrator",
        "--cov-report=term",
        "--cov-report=xml:coverage.xml",
        "--cov-report=html:htmlcov"
    ]
    
    try:
        run_command(cmd)
        print("✅ Coverage report generated!")
        print(f"📁 HTML report: {coverage_dir}/index.html")
        print(f"📁 XML report: {PROJECT_ROOT}/coverage.xml")
    except subprocess.CalledProcessError:
        print("⚠️  Coverage generation completed with warnings")


def run_full_ci():
    """Run the full CI pipeline locally."""
    print("🚀 Running full CI pipeline locally...\n")
    
    steps = [
        ("Building Docker image", build_image),
        ("Running linting checks", run_lint),
        ("Running unit tests", lambda: run_tests("unit")),
        ("Running integration tests", lambda: run_tests("integration")),
        ("Generating coverage report", generate_coverage),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"Step: {step_name}")
        print(f"{'='*60}\n")
        try:
            step_func()
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Step '{step_name}' failed!")
            print(f"Error: {e}")
            sys.exit(1)
    
    print(f"\n{'='*60}")
    print("✅ All CI checks passed!")
    print(f"{'='*60}\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CLI tool for running CI/CD operations locally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "command",
        choices=["build", "lint", "format", "test", "coverage", "ci", "help"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--test-type",
        choices=["unit", "integration", "system", "all"],
        default="all",
        help="Type of tests to run (for 'test' command)"
    )
    
    args = parser.parse_args()
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not installed or not available in PATH")
        print("💡 Please install Docker to use this CLI tool")
        sys.exit(1)
    
    # Execute command
    if args.command == "help":
        parser.print_help()
    elif args.command == "build":
        build_image()
    elif args.command == "lint":
        success = run_lint()
        sys.exit(0 if success else 1)
    elif args.command == "format":
        format_code()
    elif args.command == "test":
        success = run_tests(args.test_type)
        sys.exit(0 if success else 1)
    elif args.command == "coverage":
        generate_coverage()
    elif args.command == "ci":
        run_full_ci()


if __name__ == "__main__":
    main()

