"""
Alert routing — dispatches violation notifications to configured channels.

Supported channels:
- stdout (always available, for demo/CI)
- PostgreSQL (via ViolationStore)
- Slack (via webhook URL)
- Email (via SMTP)

Usage:
    router = AlertRouter()
    router.register_channel("stdout", enabled=True)
    router.register_channel("slack", enabled=True, webhook_url="https://hooks.slack.com/...")
    router.route(violation)
    router.route_batch(violations)
"""
from __future__ import annotations
import json
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from streamdq.rules.base import Violation


@dataclass
class Alert:
    """An alert to be dispatched."""
    violation: Violation
    channel: str
    message: str
    severity: str
    rule_id: str
    entity_id: str


class AlertChannel:
    """Base class for alert channels."""

    def __init__(self, name: str, enabled: bool = True, **kwargs):
        self.name = name
        self.enabled = enabled
        self.config = kwargs

    def send(self, alert: Alert) -> bool:
        """Send an alert. Returns True on success."""
        raise NotImplementedError

    def format_message(self, violation: Violation) -> str:
        """Format a violation as a human-readable alert message."""
        return (
            f"[{violation.severity}] {violation.rule_id} — {violation.rule_name}\n"
            f"Entity: {violation.entity_type}:{violation.entity_id}\n"
            f"Type: {violation.violation_type}\n"
            f"Details: {json.dumps(violation.details, indent=2)}\n"
            f"Detected: {violation.detected_at}\n"
            f"Latency: {violation.processing_latency_ms:.2f}ms"
        )


class StdoutChannel(AlertChannel):
    """Print alerts to stdout (demo/CI)."""

    def send(self, alert: Alert) -> bool:
        if not self.enabled:
            return True
        print(f"[ALERT-{alert.channel.upper()}] {alert.message}")
        return True


class SlackChannel(AlertChannel):
    """Send alerts to Slack via webhook."""

    def send(self, alert: Alert) -> bool:
        if not self.enabled:
            return True
        webhook_url = self.config.get("webhook_url")
        if not webhook_url:
            print(f"[AlertRouter] Slack webhook URL not configured, skipping alert")
            return False

        payload = {
            "text": f":warning: *{alert.severity}* Violation: `{alert.rule_id}`",
            "attachments": [
                {
                    "color": self._severity_color(alert.severity),
                    "fields": [
                        {"title": "Entity", "value": f"{alert.violation.entity_type}:{alert.entity_id}", "short": True},
                        {"title": "Rule", "value": alert.rule_id, "short": True},
                        {"title": "Type", "value": alert.violation.violation_type, "short": True},
                        {"title": "Latency", "value": f"{alert.violation.processing_latency_ms:.2f}ms", "short": True},
                    ],
                    "text": alert.message,
                }
            ],
        }

        try:
            import urllib.request
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[AlertRouter] Slack send failed: {e}")
            return False

    @staticmethod
    def _severity_color(severity: str) -> str:
        return {
            "CRITICAL": "#ff0000",
            "HIGH": "#ff8800",
            "MEDIUM": "#ffcc00",
            "LOW": "#00aa00",
        }.get(severity, "#888888")


class EmailChannel(AlertChannel):
    """Send alerts via email."""

    def send(self, alert: Alert) -> bool:
        if not self.enabled:
            return True
        smtp_host = self.config.get("smtp_host", "localhost")
        smtp_port = self.config.get("smtp_port", 587)
        from_addr = self.config.get("from_addr", "streamdq@example.com")
        to_addrs = self.config.get("to_addrs", [])

        if not to_addrs:
            print(f"[AlertRouter] No email recipients configured, skipping alert")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{alert.severity}] StreamDQ Violation: {alert.rule_id}"
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        msg.attach(MIMEText(alert.message, "plain"))

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.sendmail(from_addr, to_addrs, msg.as_string())
            return True
        except Exception as e:
            print(f"[AlertRouter] Email send failed: {e}")
            return False


