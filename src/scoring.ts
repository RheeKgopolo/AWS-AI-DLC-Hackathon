export type Tier = 'Invite' | 'Nurture' | 'Deprioritize'
export type Badge = 'Moved up' | 'Moved down' | 'No change'

export type SignalKey =
  | 'local_decision_authority'
  | 'offering_fit'
  | 'trigger_signals'
  | 'deal_size_fit'
  | 'relationship_warmth'
  | 'persona_confidence'

export type Weights = Record<SignalKey, number>

export type AccountRow = Record<string, string>

export type ScoredAccount = {
  company: string
  score: number
  tier: Tier
  badge: Badge
  executives: number
  row: AccountRow
}

export const DEFAULT_WEIGHTS: Weights = {
  local_decision_authority: 20,
  offering_fit: 25,
  trigger_signals: 20,
  deal_size_fit: 15,
  relationship_warmth: 10,
  persona_confidence: 10,
}

const AUTHORITY: Record<string, number> = { Yes: 3, Partial: 2, No: 0 }
const LEVEL: Record<string, number> = { High: 3, Medium: 2, Low: 1 }
const WARMTH: Record<string, number> = { Warm: 3, Known: 2, Cold: 0 }
const TIER_RANK: Record<Tier, number> = { Invite: 0, Nurture: 1, Deprioritize: 2 }
const CURRENT_TIER: Record<string, Tier> = {
  'Tier 1': 'Invite',
  'Tier 2': 'Nurture',
  'Tier 3': 'Deprioritize',
}

export function splitList(value: string | undefined): string[] {
  return (value ?? '')
    .split(';')
    .map((item) => item.trim())
    .filter((item) => item !== '')
}

// Points (0 to 3) for each signal, per requirement 4.
export function signalPoints(row: AccountRow): Record<SignalKey, number> {
  const get = (key: string) => (row[key] ?? '').trim()
  return {
    local_decision_authority: AUTHORITY[get('local_decision_authority')] ?? 0,
    offering_fit: LEVEL[get('offering_fit')] ?? 0,
    trigger_signals: Math.min(splitList(row.trigger_signals).length, 3),
    deal_size_fit: LEVEL[get('deal_size_fit')] ?? 0,
    relationship_warmth: WARMTH[get('relationship_warmth')] ?? 0,
    persona_confidence: LEVEL[get('persona_confidence')] ?? 0,
  }
}

// Requirements 5, 6 and 12: weights are scaled so they total 100.
export function scoreAccount(row: AccountRow, weights: Weights = DEFAULT_WEIGHTS): number {
  const points = signalPoints(row)
  const keys = Object.keys(points) as SignalKey[]
  const total = keys.reduce((sum, key) => sum + weights[key], 0)
  if (total <= 0) return 0
  const scale = 100 / total
  const raw = keys.reduce((sum, key) => sum + (weights[key] * scale * points[key]) / 3, 0)
  return Math.min(100, Math.max(0, Math.round(raw)))
}

// Requirement 7.
export function tierForScore(score: number): Tier {
  if (score >= 70) return 'Invite'
  if (score >= 40) return 'Nurture'
  return 'Deprioritize'
}

// Requirement 9.
export function badgeFor(currentTier: string, curated: Tier): Badge {
  const original = CURRENT_TIER[currentTier.trim()]
  if (!original) return 'No change'
  const diff = TIER_RANK[original] - TIER_RANK[curated]
  if (diff > 0) return 'Moved up'
  if (diff < 0) return 'Moved down'
  return 'No change'
}

// Requirement 10: sorted by score, highest first. Ties keep input order.
export function scoreAccounts(
  rows: AccountRow[],
  weights: Weights = DEFAULT_WEIGHTS,
): ScoredAccount[] {
  return rows
    .map((row, index) => {
      const score = scoreAccount(row, weights)
      const tier = tierForScore(score)
      return {
        index,
        account: {
          company: row.company ?? '',
          score,
          tier,
          badge: badgeFor(row.current_tier ?? '', tier),
          executives: splitList(row.target_persona).length,
          row,
        },
      }
    })
    .sort((a, b) => b.account.score - a.account.score || a.index - b.index)
    .map((entry) => entry.account)
}

// Requirement 14: Invite accounts in score order until the next one would exceed the room.
export function buildInviteList(
  scored: ScoredAccount[],
  roomSize: number,
): { accounts: ScoredAccount[]; executives: number } {
  const accounts: ScoredAccount[] = []
  let executives = 0
  for (const account of scored) {
    if (account.tier !== 'Invite') continue
    if (executives + account.executives > roomSize) break
    accounts.push(account)
    executives += account.executives
  }
  return { accounts, executives }
}
