# Less Destructive Farm

Look at the examples in `game-archive`, you should put your node module that export a submitter with the game configuration in the `game` folder.

The package.json and the other module files should be directly inside the game folder:
- game/package.json
- game/index.js
- game/...

After that just use `docker-compose up -d` and you are ready to go.

## A/D Game Configuration (10.10.0.1) April 10th 2026

The current `game/index.js` is configured for the checker APIs described in the rules:

- Flag submit endpoint: `PUT http://10.10.0.1:8080/flags`
- Flag IDs metadata endpoint: `GET http://10.10.0.1:8081/`
- Flag IDs endpoint: `GET http://10.10.0.1:8081/flagIds`

Set runtime variables before starting the stack:

```bash
export TEAM_TOKEN='YOUR_TEAM_TOKEN'
export FLAG_SUBMIT_URL='http://10.10.0.1:8080/flags'
export FLAG_IDS_BASE_URL='http://10.10.0.1:8081'
docker compose up -d --build
```

Status mapping used by the submitter:

- `ACCEPTED` -> stored as `ACCEPTED`
- `DENIED` -> stored as `REJECTED`
- `RESUBMIT` and `ERROR` -> kept as `QUEUED` to retry on next cycle

Rate-limit awareness:

- The submitter waits between requests (`FLAG_SUBMIT_SPACING_MS`, default 2200 ms)
- Flags are sent in batches (`FLAG_SUBMIT_BATCH_SIZE`, default 250)
- Defaults are chosen to stay under 30 requests/minute while keeping request bodies below 100kB

## Client

https://github.com/DestructiveVoice/DestructiveFarm/blob/master/docs/en/farm_client.md