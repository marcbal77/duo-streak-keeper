#!/usr/bin/env python3
"""
Duo Streak Keeper - Main Entry Point

Automatically maintains your Duolingo streak by purchasing streak freezes when needed.

Usage:
    python main.py              # Run once
    python main.py --dry-run    # Test mode (no purchases)
    python main.py --status     # Show current status only
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

from src.duolingo_api import (
    DuolingoClient,
    AuthenticationError,
    DuolingoAPIError
)
from src.streak_manager import StreakManager
from src.notifications import NotificationService


def setup_logging(log_level="INFO"):
    """Configure logging to console and file"""
    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('duo-streak-keeper.log')
        ]
    )


def load_config():
    """Load configuration from environment variables"""
    load_dotenv()

    config = {
        'duolingo_username': os.getenv('DUOLINGO_USERNAME'),
        'duolingo_password': os.getenv('DUOLINGO_PASSWORD'),
        'smtp_host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'smtp_username': os.getenv('SMTP_USERNAME'),
        'smtp_password': os.getenv('SMTP_PASSWORD'),
        'notification_email': os.getenv('NOTIFICATION_EMAIL'),
        'low_gems_threshold': int(os.getenv('LOW_GEMS_THRESHOLD', '600')),
        'min_gems_required': int(os.getenv('MIN_GEMS_REQUIRED', '200')),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    }

    # Validate required fields
    if not config['duolingo_username'] or not config['duolingo_password']:
        print("ERROR: DUOLINGO_USERNAME and DUOLINGO_PASSWORD are required.")
        print("Please create a .env file based on .env.example")
        sys.exit(1)

    return config


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Automatically maintain your Duolingo streak'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode - no actual purchases will be made'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current streak status and exit'
    )
    parser.add_argument(
        '--no-email',
        action='store_true',
        help='Disable email notifications'
    )
    args = parser.parse_args()

    # Load configuration
    config = load_config()
    setup_logging(config['log_level'])
    logger = logging.getLogger(__name__)

    logger.info("Starting Duo Streak Keeper...")

    if args.dry_run:
        logger.info("DRY RUN MODE - No purchases will be made")

    try:
        # Initialize Duolingo client
        logger.info("Authenticating with Duolingo...")
        client = DuolingoClient(
            config['duolingo_username'],
            config['duolingo_password']
        )

        client.login()

        # Initialize notification service (if configured)
        notifier = None
        if not args.no_email and config['smtp_username'] and config['notification_email']:
            notifier = NotificationService(
                smtp_host=config['smtp_host'],
                smtp_port=config['smtp_port'],
                smtp_username=config['smtp_username'],
                smtp_password=config['smtp_password'],
                recipient_email=config['notification_email'],
                enabled=True
            )
            logger.info("Email notifications enabled")
        else:
            logger.info("Email notifications disabled")

        # Initialize streak manager
        manager = StreakManager(
            duolingo_client=client,
            notification_service=notifier,
            low_gems_threshold=config['low_gems_threshold'],
            min_gems_required=config['min_gems_required'],
            dry_run=args.dry_run
        )

        # Show status if requested
        if args.status:
            print("\n" + manager.get_status_report())
            return

        # Run the main check and maintenance
        result = manager.check_and_maintain_streak()

        # Print summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Status: {'✓ Success' if result['success'] else '✗ Failed'}")
        print(f"Action: {result['action_taken']}")
        print(f"Streak: {result['streak_count']} days")
        print(f"Freeze: {'✓ Equipped' if result['has_freeze'] else '✗ Not equipped'}")
        print(f"Gems: {result['gems_remaining']}")
        print("="*60)

        if not result['success']:
            sys.exit(1)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        print(f"\nERROR: Could not login to Duolingo")
        print(f"Check your DUOLINGO_USERNAME and DUOLINGO_PASSWORD in .env")
        sys.exit(1)

    except DuolingoAPIError as e:
        logger.error(f"API error: {e}")
        print(f"\nERROR: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nStopped by user")
        sys.exit(0)

    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
