"""Convenience script to run the Discord Message Delete Helper application.

This script simply imports and runs the main application.
It's provided as a convenience for users who prefer to run
'python run_app.py' instead of 'python src/main.py'.
"""

if __name__ == "__main__":
    from src.main import main
    import sys
    sys.exit(main())
