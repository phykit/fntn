# Notes to `fomc_dates.csv`

Collected 29 October 2026 by an agent instructed to read no price, index or return data, under
`PREREG.md` section 1. Source: federalreserve.gov only. Every page was read through WebFetch; a
direct HTTP fetch of the raw HTML was refused by the session's egress proxy, so the page text
reached the agent through WebFetch's summariser and each year was cross-checked by a second
WebFetch query with a counting prompt where the first answer was internally inconsistent (1998,
2003, 2020) and for the whole out-of-sample stretch (the calendars page).

Row convention: one row per scheduled meeting; `meeting_end` equals `announcement_day` by
construction (section 1: the announcement day is the last day of each scheduled meeting);
sorted by `announcement_day`; cutoff is the latest meeting ending on or before 29 October 2026.

## Pages read

| Page | Years supplied | Result |
|---|---|---|
| `https://www.federalreserve.gov/monetarypolicy/fomchistorical1994.htm` to `...2020.htm` (27 pages) | 1994 to 2020 | fetched |
| `https://www.federalreserve.gov/monetarypolicy/fomchistorical2021.htm` | n/a | **not fetched**: the site returned a client error on three attempts; 2021 is taken from the calendars page instead, which lists it in full |
| `https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm` | 2021 to 2026 (page runs 2021 to 2027) | fetched |

The calendars page shows no year before 2021, so there is no overlap between the two sources
and no year is double-sourced.

## Exclusion rule applied

A page entry was kept only if its heading reads as a scheduled meeting, i.e. a date or date
range followed by "Meeting" on the historical pages, or a bare date range on the calendars page.
Entries labelled "Conference Call", "(unscheduled)", "(notation vote)" or "(cancelled)" were
excluded. Entries excluded, by year (all as labelled on the page):

- 1994: conference calls 28 Feb, 24 Mar, 18 Apr, 20 Jul, 30 Dec
- 1995: conference calls 13 Jan, 10 Mar, 28 Apr
- 1998: conference calls 21 Sep, 15 Oct
- 2001: conference calls 3 Jan, 11 Apr, 18 Apr, 13 Sep, 17 Sep
- 2003: conference calls 25 Mar, 1 Apr, 8 Apr, 16 Apr; and see the 15 September entry below
- 2007: conference calls 10 Aug, 16 Aug, 6 Dec
- 2008: conference calls 9 Jan, 21 Jan, 10 Mar, 24 Jul, 29 Sep, 7 Oct
- 2009: conference calls 16 Jan, 7 Feb, 3 Jun
- 2010: conference calls 9 May, 15 Oct
- 2011: conference calls 1 Aug, 28 Nov
- 2013: "October 16 (unscheduled)"
- 2014: "March 4 (unscheduled)"
- 2019: "October 4 (unscheduled)"
- 2020: "March 2 (unscheduled) Meeting", "March 15 (unscheduled) Meeting", "March 17-18
  (cancelled) Meeting", notation votes 19 Mar, 23 Mar, 31 Mar, 27 Aug
- 2025: "August 22 (notation vote)"
- 2026: "December 8-9" (after the cutoff, not an exclusion on type)

## Count of meetings per year

| Year | Count | Year | Count | Year | Count |
|---|---|---|---|---|---|
| 1994 | 8 | 2005 | 8 | 2016 | 8 |
| 1995 | 8 | 2006 | 8 | 2017 | 8 |
| 1996 | 8 | 2007 | 8 | 2018 | 8 |
| 1997 | 8 | 2008 | 8 | 2019 | 8 |
| 1998 | 8 | 2009 | 8 | 2020 | **7** |
| 1999 | 8 | 2010 | 8 | 2021 | 8 |
| 2000 | 8 | 2011 | 8 | 2022 | 8 |
| 2001 | 8 | 2012 | 8 | 2023 | 8 |
| 2002 | 8 | 2013 | 8 | 2024 | 8 |
| 2003 | 8 | 2014 | 8 | 2025 | 8 |
| 2004 | 8 | 2015 | 8 | 2026 | **7** (to cutoff) |

Total: **262** scheduled meetings. Of these, **86** have an announcement day on or after
1 January 2016 (the PREREG's primary out-of-sample window), against the "about 86" the PREREG
anticipated in section 5.

## Years with a count other than 8

- **2020: 7.** The scheduled 17-18 March 2020 meeting is labelled "March 17-18 (cancelled)
  Meeting - 2020" on the historical page, with no statement beneath it; the policy action of that
  fortnight is under "March 15 (unscheduled) Meeting - 2020", which carries a statement and is
  excluded as unscheduled. A cancelled meeting has no last-day announcement, so no row is
  written for it. **This is a judgement call and the operator may wish to rule on it**: section 1
  says "scheduled" and excludes "unscheduled and conference-call meetings", and does not speak to
  a cancelled one. Including 2020-03-18 as a row would add one announcement day on which no
  announcement was made.
- **2026: 7.** The 8-9 December 2026 meeting falls after the 29 October 2026 cutoff. The
  27-28 October 2026 meeting is the last row.

## Ambiguities

1. **September 2003.** The historical page lists two consecutive entries, "September 15 Meeting -
   2003" and "September 16 Meeting - 2003". The 15 September entry carries only an agenda,
   memos, a minutes link that points at the August 12 minutes section, a transcript and
   presentation materials; the 16 September entry carries the Beige Book, Greenbook, Bluebook,
   agenda, **Statement**, minutes "(Released October 30, 2003)" and transcript. The CSV records
   one scheduled meeting with `meeting_start` and `meeting_end` both 2003-09-16, which is the day
   the statement sits under. The alternative readings are i) a two-day meeting 15-16 September
   (same announcement day, different `meeting_start`) or ii) two separate meetings, which would
   add a 15 September row with no statement and make 2003 a nine-count year. The announcement
   day is 2003-09-16 under either of the first two readings; only reading ii) changes the test.
2. **Statements before May 1999.** Section 1 defines the announcement day as the last day of
   each scheduled meeting; it does not require that a statement was issued. The page entries
   for 1994 to early 1999 do not uniformly carry a "Statement" link, and this file does not
   record which do. No row was dropped on that ground.
3. **Cross-month two-day meetings** were transcribed from labels of the form "June 30-July 1",
   "January 31-February 1", "July 31-August 1", "April/May 30-1", "Jan/Feb 31-1", "Jul/Aug 31-1"
   and "Oct/Nov 31-1"; each resolves to consecutive calendar days and the build script asserts a
   span of at most one day for every row.
4. **Weekday check.** Announcement days fall on 167 Wednesdays, 85 Tuesdays, 9 Thursdays and 1
   Friday (4 February 1994). The Thursdays are 6 July 1995; 30 June 2005; 29 June 2006; 28 June
   2007; 13 September 2012; 17 September 2015; 8 November 2018; 5 November 2020; 7 November
   2024. Each matches a page label; none is a transcription slip. No announcement day falls on a
   weekend.
5. **Summariser dependence.** Because the raw HTML could not be fetched, every label passed
   through WebFetch's model. Where its running commentary contradicted its own list (1998: "seven
   scheduled" beside eight "Meeting" headings), the verbatim headings were taken and the page
   re-queried with a counting prompt, which returned eight. A reader with direct access to the
   pages can verify the CSV against them in a few minutes; the source URL is on every row.
