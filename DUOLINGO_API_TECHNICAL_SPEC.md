# Duolingo API Technical Specification
## Unofficial API Documentation for Automation

**Document Version:** 1.0
**Last Updated:** November 2025
**Status:** Reverse-Engineered (Unofficial)

---

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Base URLs](#api-base-urls)
4. [User Data Endpoints](#user-data-endpoints)
5. [Streak Freeze Purchase](#streak-freeze-purchase)
6. [Error Handling](#error-handling)
7. [Rate Limiting & Security](#rate-limiting--security)
8. [Code Examples](#code-examples)

---

## Overview

Duolingo does not provide an official public API. All endpoints documented here have been reverse-engineered from mobile and web applications. The API uses JWT (JSON Web Token) authentication with Bearer token headers.

**Important Notes:**
- API endpoints may change without notice
- Excessive automation may trigger anti-bot detection
- User-Agent headers are required to avoid blocking
- The API was involved in a 2.6M user data scraping incident in 2023

---

## Authentication

### Login Endpoint

**URL:** `https://www.duolingo.com/login`
**Method:** POST
**Content-Type:** application/json

#### Request Payload

```json
{
  "login": "username_or_email",
  "password": "your_password"
}
```

#### Request Headers

```http
Content-Type: application/json
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
```

#### Response

**Status:** 200 OK

The JWT token is returned in the **response headers** (not the body):

```http
jwt: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response Body Example:**

```json
{
  "user_id": 14397890,
  "username": "user123",
  "response": "OK"
}
```

### JWT Token Management

#### Token Storage
- Extract JWT from response headers: `response.headers['jwt']`
- Store JWT for subsequent requests
- Token persists until password change
- Can be saved to file for session persistence

#### Token Usage
All authenticated requests must include:

```http
Authorization: Bearer <jwt_token>
```

#### Alternative: Extract JWT from Browser

If you're already logged in via browser:

```javascript
// Run in browser console on duolingo.com
document.cookie.match(new RegExp('(^| )jwt_token=([^;]+)'))[0].slice(11)
```

### Session Persistence

Save JWT to file to avoid repeated logins:

```python
# Session file format (JSON)
{
  "jwt_session": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Login Validation

**Endpoint:** `https://www.duolingo.com/users/{username}`
**Method:** GET

Check if JWT is valid by requesting user data. Status 200 = valid, 401/403 = invalid.

---

## API Base URLs

### Primary Endpoints
- **Main API:** `https://www.duolingo.com/`
- **Versioned API:** `https://www.duolingo.com/2017-06-30/`
- **Dictionary/Translations:** `https://d2.duolingo.com/api/1/`
- **Mobile API:** `https://android-api-cf.duolingo.com/`

### API Version
The version string `2017-06-30` appears in many endpoints but doesn't reflect actual API versioning. It's a legacy identifier still in use.

---

## User Data Endpoints

### 1. Get User Profile (Basic)

**URL:** `https://www.duolingo.com/users/{username}`
**Method:** GET
**Authentication:** Optional (more data if authenticated)

#### Response Structure (Authenticated)

```json
{
  "username": "user123",
  "id": 14397890,
  "fullname": "John Doe",
  "avatar": "https://simg-ssl.duolingo.com/avatar/abc123/large",
  "bio": "Learning Spanish!",
  "location": "New York, USA",
  "created": "2015-01-10",
  "language": "en",
  "learning_language_string": "Spanish",
  "site_streak": 365,
  "daily_goal": 50,
  "rupees": 2500,
  "lingots": 250,
  "gem_balance": 2500,
  "streak_extended_today": false,
  "has_observer": false,
  "inventory": {
    "streak_freeze": "2024-11-01 12:34:56",
    "rupee_wager": null,
    "formal_outfit": "2024-10-15 08:22:10",
    "timed_practice": "grandfathered"
  },
  "languages": [
    {
      "language_string": "Spanish",
      "language": "es",
      "level": 15,
      "points": 12450,
      "streak": 365,
      "current_learning": true
    }
  ]
}
```

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | User ID (required for shop purchases) |
| `username` | string | Display username |
| `rupees` / `gem_balance` | integer | Available gems (mobile uses gems, web uses lingots at 10:1 ratio) |
| `lingots` | integer | Available lingots (web currency) |
| `site_streak` | integer | Current global streak count |
| `streak_extended_today` | boolean | Whether streak freeze is active today |
| `inventory` | object | Owned items with purchase timestamps |
| `inventory.streak_freeze` | string/null | Timestamp if owned, null if not |

### 2. Get User Profile (Detailed)

**URL:** `https://www.duolingo.com/2017-06-30/users/{user_id}`
**Method:** GET
**Authentication:** Required

Returns more detailed information with extended fields.

### 3. Get User with Specific Fields

**URL:** `https://www.duolingo.com/2017-06-30/users?username={username}&fields={field_list}`
**Method:** GET
**Authentication:** Required

#### Example Request

```
GET https://www.duolingo.com/2017-06-30/users?username=user123&fields=streak,streakData{currentStreak,previousStreak},inventory
```

#### Response

```json
{
  "data": {
    "users": [
      {
        "streak": 365,
        "streakData": {
          "currentStreak": {
            "startDate": "2024-01-01",
            "length": 365
          },
          "previousStreak": {
            "startDate": "2023-06-15",
            "length": 120
          }
        },
        "inventory": {
          "streak_freeze": "2024-11-01 12:34:56"
        }
      }
    ]
  }
}
```

### 4. Check Gem/Lingot Balance

Extract from user profile endpoint:

```json
{
  "rupees": 2500,        // Mobile gem balance
  "lingots": 250,        // Web lingot balance
  "gem_balance": 2500    // Alternative gem field
}
```

**Conversion:** 1 Lingot = 10 Gems (approximately)

### 5. Check Streak Status

```json
{
  "site_streak": 365,                    // Global streak
  "streak_extended_today": false,        // Is freeze active?
  "inventory": {
    "streak_freeze": "2024-11-01 12:34:56"  // Owned freeze
  }
}
```

### 6. Get Streak Freeze Inventory

Check `inventory.streak_freeze`:
- **Non-null value** (timestamp): User owns a streak freeze
- **Null or missing**: No streak freeze owned
- Maximum: 2 streak freezes can be owned at once

---

## Streak Freeze Purchase

### Purchase Item Endpoint

**URL:** `https://www.duolingo.com/2017-06-30/users/{user_id}/shop-items`
**Method:** POST
**Authentication:** Required (JWT Bearer token)

#### Request Headers

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
```

#### Request Payload

```json
{
  "itemName": "streak_freeze",
  "learningLanguage": "es"
}
```

**Parameters:**
- `itemName` (string, required): The item to purchase (e.g., "streak_freeze", "rupee_wager")
- `learningLanguage` (string, required): Language abbreviation code (e.g., "es", "fr", "de", "en")

#### Success Response

**Status:** 200 OK

```json
{
  "streak_freeze": "2024-11-01 14:22:35.594327"
}
```

Returns timestamp of when the item was purchased/equipped.

#### Error Responses

##### Already Own Item

**Status:** 400 Bad Request

```json
{
  "error": "ALREADY_HAVE_STORE_ITEM",
  "message": "You already have this item equipped"
}
```

##### Insufficient Funds

**Status:** 400 Bad Request

```json
{
  "error": "INSUFFICIENT_FUNDS",
  "message": "You do not have enough gems/lingots to purchase this item"
}
```

##### Authentication Failed

**Status:** 401 Unauthorized / 403 Forbidden

```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired token"
}
```

### Streak Freeze Cost

- **Mobile App (Gems):** 200 gems
- **Web App (Lingots):** 10 lingots
- **Equivalence:** ~200 gems = 10 lingots

### Purchase Flow Diagram

```
┌─────────────────────┐
│ Start               │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Get User Data       │
│ (Check Balance)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Check Inventory     │
│ for streak_freeze   │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
  Owned        Not Owned
    │             │
    │             ▼
    │    ┌───────────────────┐
    │    │ Check Gem Balance │
    │    │ >= 200 gems?      │
    │    └────────┬──────────┘
    │             │
    │      ┌──────┴──────┐
    │      │             │
    │      ▼             ▼
    │    Yes            No
    │      │             │
    │      ▼             │
    │ ┌─────────────────┐│
    │ │ POST to shop-   ││
    │ │ items endpoint  ││
    │ └────────┬────────┘│
    │          │         │
    │     ┌────┴────┐    │
    │     │         │    │
    │     ▼         ▼    ▼
    │  Success   Error  Skip
    │     │         │    │
    │     ▼         ▼    ▼
    └────►┌───────────────┐
          │ Return Status │
          └───────────────┘
```

### Get Shop Items

**URL:** `https://www.duolingo.com/api/1/store/get_items`
**Method:** GET
**Authentication:** Required

#### Response

```json
{
  "shopItems": [
    {
      "name": "streak_freeze",
      "price": 10,
      "currency": "lingots",
      "description": "Protect your streak if you miss a day"
    },
    {
      "name": "rupee_wager",
      "price": 5,
      "currency": "lingots",
      "description": "Double or nothing on your daily XP goal"
    }
  ]
}
```

---

## Error Handling

### Exception Types

```python
class DuolingoException(Exception):
    """Base exception for all Duolingo API errors"""
    pass

class CaptchaException(DuolingoException):
    """Raised when captcha/bot detection triggered"""
    pass

class AlreadyHaveStoreItemException(DuolingoException):
    """User already owns the item"""
    pass

class InsufficientFundsException(DuolingoException):
    """Not enough gems/lingots"""
    pass

class OtherUserException(DuolingoException):
    """Operation not allowed for this user"""
    pass
```

### HTTP Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | Parse response data |
| 400 | Bad request | Check error field for specific reason |
| 401 | Unauthorized | Re-authenticate (JWT invalid) |
| 403 | Forbidden | Check for captcha/bot detection |
| 404 | Not found | User or resource doesn't exist |
| 429 | Rate limited | Back off and retry with delay |
| 500 | Server error | Retry with exponential backoff |

### Detecting Captcha/Bot Block

**Response Status:** 403 Forbidden

**Response Body:**

```json
{
  "blockScript": true,
  "redirect": "/captcha"
}
```

**Common Triggers:**
- User-Agent contains "python", "bot", "curl"
- Too many requests in short time window
- Suspicious access patterns
- Multiple failed login attempts

---

## Rate Limiting & Security

### Rate Limiting

Duolingo implements rate limiting but exact limits are not documented:

- **Recommendation:** Max 1 request per minute for automation
- **Monitoring:** Check for 429 status codes
- **Backoff Strategy:** Exponential backoff on failures

### Anti-Bot Detection

#### Blocked User-Agents
Avoid these strings in User-Agent:
- "python"
- "bot"
- "curl"
- "wget"
- "scraper"

#### Recommended User-Agent

```
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
```

Or use a more recent version:

```
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

### Security Best Practices

1. **Never hardcode credentials** - Use environment variables
2. **Store JWT securely** - Use encrypted storage or system keychain
3. **Implement request throttling** - Add delays between requests
4. **Handle errors gracefully** - Don't retry indefinitely on 403
5. **Rotate User-Agents** - Use multiple realistic user-agent strings
6. **Monitor for API changes** - Endpoints may change without notice

### Known Security Issues

- **2023 Data Scraping:** 2.6M users' data was scraped and sold
- **API Abuse:** Duolingo has implemented stricter rate limiting since then
- **Purchase Exploit (2019):** Setting `isFree: true` in purchase requests bypassed costs (now patched)

---

## Code Examples

### Python Implementation (Using requests)

#### Full Authentication & Purchase Example

```python
import requests
import json
from typing import Optional, Dict, Any

class DuolingoAPI:
    BASE_URL = "https://www.duolingo.com"
    API_VERSION = "2017-06-30"

    def __init__(self, username: str = None, password: str = None, jwt: str = None):
        self.username = username
        self.jwt = jwt
        self.user_id = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
        })

        if jwt:
            self._set_jwt(jwt)
        elif username and password:
            self.login(username, password)

    def _set_jwt(self, jwt: str):
        """Set JWT token for authentication"""
        self.jwt = jwt
        self.session.headers.update({
            'Authorization': f'Bearer {jwt}'
        })

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with Duolingo

        Args:
            username: Duolingo username or email
            password: Account password

        Returns:
            Dict containing user_id and username

        Raises:
            requests.HTTPError: If login fails
        """
        url = f"{self.BASE_URL}/login"
        payload = {
            "login": username,
            "password": password
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()

        # Extract JWT from response headers
        if 'jwt' in response.headers:
            self._set_jwt(response.headers['jwt'])

        data = response.json()
        self.user_id = data.get('user_id')
        self.username = data.get('username')

        return data

    def get_user_info(self, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user profile information

        Args:
            username: Username to query (defaults to authenticated user)

        Returns:
            User data dictionary
        """
        username = username or self.username
        url = f"{self.BASE_URL}/users/{username}"

        response = self.session.get(url)
        response.raise_for_status()

        return response.json()

    def get_streak_info(self) -> Dict[str, Any]:
        """
        Get current streak information

        Returns:
            Dict with streak count and status
        """
        user_data = self.get_user_info()

        return {
            'streak': user_data.get('site_streak', 0),
            'extended_today': user_data.get('streak_extended_today', False),
            'has_freeze': user_data.get('inventory', {}).get('streak_freeze') is not None
        }

    def get_gem_balance(self) -> int:
        """
        Get current gem/lingot balance

        Returns:
            Current gem balance
        """
        user_data = self.get_user_info()

        # Try multiple fields (API uses different names)
        return (
            user_data.get('gem_balance') or
            user_data.get('rupees') or
            user_data.get('lingots', 0) * 10  # Convert lingots to gems
        )

    def get_learning_language(self) -> str:
        """
        Get current learning language abbreviation

        Returns:
            Language code (e.g., 'es', 'fr', 'de')
        """
        user_data = self.get_user_info()
        languages = user_data.get('languages', [])

        for lang in languages:
            if lang.get('current_learning'):
                return lang.get('language')

        # Fallback to first language
        return languages[0].get('language') if languages else 'es'

    def buy_item(self, item_name: str, learning_language: str) -> Dict[str, Any]:
        """
        Purchase an item from the shop

        Args:
            item_name: Name of item (e.g., 'streak_freeze')
            learning_language: Language code (e.g., 'es')

        Returns:
            Purchase confirmation with timestamp

        Raises:
            AlreadyHaveStoreItemException: If item already owned
            InsufficientFundsException: If not enough gems
            requests.HTTPError: For other API errors
        """
        if not self.user_id:
            user_data = self.get_user_info()
            self.user_id = user_data['id']

        url = f"{self.BASE_URL}/{self.API_VERSION}/users/{self.user_id}/shop-items"
        payload = {
            "itemName": item_name,
            "learningLanguage": learning_language
        }

        response = self.session.post(url, json=payload)

        if response.status_code == 400:
            error_data = response.json()
            error_code = error_data.get('error', '')

            if error_code == 'ALREADY_HAVE_STORE_ITEM':
                raise AlreadyHaveStoreItemException("Item already equipped")
            elif error_code == 'INSUFFICIENT_FUNDS':
                raise InsufficientFundsException("Not enough gems/lingots")

        response.raise_for_status()
        return response.json()

    def buy_streak_freeze(self) -> bool:
        """
        Purchase a streak freeze

        Returns:
            True if purchased successfully, False if already owned

        Raises:
            InsufficientFundsException: If not enough gems
        """
        lang = self.get_learning_language()

        try:
            result = self.buy_item('streak_freeze', lang)
            print(f"Streak freeze purchased: {result}")
            return True
        except AlreadyHaveStoreItemException:
            print("Already have streak freeze equipped")
            return False

    def save_session(self, filepath: str):
        """Save JWT to file for session persistence"""
        with open(filepath, 'w') as f:
            json.dump({'jwt_session': self.jwt}, f)

    def load_session(self, filepath: str):
        """Load JWT from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            self._set_jwt(data['jwt_session'])


class AlreadyHaveStoreItemException(Exception):
    pass

class InsufficientFundsException(Exception):
    pass


# Example Usage
if __name__ == "__main__":
    # Method 1: Login with credentials
    api = DuolingoAPI(username="your_username", password="your_password")

    # Method 2: Use existing JWT
    # api = DuolingoAPI(jwt="your_jwt_token_here")

    # Check streak status
    streak_info = api.get_streak_info()
    print(f"Current streak: {streak_info['streak']} days")
    print(f"Freeze active: {streak_info['extended_today']}")
    print(f"Has freeze: {streak_info['has_freeze']}")

    # Check gem balance
    gems = api.get_gem_balance()
    print(f"Gem balance: {gems}")

    # Purchase streak freeze if needed
    if not streak_info['has_freeze'] and gems >= 200:
        try:
            success = api.buy_streak_freeze()
            if success:
                print("Successfully purchased streak freeze!")
        except InsufficientFundsException:
            print("Not enough gems to purchase streak freeze")

    # Save session for later use
    api.save_session('duolingo_session.json')
```

### Automation Script with Error Handling

```python
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DuolingoStreakBot:
    def __init__(self, username: str, password: str):
        self.api = DuolingoAPI(username=username, password=password)
        self.max_retries = 3
        self.retry_delay = 60  # seconds

    def ensure_streak_freeze(self) -> bool:
        """
        Ensure user has a streak freeze equipped

        Returns:
            True if freeze is equipped, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                streak_info = self.api.get_streak_info()

                if streak_info['has_freeze']:
                    logger.info("Streak freeze already equipped")
                    return True

                # Check if we have enough gems
                gems = self.api.get_gem_balance()
                if gems < 200:
                    logger.warning(f"Insufficient gems: {gems} (need 200)")
                    return False

                # Attempt purchase
                logger.info("Attempting to purchase streak freeze...")
                success = self.api.buy_streak_freeze()

                if success:
                    logger.info("Successfully purchased streak freeze!")
                    return True

                return False

            except AlreadyHaveStoreItemException:
                logger.info("Streak freeze already equipped")
                return True

            except InsufficientFundsException:
                logger.error("Not enough gems to purchase streak freeze")
                return False

            except requests.HTTPError as e:
                if e.response.status_code == 403:
                    logger.error("Bot detection triggered - stopping")
                    return False
                elif e.response.status_code == 429:
                    logger.warning(f"Rate limited - retrying in {self.retry_delay}s")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"HTTP error: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

        return False

    def run(self):
        """Main bot execution"""
        logger.info(f"Starting Duolingo Streak Bot at {datetime.now()}")

        try:
            result = self.ensure_streak_freeze()

            if result:
                logger.info("Streak freeze is equipped - streak is protected!")
            else:
                logger.warning("Could not ensure streak freeze is equipped")

        except Exception as e:
            logger.error(f"Bot failed: {e}")


# Usage
if __name__ == "__main__":
    import os

    username = os.environ.get('DUOLINGO_USERNAME')
    password = os.environ.get('DUOLINGO_PASSWORD')

    if not username or not password:
        raise ValueError("Set DUOLINGO_USERNAME and DUOLINGO_PASSWORD environment variables")

    bot = DuolingoStreakBot(username, password)
    bot.run()
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

class DuolingoAPI {
  constructor(username = null, password = null, jwt = null) {
    this.baseURL = 'https://www.duolingo.com';
    this.apiVersion = '2017-06-30';
    this.username = username;
    this.jwt = jwt;
    this.userId = null;

    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/json'
      }
    });

    if (jwt) {
      this.setJWT(jwt);
    } else if (username && password) {
      this.login(username, password);
    }
  }

  setJWT(jwt) {
    this.jwt = jwt;
    this.client.defaults.headers['Authorization'] = `Bearer ${jwt}`;
  }

  async login(username, password) {
    try {
      const response = await this.client.post('/login', {
        login: username,
        password: password
      });

      // Extract JWT from response headers
      if (response.headers['jwt']) {
        this.setJWT(response.headers['jwt']);
      }

      this.userId = response.data.user_id;
      this.username = response.data.username;

      return response.data;
    } catch (error) {
      throw new Error(`Login failed: ${error.message}`);
    }
  }

  async getUserInfo(username = null) {
    username = username || this.username;
    const response = await this.client.get(`/users/${username}`);
    return response.data;
  }

  async getStreakInfo() {
    const userData = await this.getUserInfo();

    return {
      streak: userData.site_streak || 0,
      extendedToday: userData.streak_extended_today || false,
      hasFreeze: userData.inventory?.streak_freeze != null
    };
  }

  async getGemBalance() {
    const userData = await this.getUserInfo();
    return userData.gem_balance || userData.rupees || (userData.lingots * 10) || 0;
  }

  async getLearningLanguage() {
    const userData = await this.getUserInfo();
    const languages = userData.languages || [];

    const currentLang = languages.find(lang => lang.current_learning);
    return currentLang?.language || languages[0]?.language || 'es';
  }

  async buyItem(itemName, learningLanguage) {
    if (!this.userId) {
      const userData = await this.getUserInfo();
      this.userId = userData.id;
    }

    try {
      const response = await this.client.post(
        `/${this.apiVersion}/users/${this.userId}/shop-items`,
        {
          itemName: itemName,
          learningLanguage: learningLanguage
        }
      );

      return response.data;
    } catch (error) {
      if (error.response?.status === 400) {
        const errorCode = error.response.data?.error;

        if (errorCode === 'ALREADY_HAVE_STORE_ITEM') {
          throw new Error('Already have this item');
        } else if (errorCode === 'INSUFFICIENT_FUNDS') {
          throw new Error('Not enough gems/lingots');
        }
      }
      throw error;
    }
  }

  async buyStreakFreeze() {
    const lang = await this.getLearningLanguage();

    try {
      const result = await this.buyItem('streak_freeze', lang);
      console.log('Streak freeze purchased:', result);
      return true;
    } catch (error) {
      if (error.message === 'Already have this item') {
        console.log('Already have streak freeze');
        return false;
      }
      throw error;
    }
  }
}

// Example usage
(async () => {
  const api = new DuolingoAPI('username', 'password');

  // Or use existing JWT
  // const api = new DuolingoAPI(null, null, 'your_jwt_token');

  const streakInfo = await api.getStreakInfo();
  console.log(`Current streak: ${streakInfo.streak} days`);
  console.log(`Has freeze: ${streakInfo.hasFreeze}`);

  if (!streakInfo.hasFreeze) {
    const gems = await api.getGemBalance();
    console.log(`Gem balance: ${gems}`);

    if (gems >= 200) {
      await api.buyStreakFreeze();
    }
  }
})();
```

### cURL Examples

#### Login

```bash
curl -X POST https://www.duolingo.com/login \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  -d '{"login":"username","password":"password"}' \
  -i
```

Extract JWT from response headers.

#### Get User Info

```bash
curl -X GET https://www.duolingo.com/users/username \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
```

#### Purchase Streak Freeze

```bash
curl -X POST https://www.duolingo.com/2017-06-30/users/14397890/shop-items \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  -d '{"itemName":"streak_freeze","learningLanguage":"es"}'
```

---

## Additional Resources

### GitHub Repositories (Reference Implementations)

1. **KartikTalwar/Duolingo** (Python)
   - https://github.com/KartikTalwar/Duolingo
   - Most popular Python implementation
   - Last active: 2021 (may be outdated)

2. **alexsanjoseph/duolingo-save-streak** (Python)
   - https://github.com/alexsanjoseph/duolingo-save-streak
   - AWS Lambda-ready automation script

3. **JoshLintag/Duolingo-Streak-Freezer** (Python)
   - https://github.com/JoshLintag/Duolingo-Streak-Freezer
   - Simple streak freeze automation

4. **Michael1337/duolingo-autostreak** (Node.js)
   - https://github.com/Michael1337/duolingo-autostreak
   - Dockerized Node.js solution
   - Updated March 2024

5. **igorskh/duolingo-api** (OpenAPI Spec)
   - https://github.com/igorskh/duolingo-api
   - Swagger/OpenAPI 2.0 definition

### Unofficial Documentation

- **tschuy.com API Docs:** https://tschuy.com/duolingo/api/endpoints.html
- **Duolingo Forum:** https://forum.duome.eu/viewtopic.php?t=25167

---

## Changelog & Updates

### Known Changes
- **2023:** Stricter rate limiting after data scraping incident
- **2021:** Login endpoint requires newer authentication flow
- **2019:** Purchase exploit patched (isFree bypass)

### Monitoring for Changes
The API can change without notice. Monitor these indicators:
- GitHub issues in reference repositories
- HTTP 404 errors on previously working endpoints
- Changes in response JSON structure
- New error codes in 400 responses

---

## Disclaimer

This documentation is for educational purposes only. The Duolingo API is not officially documented or supported. Use at your own risk. Excessive automation may violate Duolingo's Terms of Service and result in account suspension.

**Recommendations:**
1. Use automation sparingly (once per day max)
2. Add random delays to mimic human behavior
3. Don't share or sell access to your implementation
4. Respect Duolingo's systems and other users
5. Consider using official Duolingo features instead of automation

---

**Document End**
