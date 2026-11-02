The problem you've run into is a classic one: an AI agent that treats every inbound email as a legitimate conversation will happily try to "reply" to a marketing blast or a no-reply notification. The fix is to build a **layered filtering gate** in front of your reply logic, so the AI only ever sees emails that actually warrant a response. Here's how to do it, from the simplest filters to the most robust.

### 🚦 Layer 1: Use Gmail's built-in categories as a first gate

Gmail already classifies every incoming message into system categories, and you can query these directly via the Gmail API. The key insight is that **Promotions is not Spam**—it's a usability layer for legitimate bulk mail (marketing, newsletters, offers). These are exactly the emails you don't want your agent replying to.

The relevant system label IDs are:

| Label ID | Tab | What lands there |
| :--- | :--- | :--- |
| `CATEGORY_PERSONAL` | Primary | One-on-one human conversations—**these are the ones you want** |
| `CATEGORY_PROMOTIONS` | Promotions | Bulk marketing, newsletters, offers, coupons |
| `CATEGORY_UPDATES` | Updates | Bills, receipts, confirmations (bulk but functional) |
| `CATEGORY_SOCIAL` | Social | Social network notifications |
| `CATEGORY_FORUMS` | Forums | Mailing lists and group discussions |

**The practical approach:** Instead of fetching all inbox emails, scope your agent's trigger to only `CATEGORY_PERSONAL`. A GitHub reference spec for a Gmail AI bot explicitly states that draft replies should be generated for `CATEGORY_PERSONAL`—emails from friends, family, or personal contacts that are one-on-one human conversations, not transactional or commercial in nature.

**One critical API gotcha:** When using the Gmail API's `labelIds` parameter, multiple labels are combined with **AND** logic, not OR. So `labelIds=["CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL"]` returns nothing, because no single email carries both category labels. To filter across multiple categories, use the `q` search parameter instead, which supports OR: `q="category:promotions OR category:social"`.

For a single category—which is what you want here—`labelIds=["CATEGORY_PERSONAL"]` works fine.

### 🧠 Layer 2: Add AI-based classification as a second opinion

Gmail's categories are a strong signal, but they aren't perfect. An ad or cold sales pitch can occasionally slip into Primary, and a genuine customer email might land in Updates if it includes an invoice reference. This is where a lightweight AI classification step earns its keep.

A common pattern in production workflows is:

1. **Trigger** on new emails (optionally pre-filtered to `CATEGORY_PERSONAL`).
2. **Classify** each email with an LLM prompt that returns a simple category: `COLD_SALES`, `BULK_MARKETING`, `NOTIFICATION`, or `NEEDS_REPLY`.
3. **Route** based on that classification—only `NEEDS_REPLY` goes to the reply generator; everything else is skipped, labeled, or archived.

The `use-agent` project on PyPI does exactly this: it scans Gmail for unsolicited sales email and bulk marketing, classifies each message as `COLD_SALES`, `BULK_MARKETING`, or `NOT_COLD_SALES`, and skips the latter category entirely.

You can make the classifier even more precise by giving it **examples** of what to skip in your system prompt—specific sender domains (e.g., `noreply@`, `no-reply@`, `marketing@`), subject-line patterns, and phrases like "unsubscribe" or "limited-time offer."

### 📨 Layer 3: Sender and header-based hard rules

Before the AI even runs, you can eliminate a huge volume of non-actionable email with deterministic rules that are cheap, fast, and 100% predictable:

- **Skip no-reply addresses.** Gmail Agent's built-in controls "ignore no-reply addresses that don't expect a response" and leave out transactional messages like order confirmations and receipts. You can implement this with a simple sender-address allowlist/blocklist.
- **Analyze headers.** Tools like Inbounter Shield filter AI agent inboxes using "content patterns, sender reputation scores, and header analysis," and specifically block "Auto-responders, bounce notifications, MAILER-DAEMON messages, and no-reply" senders.
- **Maintain a blocklist of known ad senders.** If you spot a marketing domain that repeatedly lands in Primary, add it to an explicit skip list. Jotform's Gmail Agent lets you exclude specific senders from draft creation, and you can apply the same logic in your own code.

### 🛡️ Layer 4: Quarantine instead of delete (so you can audit and improve)

Don't just silently drop filtered emails. Route them to a separate **quarantine label** or folder so you can periodically review what your agent skipped. Inbounter Shield, for example, "silently discards" spam or routes it to a separate quarantine inbox. This gives you two benefits:

- **False-negative detection:** If a real customer email got filtered as an ad, you'll catch it and adjust your rules.
- **Iterative improvement:** You can feed misclassified examples back into your AI classifier's prompt to make it smarter over time.

### 🧩 Putting it together: a practical filtering pipeline

Here's how the layers stack in practice:

```
New email arrives
      ↓
[Gate 1] Query Gmail: labelIds=["CATEGORY_PERSONAL"]  → skip Promotions/Updates/Social/Forums
      ↓
[Gate 2] Sender/header rules: skip noreply@, no-reply@, mailer-daemon, auto-responders
      ↓
[Gate 3] AI classifier: COLD_SALES / BULK_MARKETING / NOTIFICATION → skip
      ↓
[Gate 4] Only NEEDS_REPLY emails reach your reply generator
      ↓
Reply sent (or draft created for review)
```

If you want to be extra cautious while you're still tuning the system, set your agent to **draft replies** rather than send them automatically. That way, even if an ad slips through all four gates, a human has to approve the draft before it goes out—and you'll immediately see which filter needs tightening.

The core principle is simple: **your AI reply agent should never be the first line of defense.** Let Gmail's categories and deterministic sender rules absorb the bulk of non-actionable email, then use AI classification to catch the rest, and only then invoke the reply generator. This keeps your agent focused on the conversations that actually matter—and prevents it from wasting effort (or embarrassing you) by replying to an ad.