"""
Streak Manager

Core automation logic for maintaining Duolingo streaks by automatically
purchasing streak freezes when needed.

⚠️  WARNING: Automated use may violate Duolingo's Terms of Service.
    Use at your own risk.
"""

import logging
from typing import Optional
from duolingo_api import (
    DuolingoClient,
    InsufficientGemsError,
    AlreadyOwnedError,
    DuolingoAPIError,
    AuthenticationError
)
from notifications import NotificationService

logger = logging.getLogger(__name__)


class StreakManager:
    """
    Manages automatic streak freeze purchases and notifications.

    Monitors gem balance and streak freeze inventory, purchasing new
    freezes when needed and sending notifications for important events.
    """

    def __init__(
        self,
        duolingo_client: DuolingoClient,
        notification_service: Optional[NotificationService] = None,
        low_gems_threshold: int = 600,
        min_gems_required: int = 200,
        dry_run: bool = False
    ):
        """
        Initialize the Streak Manager.

        Args:
            duolingo_client: Authenticated Duolingo API client
            notification_service: Service for sending email notifications
            low_gems_threshold: Gems level to trigger low balance warning
            min_gems_required: Minimum gems needed to purchase freeze
            dry_run: If True, log actions but don't actually purchase
        """
        self.client = duolingo_client
        self.notifier = notification_service
        self.low_gems_threshold = low_gems_threshold
        self.min_gems_required = min_gems_required
        self.dry_run = dry_run

        # Track notification state to avoid spamming
        self.low_gems_notified = False
        self.out_of_gems_notified = False
        self.streak_broken_notified = False

    def check_and_maintain_streak(self) -> dict:
        """
        Main automation logic: Check status and purchase freeze if needed.

        Returns:
            Dictionary with status information:
            - success: bool
            - action_taken: str describing what happened
            - gems_remaining: int
            - has_freeze: bool
            - streak_count: int
        """
        try:
            logger.info("=" * 60)
            logger.info("Starting streak maintenance check...")
            logger.info("=" * 60)

            # Refresh user data
            self.client.refresh_data()

            # Get current status
            gem_balance = self.client.get_gem_balance()
            streak_info = self.client.get_streak_info()

            logger.info(f"Current streak: {streak_info['streak_count']} days")
            logger.info(f"Gem balance: {gem_balance}")
            logger.info(f"Has streak freeze: {streak_info['has_freeze']}")

            status = {
                "success": True,
                "action_taken": "No action needed",
                "gems_remaining": gem_balance,
                "has_freeze": streak_info["has_freeze"],
                "streak_count": streak_info["streak_count"]
            }

            # Check if we need to purchase a streak freeze
            if not streak_info["has_freeze"]:
                logger.info("No streak freeze detected. Attempting purchase...")
                purchase_result = self._purchase_freeze_if_possible(gem_balance)
                status.update(purchase_result)
            else:
                logger.info("✓ Streak freeze already equipped")
                status["action_taken"] = "Streak freeze already equipped"

                # Still check gem balance for warnings
                self._check_gem_balance_warnings(gem_balance)

            logger.info(f"Status: {status['action_taken']}")
            logger.info("=" * 60)

            return status

        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            return {
                "success": False,
                "action_taken": f"Authentication error: {e}",
                "gems_remaining": 0,
                "has_freeze": False,
                "streak_count": 0
            }

        except DuolingoAPIError as e:
            logger.error(f"API error occurred: {e}")
            if self.notifier:
                self.notifier.send_error_notification(str(e))
            return {
                "success": False,
                "action_taken": f"API error: {e}",
                "gems_remaining": 0,
                "has_freeze": False,
                "streak_count": 0
            }

    def _purchase_freeze_if_possible(self, gem_balance: int) -> dict:
        """
        Attempt to purchase a streak freeze if gems allow.

        Args:
            gem_balance: Current gem count

        Returns:
            Dictionary with purchase result details
        """
        # Check if we have enough gems
        if gem_balance < self.min_gems_required:
            logger.warning(f"⚠️  INSUFFICIENT GEMS: {gem_balance} (need {self.min_gems_required})")

            if not self.out_of_gems_notified and self.notifier:
                self.notifier.send_out_of_gems_alert(gem_balance, self.min_gems_required)
                self.out_of_gems_notified = True

            return {
                "success": False,
                "action_taken": "Insufficient gems to purchase streak freeze",
                "gems_remaining": gem_balance,
                "has_freeze": False
            }

        # We have enough gems - purchase the freeze
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would purchase streak freeze (cost: 200 gems)")
                new_balance = gem_balance - 200
                logger.info(f"[DRY RUN] New balance would be: {new_balance} gems")

                return {
                    "success": True,
                    "action_taken": "[DRY RUN] Would have purchased streak freeze",
                    "gems_remaining": new_balance,
                    "has_freeze": False  # Not really purchased
                }

            # Actually purchase the freeze
            logger.info("💎 Purchasing streak freeze...")
            self.client.purchase_streak_freeze()

            # Calculate new balance
            new_balance = gem_balance - 200
            logger.info(f"✓ Successfully purchased streak freeze!")
            logger.info(f"New gem balance: {new_balance}")

            # Send success notification
            if self.notifier:
                self.notifier.send_purchase_success(new_balance)

            # Reset notification flags on successful purchase
            self.low_gems_notified = False
            self.out_of_gems_notified = False

            # Check if new balance is low
            self._check_gem_balance_warnings(new_balance)

            return {
                "success": True,
                "action_taken": "Purchased streak freeze",
                "gems_remaining": new_balance,
                "has_freeze": True
            }

        except AlreadyOwnedError:
            logger.info("Already own maximum streak freezes (2)")
            return {
                "success": True,
                "action_taken": "Already own maximum streak freezes",
                "gems_remaining": gem_balance,
                "has_freeze": True
            }

        except InsufficientGemsError as e:
            logger.error(f"Purchase failed: {e}")
            if self.notifier and not self.out_of_gems_notified:
                self.notifier.send_out_of_gems_alert(gem_balance, self.min_gems_required)
                self.out_of_gems_notified = True

            return {
                "success": False,
                "action_taken": str(e),
                "gems_remaining": gem_balance,
                "has_freeze": False
            }

    def _check_gem_balance_warnings(self, gem_balance: int):
        """
        Check gem balance and send warning notifications if needed.

        Args:
            gem_balance: Current gem count
        """
        if gem_balance < self.min_gems_required:
            # Out of gems
            if not self.out_of_gems_notified and self.notifier:
                logger.warning(f"⚠️  OUT OF GEMS: {gem_balance}")
                self.notifier.send_out_of_gems_alert(gem_balance, self.min_gems_required)
                self.out_of_gems_notified = True

        elif gem_balance < self.low_gems_threshold:
            # Low gems warning
            if not self.low_gems_notified and self.notifier:
                logger.warning(f"⚠️  LOW GEMS WARNING: {gem_balance}")
                self.notifier.send_low_gems_warning(gem_balance, self.low_gems_threshold)
                self.low_gems_notified = True

    def check_for_broken_streak(self) -> bool:
        """
        Check if the streak has been broken.

        Returns:
            True if streak is 0 or has dropped, False otherwise
        """
        try:
            self.client.refresh_data()
            streak_info = self.client.get_streak_info()

            if streak_info["streak_count"] == 0:
                logger.error("💔 STREAK HAS BEEN BROKEN!")

                if not self.streak_broken_notified and self.notifier:
                    self.notifier.send_streak_broken_alert()
                    self.streak_broken_notified = True

                return True

            return False

        except DuolingoAPIError as e:
            logger.error(f"Failed to check streak status: {e}")
            return False

    def get_status_report(self) -> str:
        """
        Generate a human-readable status report.

        Returns:
            Formatted status string
        """
        try:
            self.client.refresh_data()
            gem_balance = self.client.get_gem_balance()
            streak_info = self.client.get_streak_info()

            report = f"""
╔══════════════════════════════════════════════════════════╗
║         DUOLINGO STREAK STATUS REPORT                     ║
╠══════════════════════════════════════════════════════════╣
║ Streak:         {streak_info['streak_count']} days
║ Streak Freeze:  {'✓ Equipped' if streak_info['has_freeze'] else '✗ Not equipped'}
║ Gem Balance:    {gem_balance} 💎
║ Status:         {'⚠️ LOW GEMS' if gem_balance < self.low_gems_threshold else '✓ Healthy'}
╚══════════════════════════════════════════════════════════╝
            """

            return report.strip()

        except DuolingoAPIError as e:
            return f"Error generating status report: {e}"
