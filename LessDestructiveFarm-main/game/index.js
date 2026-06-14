const got = require('got');

// Should be the actual team token provided by participants.
const TEAM_TOKEN = process.env.TEAM_TOKEN || '';
// Use the checker submission endpoint from specification.
const FLAG_SUBMIT_URL = process.env.FLAG_SUBMIT_URL || 'http://10.10.0.1:8080/flags';
// Base URL for metadata and flag IDs APIs.
const FLAG_IDS_BASE_URL = process.env.FLAG_IDS_BASE_URL || 'http://10.10.0.1:8081';
const TIMEOUT_MS = Number(process.env.FLAG_SUBMIT_TIMEOUT_MS || 5000);
// Request spacing keeps the sender under the 30 req/min limit.
const REQUEST_SPACING_MS = Number(process.env.FLAG_SUBMIT_SPACING_MS || 2200);
// Batch size is tuned to stay below the 100kB body limit.
const MAX_FLAGS_PER_REQUEST = Number(process.env.FLAG_SUBMIT_BATCH_SIZE || 250);
const rawTeams = require('./teams.json');
const teams = rawTeams.teams || rawTeams;
// Teams format:
/*
{
  "name1": "IP1",
  "name2": "IP2"
}
*/

// Helper function to decode flag format: extract round, team, and service IDs
// Flag structure: [0:2]=round, [2:4]=team, [4:6]=service (all in base 36)
const decodeFlag = (flag) => {
  if (!flag || flag.length < 6) return null;
  try {
    return {
      round: parseInt(flag.slice(0, 2), 36),
      team: parseInt(flag.slice(2, 4), 36),
      service: parseInt(flag.slice(4, 6), 36)
    };
  } catch {
    return null;
  }
};

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms)); // Simple sleep function for spacing out requests.

// Checker returns messages as "[FLAG] message". Extract only the readable part.
const extractMessage = msg => {
  if (typeof msg !== 'string') return '';
  const separator = msg.indexOf(']');
  if (separator === -1) return msg.trim();
  return msg.slice(separator + 1).trim();
};

const mapCheckerStatus = status => {
  switch (status) {
    case 'ACCEPTED':
      return 'ACCEPTED';
    case 'DENIED':
      // The local DB tracks denied flags as REJECTED.
      return 'REJECTED';
    case 'RESUBMIT':
    case 'ERROR':
      // Keep retryable flags in queue.
      return 'QUEUED';
    default:
      return 'QUEUED';
  }
};

module.exports = {
  // Anchored regex from specification: /^[A-Z0-9]{31}=$/
  flagFormat: '[A-Z0-9]{31}=',
  decodeFlag,
  // One tick is 120 seconds.
  submitInterval: 120,
  // A flag stays valid for 5 rounds (10 minutes total).
  flagLifetime: 5 * 120,
  teams,
  // Response statuses per specification:
  // - ACCEPTED: accepted by game system
  // - DENIED: invalid/expired/own/already claimed/check failed
  // - RESUBMIT: not active yet, retry next round
  // - ERROR: temporary backend problem, retry later
  submitFlags: async (flags, onSubmit) => {
    if (!TEAM_TOKEN) {
      console.log('TEAM_TOKEN is empty. Configure TEAM_TOKEN before submitting flags.');
      return;
    }

    const tot = flags.length;
    const chunkSize = Math.min(MAX_FLAGS_PER_REQUEST, flags.length);
    for (let i = 0; i < tot; i += chunkSize) {
      try {
        const chunk = flags.slice(i, i + chunkSize);
        // Submit in batches to respect body and rate limits.
        const answer = await got
        .put(FLAG_SUBMIT_URL, {
          headers: {
            'X-Team-Token': TEAM_TOKEN
          },
          timeout: TIMEOUT_MS,
          json: chunk
        })
        .json();

        if (!Array.isArray(answer)) {
          console.log('Unexpected checker response format:', answer);
          continue;
        }

        // Response format: [{ flag, status, msg }]
        for (let idx = 0; idx < answer.length; idx += 1) {
          const response = answer[idx] || {};
          const rawStatus = response.status;
          const dbStatus = mapCheckerStatus(rawStatus);
          const message = extractMessage(response.msg);
          const flag = response.flag || chunk[idx];
          await onSubmit(flag, dbStatus, `[${rawStatus || 'UNKNOWN'}] ${message}`.trim());
        }
      } catch (e) {
        // HTTP 500 can indicate malformed request, invalid token, or ended game.
        console.log('Flag submission error:', e.message);
        if (e.response && e.response.statusCode === 500) {
          console.log('Server error (500):', e.response.body);
        }
      } finally {
        // Add a pause before next request to avoid submission throttling.
        if (i + chunkSize < tot) {
          await sleep(REQUEST_SPACING_MS);
        }
      }
    }
  },
  // Returns available teams/services/rounds from the checker metadata endpoint.
  getMetadata: async () => {
    try {
      const metadata = await got.get(FLAG_IDS_BASE_URL, {
        timeout: TIMEOUT_MS
      }).json();
      return metadata;
    } catch (e) {
      console.log('Error fetching metadata:', e.message);
      return null;
    }
  },
  // Fetch flag IDs with optional filters: service, team, round.
  getFlagIds: async (filter = {}) => {
    try {
      const url = new URL('/flagIds', FLAG_IDS_BASE_URL);
      if (filter.service) url.searchParams.append('service', filter.service);
      if (filter.team) url.searchParams.append('team', filter.team);
      if (filter.round) url.searchParams.append('round', filter.round);
      
      const flagIds = await got.get(url.toString(), {
        timeout: TIMEOUT_MS
      }).json();
      return flagIds;
    } catch (e) {
      console.log('Error fetching flag IDs:', e.message);
      return null;
    }
  }
};
