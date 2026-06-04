# Kit row expectations for crash-suite verification

| kit | rows after seed load | notes |
|-----|---------------------:|-------|
| KIT-A | 48 | alpha line sensors |
| KIT-B | 36 | bravo line sensors |
| KIT-C | 52 | charlie line sensors |
| KIT-D | 40 | delta line sensors |

Each kit must reopen after simulated abrupt stop during the compaction window with `schema_marker` 2 and full row totals above.