class AlertRouter:
    """
    Route violations to configured alert channels.

    Supports:
    - Deduplication: suppress repeated alerts on the same (rule_id, entity_id) within a time window
    - Severity threshold: only alert for violations above the configured severity level
    - Multiple channels: stdout, Slack, email

    Usage:
        router = AlertRouter()
        router.register_channel("stdout")
        router.register_channel("slack", webhook_url="https://hooks.slack.com/...")
        router.route(violation)
        router.route_batch(violations)
    """

    SEVERITY_THRESHOLD = "MEDIUM"  # Only alert for MEDIUM and above

    def __init__(self, severity_threshold: str = "MEDIUM", dedup_window_seconds: int = 300, confidence_threshold: float = 0.7):
        self._channels: dict[str, AlertChannel] = {}
        self.severity_threshold = severity_threshold
        self.confidence_threshold = confidence_threshold
        self._severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        # NG-16: Deduplication state — { (rule_id, entity_id, entity_type): last_alert_time }
        self._recent_alerts: dict[tuple, datetime] = {}
        self._dedup_window = timedelta(seconds=dedup_window_seconds)

    def register_channel(self, channel_type: str, enabled: bool = True, **kwargs) -> None:
        """Register an alert channel."""
        if channel_type == "stdout":
            self._channels["stdout"] = StdoutChannel("stdout", enabled)
        elif channel_type == "slack":
            self._channels["slack"] = SlackChannel("slack", enabled, **kwargs)
        elif channel_type == "email":
            self._channels["email"] = EmailChannel("email", enabled, **kwargs)
        else:
            raise ValueError(f"Unknown channel type: {channel_type}")

    def _is_duplicate(self, violation: Violation) -> bool:
        """
        NG-16: Check if this violation is a duplicate within the dedup window.

        Duplicates are defined as violations on the same (rule_id, entity_id, entity_type)
        within the configured time window.
        """
        key = (violation.rule_id, str(violation.entity_id), violation.entity_type)
        now = datetime.now()
        if key in self._recent_alerts:
            last_time = self._recent_alerts[key]
            if (now - last_time).total_seconds() < self._dedup_window.total_seconds():
                return True
        self._recent_alerts[key] = now
        # Evict old entries periodically
        cutoff = now - self._dedup_window * 2
        for k, t in list(self._recent_alerts.items()):
            if t < cutoff:
                del self._recent_alerts[k]
        return False

    def should_route(self, violation: Violation) -> bool:
        """
        Determine if violation should be routed to downstream systems.

        Filters based on:
        1. Confidence threshold (for CRS003 and other confidence-scored rules)
        2. Severity level
        3. Rule-specific routing configuration

        Phase 1 (T1): Add confidence-based filtering to reduce false positive noise.

        Args:
            violation: Violation to evaluate

        Returns:
            True if should route, False if should suppress
        """
        # Phase 1 (T1) - Confidence filtering
        # Check if violation has confidence score
        confidence = violation.details.get("adjudication_confidence")

        if confidence is not None:
            # Confidence-scored violation: apply threshold
            if confidence <= self.confidence_threshold:
                # Low confidence: suppress
                return False

        # No confidence score or above threshold: apply standard routing logic
        # (existing severity/rule-based filtering goes here)

        return True  # Default: route

    def route(self, violation: Violation) -> list[bool]:
        """
        Route a single violation to all enabled channels.

        NG-16: Suppresses duplicate alerts within the dedup window.
        Returns:
            List of bool (success/failure) per channel.
        """
        if not self._should_alert(violation):
            return []
        if self._is_duplicate(violation):
            return []

        results = []
        for channel in self._channels.values():
            if not channel.enabled:
                continue
            alert = Alert(
                violation=violation,
                channel=channel.name,
                message=channel.format_message(violation),
                severity=violation.severity,
                rule_id=violation.rule_id,
                entity_id=str(violation.entity_id),
            )
            results.append(channel.send(alert))
        return results

    def route_batch(self, violations: list[Violation]) -> dict[str, int]:
        """
        Route a batch of violations.

        NG-16: Suppresses duplicate alerts within the dedup window.
        Returns:
            Dict mapping channel name to number of successful alerts sent.
        """
        success_counts: dict[str, int] = {name: 0 for name in self._channels}

        for v in violations:
            if not self._should_alert(v):
                continue
            if self._is_duplicate(v):
                continue
            for channel in self._channels.values():
                if not channel.enabled:
                    continue
                alert = Alert(
                    violation=v,
                    channel=channel.name,
                    message=channel.format_message(v),
                    severity=v.severity,
                    rule_id=v.rule_id,
                    entity_id=str(v.entity_id),
                )
                if channel.send(alert):
                    success_counts[channel.name] += 1

        return success_counts

    def _should_alert(self, violation: Violation) -> bool:
        """Check if violation severity meets the threshold."""
        if violation.severity not in self._severity_order:
            return False
        alert_level = self._severity_order.index(violation.severity)
        threshold_level = self._severity_order.index(self.severity_threshold)
        return alert_level >= threshold_level
