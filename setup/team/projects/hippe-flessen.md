# Hippe Flessen — team projectdossier

Thomas' moeder start Hippe Flessen: lege keramische olijfolieflessen verkopen via eigen webshop.
Stijl: Klei & crème (goedgekeurd). Logo: 02 Duo (richting B, goedgekeurd).

## Repos en hosting (geverifieerd 2026-09-25)
- Het oude Railway-project `07ed67ea-cec7-413f-b7fe-51e1256913c8` en de oude production-omgeving `a90dcd64-473b-4b2c-8ca4-24841a17938a` zijn NOOIT deploydoel.
- Actief project `Hippe flessen` `034962d3-be03-4512-8c4e-b74ef230d2ef`, echte environment `Staging` `aea88124-0a2d-453f-af5d-0fa0503c0447`, service `Hippe-flessen` `9d39c208-412d-410b-a666-8b2c1c71675a`.
- GitHub `BARTBARTBART121231231254365423734568u3/Hippe-flessen`, branch `staging`; URL https://hippe-flessen-staging.up.railway.app. Manifest: `~/.hermes/team/deployments/hippe-flessen-staging.json`. Alleen `railway deploy-verified` met exacte reviewed SHA voor releases, geen raw upload.
- Dashboard-release t_b079d479: security en functionele GO op `f0e3240c43a603090ddf6d95e5846feb1f7feef0`; staging-branch naar die SHA gepusht, Railway-deployment `ed23b9cb-7748-40ac-9622-1e9e85bb5181` SUCCESS (vorige `2890d662-c232-46d8-97dc-ee7ebf8bf787`, SHA `b3b26a04d5a4562a6a57c27ca5e9740bb748f418`). Publieke routes en anonieme beveiliging live gecheckt; geauthenticeerde dashboard-mutaties nog NIET live geverifieerd zolang een veilige admin-testlogin ontbreekt. Taak blijft geblokkeerd, niet als volledig opgeleverd rapporteren.

## Demo-grenzen (blijven gelden)
Voorbeeldinhoud, geen echte verkoop/betaling/verzending. De volledige winkel/beheer-app moet op staging interactief werken zonder publiek onbeschermde mutaties; beveiligings- en opslagontwerp wordt onafhankelijk beoordeeld voordat devops publiceert. Echte commerce pas na aparte goedkeuring.
