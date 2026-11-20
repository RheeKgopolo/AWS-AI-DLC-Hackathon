import Papa from 'papaparse'
import { describe, expect, it } from 'vitest'
import sampleCsv from '../public/sample/tampa_target_accounts.csv?raw'
import { buildInviteList, scoreAccounts } from './scoring.ts'
import type { AccountRow } from './scoring.ts'

const rows = Papa.parse<AccountRow>(sampleCsv, {
  header: true,
  skipEmptyLines: true,
}).data

const expected = [
  ['Suncoast Credit Union', 100, 'Invite', 'Moved up'],
  ['BayFirst Financial', 97, 'Invite', 'Moved up'],
  ['Raymond James', 92, 'Invite', 'No change'],
  ['GTE Financial', 90, 'Invite', 'Moved up'],
  ['Bankers Financial Corporation', 82, 'Invite', 'Moved up'],
  ['Gulfside Payments', 82, 'Invite', 'Moved up'],
  ['Franklin Templeton', 78, 'Invite', 'No change'],
  ['Harbor Ledger Labs', 60, 'Nurture', 'Moved up'],
  ['Lakeland Community Credit Union', 55, 'Nurture', 'Moved up'],
  ['Northern Trust', 53, 'Nurture', 'No change'],
  ['MetLife', 53, 'Nurture', 'No change'],
  ['Citi', 48, 'Nurture', 'Moved down'],
  ['USAA', 42, 'Nurture', 'Moved down'],
  ['Bayshore Robo Advisory', 42, 'Nurture', 'Moved up'],
  ['Clearwater Lending Cloud', 37, 'Deprioritize', 'No change'],
  ['Palmetto Pay', 37, 'Deprioritize', 'No change'],
  ['JPMorgan Chase', 32, 'Deprioritize', 'Moved down'],
  ['Atlantic Wealth Partners', 22, 'Deprioritize', 'No change'],
  ['Bank of America', 17, 'Deprioritize', 'Moved down'],
  ['Magnolia Regional Bank', 17, 'Deprioritize', 'No change'],
] as const

describe('sample data scoring with default weights', () => {
  const scored = scoreAccounts(rows)

  it('loads 20 accounts', () => {
    expect(rows).toHaveLength(20)
    expect(scored).toHaveLength(20)
  })

  it.each(expected)('%s scores %i, tier %s, badge %s', (company, score, tier, badge) => {
    const account = scored.find((item) => item.company === company)
    expect(account).toBeDefined()
    expect(account?.score).toBe(score)
    expect(account?.tier).toBe(tier)
    expect(account?.badge).toBe(badge)
  })

  it('sorts by score, highest first', () => {
    const scores = scored.map((item) => item.score)
    expect(scores).toEqual([...scores].sort((a, b) => b - a))
  })

  it('builds the invite list for room size 40', () => {
    const invite = buildInviteList(scored, 40)
    expect(invite.accounts).toHaveLength(7)
    expect(invite.executives).toBe(14)
  })

  it('builds the invite list for room size 10', () => {
    const invite = buildInviteList(scored, 10)
    expect(invite.accounts).toHaveLength(5)
    expect(invite.executives).toBe(10)
  })

  it('has a non empty source on every row', () => {
    for (const row of rows) {
      expect(row.source?.trim()).toBeTruthy()
    }
  })
})
