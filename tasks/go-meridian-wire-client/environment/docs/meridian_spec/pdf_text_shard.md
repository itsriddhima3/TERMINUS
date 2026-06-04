# PDF text shard — extracted OpenAPI pages 61–120

## Operation 61
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: beneficiary label string with whitespace normalization
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 0.

## Operation 62
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: amount minor units int64
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 1.

## Operation 63
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: amount major_alias scaled field
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 2.

## Operation 64
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: fingerprint slot gamma_spaced vs gamma_compact
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 3.

## Operation 65
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: origin Acme-Origin routing profile
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 4.

## Operation 66
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: destination Beta-Dest settlement lane
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 5.

## Operation 67
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: beneficiary label string with whitespace normalization
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 6.

## Operation 68
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: amount minor units int64
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 7.

## Operation 69
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: amount major_alias scaled field
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 8.

## Operation 70
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: fingerprint slot gamma_spaced vs gamma_compact
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 9.

## Operation 71
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: origin Acme-Origin routing profile
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 10.

## Operation 72
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: destination Beta-Dest settlement lane
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 11.

## Operation 73
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: beneficiary label string with whitespace normalization
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 12.

## Operation 74
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: amount minor units int64
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 13.

## Operation 75
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: amount major_alias scaled field
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 14.

## Operation 76
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: fingerprint slot gamma_spaced vs gamma_compact
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 15.

## Operation 77
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: origin Acme-Origin routing profile
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 16.

## Operation 78
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: destination Beta-Dest settlement lane
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 17.

## Operation 79
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: beneficiary label string with whitespace normalization
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 18.

## Operation 80
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: amount minor units int64
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 19.

## Operation 81
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: amount major_alias scaled field
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 20.

## Operation 82
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: fingerprint slot gamma_spaced vs gamma_compact
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 21.

## Operation 83
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: origin Acme-Origin routing profile
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 22.

## Operation 84
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: destination Beta-Dest settlement lane
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 23.

## Operation 85
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: beneficiary label string with whitespace normalization
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 24.

## Operation 86
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: amount minor units int64
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 25.

## Operation 87
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: amount major_alias scaled field
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 26.

## Operation 88
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: fingerprint slot gamma_spaced vs gamma_compact
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 27.

## Operation 89
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: origin Acme-Origin routing profile
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 28.

## Operation 90
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: destination Beta-Dest settlement lane
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 29.

## Operation 91
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: beneficiary label string with whitespace normalization
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 30.

## Operation 92
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: amount minor units int64
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 31.

## Operation 93
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: amount major_alias scaled field
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 32.

## Operation 94
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: fingerprint slot gamma_spaced vs gamma_compact
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 33.

## Operation 95
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: origin Acme-Origin routing profile
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 34.

## Operation 96
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: destination Beta-Dest settlement lane
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 35.

## Operation 97
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: beneficiary label string with whitespace normalization
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 36.

## Operation 98
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: amount minor units int64
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 37.

## Operation 99
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: amount major_alias scaled field
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 38.

## Operation 100
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: fingerprint slot gamma_spaced vs gamma_compact
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 39.

## Operation 101
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: origin Acme-Origin routing profile
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 40.

## Operation 102
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: destination Beta-Dest settlement lane
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 41.

## Operation 103
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: beneficiary label string with whitespace normalization
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 42.

## Operation 104
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: amount minor units int64
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 43.

## Operation 105
- method: `POST`
- path: `/v1/transfers/probe`
- required header: `Idempotency-Key`
- success code: 202
- response header: Retry-After delta-seconds on 429
- schema note: amount major_alias scaled field
- narrative: acceptance anchor timestamp; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 44.

## Operation 106
- method: `POST`
- path: `/v1/transfers/commit`
- required header: `Idempotency-Key`
- success code: 200
- response header: Retry-After HTTP-date on 503
- schema note: fingerprint slot gamma_spaced vs gamma_compact
- narrative: settlement confirmation; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 45.

## Operation 107
- method: `GET`
- path: `/v1/transfers/{id}`
- required header: `none`
- success code: 200
- response header: X-RateLimit-Remaining throttle staircase
- schema note: origin Acme-Origin routing profile
- narrative: transfer status poll; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 46.

## Operation 108
- method: `POST`
- path: `/v1/transfers`
- required header: `Idempotency-Key`
- success code: 200
- response header: X-Meridian-Anchor acceptance clock
- schema note: destination Beta-Dest settlement lane
- narrative: single-phase settlement; callers parse mixed Retry-After formats and scope idempotency to fingerprint slot 47.

## Volume 04 cross-reference

PDF extract references superseded one-hour TTL language in volume 04 appendix; integrators MUST consult `/app/docs/meridian_precedence.md` for the 24-hour reuse window.
