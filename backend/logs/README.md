# Logs

This directory stores server-side logs related to API activities.

---

## Upload Abuse Logging

**File:** `upload_abuse.log`

The backend automatically monitors and logs suspicious or abusive upload activities.
Each entry is formatted as:

```
[timestamp] IP <client_ip>: <reason>
```

Where:

- `timestamp` is in UTC ISO format.
- `client_ip` is the IP address of the user attempting the upload.
- `reason` explains the violation (e.g., "Rate limit exceeded", "Invalid file extension", "Malicious content detected", etc.)

---

## Purpose

- Maintain traceability of abusive or suspicious behaviors.
- Protect the API from denial of service (DoS) attempts.
- Enable future alerting, banning, or advanced rate limiting if needed.

---

## Future Enhancements (Optional)

- Rotate log files daily or when exceeding a size threshold.
- Ship critical abuse logs to a centralized monitoring system (e.g., Loki, ELK).
- Enforce automatic IP blacklisting based on abuse patterns.

---

## Important Notes

- **No sensitive user data is logged.** Only IP and violation reason are stored.
- **Retention Policy:** It is recommended to periodically clear or rotate this log to avoid disk space issues.
