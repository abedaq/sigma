# SIGMA_ASR_VTT - API Integration & Key Pool Management

**Developer & Main Contributor:** أصيل السويدي

## Provider Abstraction & Key Pool

```text
                  API Client Request
                          ↓
              Key Pool Load Balancer
                          ↓
      [ Check Key Priority & Quota Status ]
                          |
             +------------+------------+
             |                         |
       Active Key OK           Rate Limit (429)
             |                         |
      Execute Provider        Circuit Breaker Trigger
             |                         |
      Return Result            Auto-Switch to Backup Key
```

## Key Management Specifications
1. **Encrypted Vault Storage:** All API keys are encrypted at rest using AES-256 Fernet encryption.
2. **Quota Tracking & Statistics:** Tracks requests per minute (RPM), remaining daily quota %, key status (Active, Standby, Exhausted, Invalid).
3. **Auto-Failover Circuit Breaker:** Instantly switches to the next available priority key upon hitting rate limits without interrupting the processing pipeline.
