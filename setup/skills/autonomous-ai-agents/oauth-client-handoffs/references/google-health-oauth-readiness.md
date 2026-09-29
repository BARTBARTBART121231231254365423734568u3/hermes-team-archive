# Google Health OAuth readiness

Use this procedure when an application connects Fitbit-family or other health data through the Google Health API.

## Configure

1. Use a Google Cloud project with the **Google Health API** enabled.
2. Create an OAuth client of type **Web application / Web server** for a server-hosted web app. Do not choose browser, Android, or iOS merely because the end user opens the app on a phone; the callback is handled by the web server.
3. Register the application's exact HTTPS callback route as an authorized redirect URI. Copy it exactly into both Google Cloud and the application's server-wide integration settings; a host, slash, or path mismatch breaks the authorization-code exchange.
4. Configure the OAuth consent screen as External when non-organization users must connect. Add only the Google Health scopes the product actually reads; restricted health scopes increase verification obligations.
5. Store the client secret only through the application's authenticated admin configuration or secret store. Never request or relay it in chat, task cards, screenshots, or logs.

## Test before owning a device

1. While publishing status is **Testing**, add each tester's Google email under **Google Auth Platform → Audience → Test users**. A valid client alone does not permit unlisted test accounts.
2. Initiate Connect from the actual application, complete consent with a listed test account, and verify the callback returns to the app with Connected state.
3. Run Sync even when the account has no device data. This validates redirect matching, authorization-code exchange, encrypted token persistence, refresh-token handling, and API reachability; an empty dataset is not an OAuth failure.
4. For populated testing without physical hardware, use Google's Health mobile app/sample-data workflow or OAuth Playground codelab, then sync the same account. Label this as synthetic-data validation.
5. Reserve one final real-device test for source-specific behavior such as Aria weight/body-composition ingestion; synthetic data proves the integration path, not the hardware's exact field mapping.

## Production readiness

- Inspect configuration by presence/non-empty state only; never print credential values.
- Verify Connect, callback, Connected state, Sync, and refresh after access-token expiry. A healthy application endpoint does not prove OAuth works.
- Confirm the production callback URI, not a tutorial placeholder such as `https://www.google.com`, is registered.
- Keep the app in Testing for controlled validation. Public rollout of restricted health scopes may require Google OAuth verification; support beyond Google's unverified-user cap may require a third-party security review.
- Prefer Google Health for current Fitbit-family integrations when the legacy Fitbit Web API is being retired; do not build new onboarding around a deprecated provider path.

## User guidance

When a non-technical user cannot find **Audience**, first identify whether they are in the older **APIs & Services** area. Direct them to **Google Auth Platform → Audience** (or its direct console URL), confirm the intended Cloud project is selected, then add the test account. Give one screen-specific next action at a time and ask for a screenshot only when the visible UI differs.
