# Standard Audit Scopes by Specialist

## Security Audit (security profile)

**CRITICAL findings:**
- Leaked secrets in source/history (API keys, passwords, JWTs)
- Hardcoded credentials
- SQL injection vulnerabilities
- Authentication/authorization bypasses
- Shell injection (shell=True, os.system)
- Unsafe deserialization (pickle.loads)
- Known CVEs in critical dependencies

**HIGH findings:**
- SMTP/email injection
- SSRF (Server-Side Request Forgery)
- Path traversal vulnerabilities
- Cross-site scripting (XSS)
- CSRF (when not protected)
- Sensitive data in logs/errors
- Weak password hashing
- Unencrypted data transmission
- Dependency vulnerabilities (moderate/high)

**MEDIUM/LOW:**
- Rate limiting gaps
- Missing security headers
- Deprecated crypto algorithms
- Unnecessary permissions
- GDPR/privacy compliance checklist

---

## Code Audit (coder profile)

**HIGH findings:**
- Architecture flaws (tight coupling, missing layers)
- Infinite loops / performance regressions
- Memory leaks
- Off-by-one errors
- Race conditions
- Missing error handling
- Silent exception swallowing (bare except)
- Dead code paths

**MEDIUM findings:**
- Code duplication (DRY violations)
- Over-complicated logic
- Missing tests
- Poor naming
- Unused imports/variables
- Large functions (>200 LOC)
- Magic numbers
- Inconsistent patterns

**LOW findings:**
- Linting violations
- Formatting issues
- Documentation gaps
- Performance micro-optimizations

---

## Design Audit (designer profile)

**HIGH findings:**
- Accessibility violations (WCAG AA)
- Broken/unusable flows
- Mobile responsiveness broken
- Contrast failures (text readability)
- Missing focus indicators
- Form validation UX gaps

**MEDIUM findings:**
- Inconsistent component styling
- Missing empty states
- Hover/touch state confusion
- Typography hierarchy issues
- Spacing inconsistency
- Icon usage conflicts

**LOW findings:**
- Polish/animation refinements
- Brand consistency tweaks
- Whitespace optimization

---

## Feature Audit (planner profile)

**HIGH findings:**
- Missing table-stakes features (competitors all have these)
- Data loss risks
- Onboarding friction
- User workflow gaps
- Unclear/broken UX paths
- Incomplete feature implementations

**MEDIUM findings:**
- Feature parity gaps
- Workflow efficiency issues
- Edge cases unhandled
- Manual workarounds required

**LOW findings:**
- Efficiency improvements
- Quality-of-life features
- Future roadmap items

---

## Competitive Research (researcher profile)

**HIGH findings:**
- Market gaps (unique opportunity)
- Feature trends (must-haves shifting)
- Unmet user needs
- Pricing/positioning gaps

**MEDIUM findings:**
- Best practice patterns
- Technology selection guidance
- Niche opportunities
- Integration recommendations

**LOW findings:**
- Aspirational features
- Long-tail improvements

---

## Operations Audit (scheduler profile)

**HIGH findings:**
- No error tracking/visibility
- No automated backups
- Data persistence risks
- No health checks
- Unmonitored deployments
- No failover/recovery plan

**MEDIUM findings:**
- CI/CD gaps
- Deployment documentation missing
- No uptime monitoring
- No rate limiting
- Response compression missing
- Slow API endpoints

**LOW findings:**
- Performance optimization opportunities
- Resource utilization improvements
- Logging/observability enhancements
