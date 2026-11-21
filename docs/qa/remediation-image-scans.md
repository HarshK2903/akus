# Local release image scans

Trivy 0.76.2. Advisory database updated 2026-11-21T13:02:47.203212637Z. Counts include fixed and unfixed package matches and count shared layers per delivered image. The JSON preserves every reported advisory ID, package version, available fixed version, target and severity source. Raw report SHA-256 values identify the privately retained originals. [Machine-readable results](remediation-image-scans.json)

| Service | Local image SHA-256 | Critical | High | Medium | Low | Unknown |
|---|---|---:|---:|---:|---:|---:|
| db | `ac95673db6d9bc41e9b1d3add97b14a9fdeda950a0c0ceebcb6338f8f0653d00` | 1 | 125 | 171 | 170 | 17 |
| api | `c7005abe589a1a4f82c59d0b377a1c34b30d14f53772debc7c4fc380b4943f60` | 0 | 50 | 97 | 78 | 7 |
| worker | `7722e5ff393b0a14ab4fe9e475a918afb1b471069eed00646eb316b0cfe06654` | 0 | 50 | 97 | 78 | 7 |
| migrate | `d1f38a28e7c438c7294119fec55a16cb49bc66d69b3d626d9c2d4575e4991efa` | 0 | 50 | 97 | 78 | 7 |
| web | `9cbd4ed4bd2862bd235aaef6b4f9c4fef78cdf4501af743900e6543b9ba4c417` | 0 | 1 | 2 | 0 | 0 |
| proxy | `947cda3e1551b5c6d3919ed93021a8a60bbaa30fa60ca263e249daaf52fc639e` | 0 | 1 | 2 | 0 | 0 |
| clamd | `be57f40ea3fa45c96fd930908239ce2dd091ecd158dee40de4f67a1d3b1a2517` | 0 | 0 | 0 | 0 | 0 |

The database image initially matched both CVE-2025-68121 and CVE-2026-6653. Trivy now reports the latter against Debian libxml2 with NVD severity. See the supplier disposition and owner actions in the [remediation report](POST_AUDIT_REMEDIATION_REPORT.md).

To repeat, build the named Compose images, update the Trivy advisory database and record its metadata. Run the following once per service against its built image, including the scanner overlay. A CLI exit of zero with the default reporting command means the scan completed. Inspect the reported findings for the release decision.

```sh
trivy image --image-src docker --scanners vuln --format json --output "$report" "akus-local-$service"
```
