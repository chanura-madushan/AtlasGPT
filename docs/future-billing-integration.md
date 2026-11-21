# Future billing integration

**Status: intentionally deferred.** No payment provider has been selected. AtlasGPT must remain usable without a payment gateway while the frontend and core product are completed.

## Current behavior

- `GET /plans` exposes the guest, free, and paid plan catalog.
- `GET /account/usage` returns the authenticated user's plan and current usage.
- `src/database/usage_db.py` enforces plan limits.
- `set_user_plan(user_id, plan, status)` is an internal database operation. It is not a public plan-upgrade endpoint.
- There are currently no checkout, payment, subscription-management, or payment-webhook endpoints.

The frontend must not simulate a successful payment or allow a browser request to grant itself a paid plan. Until billing exists, present the paid tier as unavailable/coming soon and continue enforcing the user's actual backend plan.

## Intended provider-neutral boundary

When a provider is selected, add a billing module that separates AtlasGPT entitlements from provider-specific APIs. Keep provider SDK calls out of route handlers and usage-limit code.

The future adapter should expose operations equivalent to:

- Create a checkout session for an authenticated user and a server-defined price/plan.
- Verify and normalize signed provider webhook events.
- Map provider customer and subscription IDs to an AtlasGPT user.
- Activate, renew, cancel, expire, or revoke an entitlement idempotently.
- Retrieve subscription state from the provider when reconciliation is needed.

Use a provider interface and one implementation per gateway. Do not let the client submit an arbitrary plan, price, amount, user ID, or entitlement status.

## Security and correctness requirements

Before enabling payments:

1. Verify webhook signatures against the raw request body using the provider's official SDK or documented algorithm.
2. Make webhook processing idempotent using the provider event ID and a database uniqueness constraint.
3. Persist provider customer/subscription IDs, price identifiers, currency, billing period, status, and event audit metadata.
4. Verify checkout ownership on the server; never trust client redirects as proof of payment.
5. Handle successful payments, failed renewals, cancellations, refunds/chargebacks, grace periods, and subscription expiry.
6. Update entitlements only after verified provider events or trusted server-side reconciliation.
7. Keep secrets in environment/secret management, never in frontend code or Git.
8. Add tests for invalid signatures, duplicate/out-of-order events, ownership violations, failed payments, cancellations, and expiry.

## Frontend contract until then

Use `GET /plans` and `GET /account/usage` to render plan details and usage. The paid plan may be shown as **Coming soon**. Do not display a working checkout action until a real provider adapter and verified webhook lifecycle are implemented.
