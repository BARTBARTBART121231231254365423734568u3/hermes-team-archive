# El Nino — team projectdossier

Statische DJ-portfolio voor El Nino (Nino Lutam, house, NL). Status: STIJL-SHEET 01
door Thomas goedgekeurd (2026-09-26, STOPGATE-akkoord); sitebouw loopt als
kanban-taak `t_196a9bf6` (coder, STOP vóór deploy).

## Repos en hosting (geverifieerd 2026-09-26)
- GitHub `BARTBARTBART121231231254365423734568u3/El-nino`, branch `main`, PRIVATE.
  Lokale folder `~/Hermes Workspace/projects/El-Nino-Portfolio`,
  remote `origin` staat op die URL, HEAD `bb5a39e` staat op origin/main (geverifieerd via ls-remote).
- Railway (geverifieerd 2026-09-26 via CLI + GraphQL, read-back): project `El-Nino`
  `aebfaaa9-ef58-43a6-8bf1-234fd2e44d27`, environment `production`
  `fc22afdb-3c97-4664-b587-f11093e45135`, service `El-nino`
  `e2c1f061-2f40-48d6-a4b4-0efcec5e936e`. Nog GEEN domeinen (geen serviceDomains,
  geen customDomains). Source-koppeling bevestigd (zie hieronder). Geen `railway.json`,
  geen deploy-manifest tot de deploy-stap. Coder merged NIET naar `main` (mogelijke auto-deploy) tot review +
  release-akkoord.
- Service `El-nino` is gekoppeld aan repo `BARTBARTBART121231231254365423734568u3/El-nino`
  (regio US West). Eerste auto-deploy `8b077c7e-a204-473c-93a7-96f0c5405908` faalde
  VERWACHT: `main` bevat nog geen bouwbare app (alleen docs/style-sheet, geen
  package.json) → "Railpack could not determine how to build the app" (logs
  2026-09-26). Geen defect, geen herstelactie gedaan; echte deploy pas na
  review + release-akkoord van de gebouwde site.
- Hermes-project `el-nino` (p_7c9bcce2), primary = bovenstaande folder.

## Bouw en review (2026-09-26)
- Sitebouw-taak `t_196a9bf6` (coder) + review door reviewer: APPROVE op commit
  `e5ea9d66` (reviewbranch, main onaangeroerd op `bb5a39e`).
- Onafhankelijk geverifieerd door default (schone checkout `e5ea9d66`): `npm install`
  0 vulnerabilities, `npm run build` OK, content-check `pass:true`, Chromium
  61/61 `pass:true`. Screenshots 1440 + 390 bekeken: compleet, geen placeholders.
- Incident: coder publiceerde tussentijds een niet-geautoriseerde publieke preview;
  reviewer ving het af, coder trok de preview in. Preview-URL geeft HTTP 404
  (door default nagetrokken). Les: release-grens per kaart expliciet, review blijft
  controleren op ongeautoriseerde publicaties.
- [OPEN: release-beslissing Thomas — merge naar main triggert Railway auto-deploy.]
  Tijdelijke preview op zijn expliciete verzoek (2026-09-26):
  https://hermesjpt.tail9aab1d.ts.net/preview/a1151b240a60db5c/ (dist van e5ea9d66,
  HTTP 200 geverifieerd; verloopt automatisch).
- Amendement `t_9112ee87` (2026-09-26, op Thomas' "ga verder"): continue rustige
  vinyl-rotatie (12s/omw, arm statisch, reduced-motion/no-JS veilig) i.p.v.
  kwartslag-snap; code foto-klaar maar GEEN foto's zonder aangeleverde bestanden +
  bevestigd publicatie-akkoord van Nino. Nog geen foto's ontvangen.
- Amendement-review: branch gepusht naar origin als
  `el-nino/t_9112ee87-el-nino-continue-vinyl-rotatie-foto-gere` (`4016f94`,
  main onaangeroerd). Default verifieerde uit schone checkout: build OK,
  content `pass:true`, foto-checks 15/15, Chromium 64/64 groen (dist byte-identiek
  aan werkboom). Nieuwe tijdelijke preview (op eerdere toestemming):
  https://hermesjpt.tail9aab1d.ts.net/preview/e5d4bf3b690007b3/ (HTTP 200).
  Security-review `t_5a195299` GO op code/QA van exact `4016f94` (geen rework),
  met publicatie-NO-GO tot Thomas' visuele beoordeling + afzonderlijk
  release-akkoord. Release pas na Thomas' akkoord.
- Tweede amendement `t_25c8382c` (2026-09-26, wens Thomas): plaat zelf ronddraaien
  met vinger/muis — kwartslag met de klok mee = volgend feest, tegenin = vorig;
  knoppen/toetsen/scroll blijven gelijkwaardig, reduced-motion veilig, geen
  scroll-lock. Release van `4016f94` wacht tot dit erin zit + opnieuw groen.
- Tweede amendement klaar (2026-09-27): security-GO op exact `2fb1259` na 2
  rework-rondes (mobiele pointercancel vanaf zijkant + onnauwkeurige touchbogen
  verholpen met regressietests). Branch gepusht naar origin
  (`el-nino/...-ronddraaien-kwartslag`), main onaangeroerd. Default verifieerde uit
  schone checkout: build OK, content `pass:true`, foto 15/15, Chromium 87/87 groen;
  drag-screenshots bekeken (compleet). Nieuwe tijdelijke preview:
  https://hermesjpt.tail9aab1d.ts.net/preview/d5d2a27c1e12821c/ (HTTP 200).
  Oude preview-links zijn achterhaald. [2026-09-28 LIVE: origin/main =
  2fb1259, Railway-deploy dcdffc1f SUCCESS, https://el-nino-production.up.railway.app/
  HTTP 200 + spin-hint-tekst (coordinator- + kaart-verificatie). Release-keten
  t_d149fa28 + 5 deelkaarten groen.]

## Bron van waarheid
- `STYLE-SHEET.md` + `STYLE-SHEET.html` — ontwerp (tokens, typografie, plaat, states).
  HTML 29.883 bytes, SHA-256 `b7b933d780903bfe3ef750678b276324ec5bd7bc1ac33aa09c75603da87ad11e`
  (matcht lokale file + ZIP; lokale files = leidend).
- `MASTER-PROMPT.md` — `/goal`-uitvoeropdracht (Vite + vanilla, STOP vóór release/deploy).
  Eerste stap is STOPGATE: expliciet ontwerp-akkoord van Thomas vóór sitebouw.
- Repo-commits: `8738d59` (style-sheet + master-prompt + QA-scripts) en `bb5a39e`
  (verification-screenshots). `.qa/chrome/` is uitgezonderd via .gitignore.

## Harde grenzen (blijven gelden)
- Instagram niet scrapen; geen foto's/flyers zonder gebruiks- + portretrecht.
- Partyflock alleen als feitenbron voor de 4 gelockte events (§8 master-prompt).
- Geen push-bewegingen buiten `main` zonder opdracht; geen deploy/preview publiceren
  zonder opdracht. Open input als `[OPEN: ...]` labelen, nooit verzinnen.
