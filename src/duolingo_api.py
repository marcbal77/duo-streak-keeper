"""
Duolingo API Client

This module provides a client for interacting with Duolingo's unofficial API.
Based on reverse-engineered endpoints from the Duolingo web application.

⚠️  WARNING: This uses unofficial API endpoints that may change without notice.
    Use at your own risk. May violate Duolingo's Terms of Service.
"""

import requests
import logging
import time
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class DuolingoAPIError(Exception):
    """Base exception for Duolingo API errors"""
    pass


class AuthenticationError(DuolingoAPIError):
    """Raised when authentication fails"""
    pass


class InsufficientGemsError(DuolingoAPIError):
    """Raised when user doesn't have enough gems"""
    pass


class AlreadyOwnedError(DuolingoAPIError):
    """Raised when user already owns the maximum streak freezes"""
    pass


class DuolingoClient:
    """
    Client for interacting with Duolingo's API.

    Handles authentication, user data retrieval, and streak freeze purchases.
    """

    BASE_URL = "https://www.duolingo.com"
    API_VERSION = "2017-06-30"

    # Realistic browser User-Agent to avoid detection
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self, username: str, password: str):
        """
        Initialize the Duolingo client.

        Args:
            username: Duolingo username or email
            password: Duolingo password
        """
        self.username = username
        self.password = password
        self.jwt_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.user_data: Optional[Dict] = None

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Content-Type": "application/json",
        })

    def login(self) -> bool:
        """
        Authenticate with Duolingo and obtain JWT token.

        Returns:
            True if authentication successful

        Raises:
            AuthenticationError: If login fails
        """
        login_url = f"{self.BASE_URL}/login"
        payload = {
            "login": self.username,
            "password": self.password
        }

        try:
            logger.info(f"Attempting to authenticate user: {self.username}")
            response = self.session.post(login_url, json=payload, timeout=30)

            if response.status_code == 401:
                raise AuthenticationError("Invalid username or password")

            response.raise_for_status()

            # JWT token is in the response headers
            self.jwt_token = response.headers.get("jwt")

            if not self.jwt_token:
                # Sometimes it's in cookies
                jwt_cookie = self.session.cookies.get("jwt_token")
                if jwt_cookie:
                    self.jwt_token = jwt_cookie
                else:
                    raise AuthenticationError("No JWT token received from server")

            # Add JWT to session headers for future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self.jwt_token}"
            })

            # Get user data to extract user_id
            response_data = response.json()
            self.user_id = response_data.get("user_id")

            if not self.user_id:
                # Try to fetch user data to get ID
                user_info = self.get_user_data()
                self.user_id = user_info.get("id")

            logger.info(f"Successfully authenticated. User ID: {self.user_id}")
            return True

        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Login request failed: {str(e)}")

    def get_user_data(self, fields: Optional[List[str]] = None) -> Dict:
        """
        Fetch user data from Duolingo.

        Args:
            fields: Optional list of specific fields to retrieve

        Returns:
            Dictionary containing user data

        Raises:
            DuolingoAPIError: If request fails
        """
        if not self.jwt_token:
            raise AuthenticationError("Not authenticated. Call login() first.")

        # Construct API URL
        if fields:
            fields_param = ",".join(fields)
            url = f"{self.BASE_URL}/{self.API_VERSION}/users?username={self.username}&fields={fields_param}"
        else:
            # Get comprehensive user data
            url = f"{self.BASE_URL}/{self.API_VERSION}/users?username={self.username}"

        try:
            logger.debug(f"Fetching user data from: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Handle response format - sometimes wrapped in 'users' array
            if "users" in data and len(data["users"]) > 0:
                self.user_data = data["users"][0]
            else:
                self.user_data = data

            # Update user_id if we didn't have it
            if not self.user_id and "id" in self.user_data:
                self.user_id = self.user_data["id"]

            return self.user_data

        except requests.exceptions.RequestException as e:
            raise DuolingoAPIError(f"Failed to fetch user data: {str(e)}")

    def get_gem_balance(self) -> int:
        """
        Get current gem balance.

        Returns:
            Number of gems available
        """
        if not self.user_data:
            self.get_user_data()

        # Gems can be under different keys
        gems = (
            self.user_data.get("rupees") or
            self.user_data.get("lingots") or
            self.user_data.get("gems") or
            0
        )

        logger.info(f"Current gem balance: {gems}")
        return gems

    def get_streak_info(self) -> Dict:
        """
        Get current streak information.

        Returns:
            Dictionary with streak data including:
            - streak_count: Current streak length
            - has_freeze: Whether user owns a streak freeze
            - freeze_used_today: Whether freeze was used today
        """
        if not self.user_data:
            self.get_user_data()

        streak_info = {
            "streak_count": self.user_data.get("site_streak", 0),
            "has_freeze": self.user_data.get("inventory", {}).get("streak_freeze") is not None,
            "freeze_used_today": self.user_data.get("streak_extended_today", False),
        }

        logger.info(f"Streak info: {streak_info}")
        return streak_info

    def purchase_streak_freeze(self, learning_language: str = "en") -> bool:
        """
        Purchase a streak freeze with gems.

        Args:
            learning_language: Language code (e.g., 'en', 'es', 'fr')

        Returns:
            True if purchase successful

        Raises:
            InsufficientGemsError: Not enough gems
            AlreadyOwnedError: Already owns maximum streak freezes
            DuolingoAPIError: Other purchase errors
        """
        if not self.jwt_token or not self.user_id:
            raise AuthenticationError("Not authenticated. Call login() first.")

        # Check current inventory first
        streak_info = self.get_streak_info()
        if streak_info["has_freeze"]:
            logger.warning("User already owns a streak freeze")
            # May still try to purchase if Duolingo allows multiple

        # Check gem balance
        gems = self.get_gem_balance()
        if gems < 200:  # Streak freeze costs 200 gems
            raise InsufficientGemsError(f"Insufficient gems: {gems} (need 200)")

        purchase_url = f"{self.BASE_URL}/{self.API_VERSION}/users/{self.user_id}/shop-items"
        payload = {
            "itemName": "streak_freeze",
            "learningLanguage": learning_language
        }

        try:
            logger.info("Attempting to purchase streak freeze...")
            response = self.session.post(purchase_url, json=payload, timeout=30)

            # Handle specific error responses
            if response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get("message", "Unknown error")

                if "ALREADY_HAVE_STORE_ITEM" in error_msg:
                    raise AlreadyOwnedError("Already own maximum streak freezes (max 2)")
                elif "INSUFFICIENT_FUNDS" in error_msg:
                    raise InsufficientGemsError("Not enough gems to purchase streak freeze")
                else:
                    raise DuolingoAPIError(f"Purchase failed: {error_msg}")

            response.raise_for_status()

            logger.info("Successfully purchased streak freeze!")

            # Refresh user data to reflect purchase
            time.sleep(1)  # Brief pause before refreshing
            self.get_user_data()

            return True

        except requests.exceptions.RequestException as e:
            raise DuolingoAPIError(f"Purchase request failed: {str(e)}")

    def needs_streak_freeze(self) -> bool:
        """
        Check if user needs to purchase a streak freeze.

        Returns:
            True if user should purchase a freeze (doesn't have one)
        """
        streak_info = self.get_streak_info()
        return not streak_info["has_freeze"]

    def refresh_data(self):
        """Refresh user data from Duolingo API"""
        logger.debug("Refreshing user data...")
        self.get_user_data()
