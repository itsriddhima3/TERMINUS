# Legacy journal notes (archive)

2019 desk builds raised `busy_timeout` to 5000 without changing journal family and called that sufficient for parallel ingest. 2021 experiments claimed `DELETE` plus aggressive `synchronous=OFF` reduced fsync latency on embedded flash.

Neither note is authoritative. They are retained only as historical counterexamples. Ingest contract and catalog part 01 supersede this file when symptoms disagree with archive guidance.
