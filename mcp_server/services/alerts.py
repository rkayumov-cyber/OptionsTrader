"""Alert system service."""

import uuid
from datetime import datetime
from mcp_server.models import AlertRule, AlertNotification, Market, AlertRuleType, AlertSeverity
from .storage import storage


class AlertService:
    """Alert rules and notifications management."""

    RULES_KEY = "alert_rules"
    NOTIFICATIONS_KEY = "alert_notifications"

    def __init__(self):
        self._rules: dict[str, AlertRule] = {}
        self._notifications: dict[str, AlertNotification] = {}
        self._load()

    def _load(self):
        """Load data from storage."""
        self._rules = storage.load_dict(self.RULES_KEY, AlertRule)
        self._notifications = storage.load_dict(self.NOTIFICATIONS_KEY, AlertNotification)

    def _save_rules(self):
        """Save rules to storage."""
        storage.save_dict(self.RULES_KEY, self._rules)

    def _save_notifications(self):
        """Save notifications to storage."""
        storage.save_dict(self.NOTIFICATIONS_KEY, self._notifications)

    # ===== Rule Management =====

    def get_all_rules(self) -> list[AlertRule]:
        """Get all alert rules."""
        return list(self._rules.values())

    def get_enabled_rules(self) -> list[AlertRule]:
        """Get enabled rules only."""
        return [r for r in self._rules.values() if r.enabled]

    def get_rule(self, rule_id: str) -> AlertRule | None:
        """Get rule by ID."""
        return self._rules.get(rule_id)

    def create_rule(
        self,
        symbol: str,
        market: Market,
        rule_type: AlertRuleType,
        threshold: float,
    ) -> AlertRule:
        """Create a new alert rule."""
        rule_id = str(uuid.uuid4())[:8]

        rule = AlertRule(
            id=rule_id,
            symbol=symbol.upper(),
            market=market,
            rule_type=rule_type,
            threshold=threshold,
            enabled=True,
            created_at=datetime.now(),
        )

        self._rules[rule_id] = rule
        self._save_rules()
        return rule

    def update_rule(self, rule_id: str, updates: dict) -> AlertRule | None:
        """Update an alert rule."""
        rule = self._rules.get(rule_id)
        if not rule:
            return None

        if "enabled" in updates:
            rule.enabled = updates["enabled"]
        if "threshold" in updates:
            rule.threshold = updates["threshold"]

        self._save_rules()
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            self._save_rules()
            return True
        return False

    def toggle_rule(self, rule_id: str) -> AlertRule | None:
        """Toggle rule enabled state."""
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = not rule.enabled
            self._save_rules()
        return rule

    # ===== Alert Checking =====

    def check_rule(self, rule: AlertRule, current_value: float) -> AlertNotification | None:
        """Check if a rule is triggered."""
        triggered = False

        if rule.rule_type == "price_above" and current_value > rule.threshold:
            triggered = True
        elif rule.rule_type == "price_below" and current_value < rule.threshold:
            triggered = True
        elif rule.rule_type == "iv_rank_above" and current_value > rule.threshold:
            triggered = True
        elif rule.rule_type == "iv_rank_below" and current_value < rule.threshold:
            triggered = True
        elif rule.rule_type == "volume_above" and current_value > rule.threshold:
            triggered = True
        elif rule.rule_type == "pc_ratio_above" and current_value > rule.threshold:
            triggered = True
        elif rule.rule_type == "pc_ratio_below" and current_value < rule.threshold:
            triggered = True

        if triggered:
            return self._create_notification(rule, current_value)
        return None

    def check_all_rules(self, market_data: dict[str, dict]) -> list[AlertNotification]:
        """Check all enabled rules against market data."""
        notifications = []

        for rule in self.get_enabled_rules():
            symbol_data = market_data.get(rule.symbol, {})
            current_value = None

            # Get appropriate value based on rule type
            if rule.rule_type in ["price_above", "price_below"]:
                current_value = symbol_data.get("price")
            elif rule.rule_type in ["iv_rank_above", "iv_rank_below"]:
                current_value = symbol_data.get("iv_rank")
            elif rule.rule_type == "volume_above":
                current_value = symbol_data.get("volume")
            elif rule.rule_type in ["pc_ratio_above", "pc_ratio_below"]:
                current_value = symbol_data.get("put_call_ratio")

            if current_value is not None:
                notification = self.check_rule(rule, current_value)
                if notification:
                    notifications.append(notification)

        return notifications

    def _create_notification(self, rule: AlertRule, current_value: float) -> AlertNotification:
        """Create a notification for a triggered rule."""
        notification_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        # Determine severity
        severity: AlertSeverity = "info"
        diff_percent = abs((current_value - rule.threshold) / rule.threshold * 100)
        if diff_percent > 10:
            severity = "critical"
        elif diff_percent > 5:
            severity = "warning"

        # Create message
        type_labels = {
            "price_above": "Price above",
            "price_below": "Price below",
            "iv_rank_above": "IV Rank above",
            "iv_rank_below": "IV Rank below",
            "volume_above": "Volume above",
            "pc_ratio_above": "P/C Ratio above",
            "pc_ratio_below": "P/C Ratio below",
        }
        label = type_labels.get(rule.rule_type, rule.rule_type)
        message = f"{rule.symbol}: {label} {rule.threshold} (current: {current_value:.2f})"

        notification = AlertNotification(
            id=notification_id,
            rule_id=rule.id,
            symbol=rule.symbol,
            market=rule.market,
            message=message,
            severity=severity,
            current_value=current_value,
            threshold=rule.threshold,
            triggered_at=now,
        )

        # Update rule
        rule.last_triggered = now
        rule.trigger_count += 1
        self._save_rules()

        # Save notification
        self._notifications[notification_id] = notification
        self._save_notifications()

        return notification

    # ===== Notification Management =====

    def get_all_notifications(self) -> list[AlertNotification]:
        """Get all notifications."""
        notifications = list(self._notifications.values())
        notifications.sort(key=lambda x: x.triggered_at, reverse=True)
        return notifications

    def get_unacknowledged(self) -> list[AlertNotification]:
        """Get unacknowledged notifications."""
        return [n for n in self._notifications.values() if not n.acknowledged]

    def acknowledge(self, notification_id: str) -> bool:
        """Acknowledge a notification."""
        notification = self._notifications.get(notification_id)
        if notification:
            notification.acknowledged = True
            self._save_notifications()
            return True
        return False

    def acknowledge_all(self) -> int:
        """Acknowledge all notifications."""
        count = 0
        for notification in self._notifications.values():
            if not notification.acknowledged:
                notification.acknowledged = True
                count += 1
        self._save_notifications()
        return count

    def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification."""
        if notification_id in self._notifications:
            del self._notifications[notification_id]
            self._save_notifications()
            return True
        return False

    def clear_old_notifications(self, days: int = 7) -> int:
        """Delete notifications older than X days."""
        now = datetime.now()
        to_delete = []

        for nid, notification in self._notifications.items():
            age = (now - notification.triggered_at).days
            if age > days:
                to_delete.append(nid)

        for nid in to_delete:
            del self._notifications[nid]

        if to_delete:
            self._save_notifications()

        return len(to_delete)


# Global service instance
alert_service = AlertService()
