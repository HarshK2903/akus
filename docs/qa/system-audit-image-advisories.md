# Release image advisory scan

Trivy 0.76.2 with advisory database updated 2026-11-21T07:02:51.626719824Z. Each Docker image was exported locally and scanned offline for Debian/Alpine OS and language packages. Each row counts package/advisory matches as reported. Shared layers repeat across images. A fixed library version can exist even when the upstream compiled binary has no patched release. These counts do not establish reachability.

| Image | Revision | Image ID | Critical | High | Medium | Low | Unknown | Matches with a listed fix |
|---|---|---|---:|---:|---:|---:|---:|---:|
| api | Before | sha256:2919c113185f | 0 | 56 | 100 | 79 | 7 | 10 |
| api | After | sha256:34c195b34a1c | 0 | 50 | 97 | 78 | 7 | 0 |
| worker | Before | sha256:ff97f7888fe9 | 0 | 56 | 100 | 79 | 7 | 10 |
| worker | After | sha256:34a479ebb48a | 0 | 50 | 97 | 78 | 7 | 0 |
| migrate | Before | sha256:31877cc0eb52 | 0 | 56 | 100 | 79 | 7 | 10 |
| migrate | After | sha256:8d91cd6cd777 | 0 | 50 | 97 | 78 | 7 | 0 |
| web | Before | sha256:81989e790d85 | 0 | 2 | 14 | 4 | 1 | 18 |
| web | After | sha256:6d5245b7c9c7 | 0 | 2 | 7 | 0 | 1 | 7 |
| proxy | Before | sha256:5813f7eb9b94 | 0 | 2 | 14 | 4 | 1 | 18 |
| proxy | After | sha256:832e6a97be44 | 0 | 2 | 7 | 0 | 1 | 7 |
| db | Before | sha256:6b7038c60456 | 2 | 151 | 204 | 173 | 17 | 64 |
| db | After | sha256:7709d9e3d641 | 2 | 150 | 202 | 173 | 17 | 61 |

## Outstanding high and critical package advisories

| Advisory | Package | Installed | Listed fix | Severity | Ecosystem | Images |
|---|---|---|---|---|---|---|
| CVE-2025-68121 | stdlib | v1.24.6 | 1.24.13, 1.25.7, 1.26.0-rc.3 | CRITICAL | gobinary | db |
| CVE-2026-6653 | libxml2 | 2.12.7+dfsg+really2.9.14-2.1+deb13u3 | No vendor fix listed | CRITICAL | debian | db |
| CVE-2025-61726 | stdlib | v1.24.6 | 1.24.12, 1.25.6 | HIGH | gobinary | db |
| CVE-2025-61729 | stdlib | v1.24.6 | 1.24.11, 1.25.5 | HIGH | gobinary | db |
| CVE-2025-69720 | libncursesw6 | 6.5+20250216-2 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2025-69720 | libtinfo6 | 6.5+20250216-2 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2025-69720 | ncurses-base | 6.5+20250216-2 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2025-69720 | ncurses-bin | 6.5+20250216-2 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-107364 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-107364 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-107364 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-107364 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-111943 | stdlib | v1.24.6 | 1.26.10, 1.27.3 | HIGH | gobinary | db |
| CVE-2026-112315 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112315 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112315 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112315 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112316 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112316 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112316 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112316 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112317 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112317 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112317 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112317 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112318 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112318 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112318 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112318 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112319 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112319 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112319 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112319 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112320 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112320 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112320 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112320 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112321 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112321 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112321 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112321 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112322 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112322 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112322 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112322 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112323 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112323 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112323 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-112323 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-116587 | github.com/go-jose/go-jose/v3 | v3.0.5 | No vendor fix listed | HIGH | gobinary | proxy, web |
| CVE-2026-118380 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-118380 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-118380 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-118380 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-119079 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-119079 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-119079 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-119079 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-119373 | libsqlite3-0 | 3.46.1-7+deb13u2 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-119374 | libsqlite3-0 | 3.46.1-7+deb13u2 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-119379 | libsqlite3-0 | 3.46.1-7+deb13u2 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-124709 | libssl3t64 | 3.5.7-1~deb13u3 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-124709 | openssl | 3.5.7-1~deb13u3 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-124709 | openssl-provider-legacy | 3.5.7-1~deb13u3 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-16742 | libsystemd-shared | 257.13-1~deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-16742 | libsystemd0 | 257.13-1~deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-16742 | libudev1 | 257.13-1~deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-16742 | systemd | 257.13-1~deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-24882 | dirmngr | 2.4.7-21+deb13u1+b5 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-24882 | gnupg | 2.4.7-21+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-24882 | gnupg-l10n | 2.4.7-21+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-24882 | gpg | 2.4.7-21+deb13u1+b5 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-24882 | gpg-agent | 2.4.7-21+deb13u1+b5 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-24882 | gpgconf | 2.4.7-21+deb13u1+b5 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-24882 | gpgsm | 2.4.7-21+deb13u1+b5 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-25679 | stdlib | v1.24.6 | 1.25.8, 1.26.1 | HIGH | gobinary | db |
| CVE-2026-27145 | stdlib | v1.24.6 | 1.25.11, 1.26.4 | HIGH | gobinary | db |
| CVE-2026-32280 | stdlib | v1.24.6 | 1.25.9, 1.26.2 | HIGH | gobinary | db |
| CVE-2026-32281 | stdlib | v1.24.6 | 1.25.9, 1.26.2 | HIGH | gobinary | db |
| CVE-2026-32283 | stdlib | v1.24.6 | 1.25.9, 1.26.2 | HIGH | gobinary | db |
| CVE-2026-33811 | stdlib | v1.24.6 | 1.25.10, 1.26.3 | HIGH | gobinary | db |
| CVE-2026-33814 | stdlib | v1.24.6 | 1.25.10, 1.26.3 | HIGH | gobinary | db |
| CVE-2026-33818 | stdlib | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 | HIGH | gobinary | db |
| CVE-2026-39820 | stdlib | v1.24.6 | 1.25.10, 1.26.3 | HIGH | gobinary | db |
| CVE-2026-39821 | stdlib | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 | HIGH | gobinary | db |
| CVE-2026-39822 | stdlib | v1.24.6 | 1.25.12, 1.26.5, 1.27.0-rc.2 | HIGH | gobinary | db |
| CVE-2026-39836 | stdlib | v1.24.6 | 1.25.10, 1.26.3 | HIGH | gobinary | db |
| CVE-2026-42499 | stdlib | v1.24.6 | 1.25.10, 1.26.3 | HIGH | gobinary | db |
| CVE-2026-42504 | stdlib | v1.24.6 | 1.25.11, 1.26.4 | HIGH | gobinary | db |
| CVE-2026-54369 | libacl1 | 2.3.2-2+b1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-56853 | stdlib | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 | HIGH | gobinary | db |
| CVE-2026-56858 | stdlib | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 | HIGH | gobinary | db |
| CVE-2026-56859 | stdlib | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 | HIGH | gobinary | db |
| CVE-2026-56860 | stdlib | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 | HIGH | gobinary | db |
| CVE-2026-56862 | stdlib | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 | HIGH | gobinary | db |
| CVE-2026-71199 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-71199 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-71199 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-71199 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-71200 | libgssapi-krb5-2 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-71200 | libk5crypto3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-71200 | libkrb5-3 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-71200 | libkrb5support0 | 1.21.3-5+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-74860 | libxml2 | 2.12.7+dfsg+really2.9.14-2.1+deb13u3 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-76642 | bsdutils | 1:2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-76642 | libblkid1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-76642 | liblastlog2-2 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-76642 | libmount1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-76642 | libsmartcols1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-76642 | libuuid1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-76642 | login | 1:4.16.0-2+really2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-76642 | mount | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-76642 | util-linux | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78408 | bsdutils | 1:2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78408 | libblkid1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78408 | liblastlog2-2 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78408 | libmount1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78408 | libsmartcols1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78408 | libuuid1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78408 | login | 1:4.16.0-2+really2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78408 | mount | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78408 | util-linux | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78409 | bsdutils | 1:2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78409 | libblkid1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78409 | liblastlog2-2 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78409 | libmount1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78409 | libsmartcols1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78409 | libuuid1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78409 | login | 1:4.16.0-2+really2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78409 | mount | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78409 | util-linux | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78410 | bsdutils | 1:2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78410 | libblkid1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78410 | liblastlog2-2 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78410 | libmount1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78410 | libsmartcols1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78410 | libuuid1 | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78410 | login | 1:4.16.0-2+really2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78410 | mount | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78410 | util-linux | 2.41.5-0+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-78661 | golang.org/x/net | v0.60.0 | 0.62.0 | HIGH | gobinary | proxy, web |
| CVE-2026-78667 | stdlib | v1.24.6 | 1.26.9, 1.27.2 | HIGH | gobinary | db |
| CVE-2026-78669 | stdlib | v1.24.6 | 1.26.9, 1.27.2 | HIGH | gobinary | db |
| CVE-2026-86138 | libxml2 | 2.12.7+dfsg+really2.9.14-2.1+deb13u3 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-86139 | libxml2 | 2.12.7+dfsg+really2.9.14-2.1+deb13u3 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-86140 | libxml2 | 2.12.7+dfsg+really2.9.14-2.1+deb13u3 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-86142 | libxml2 | 2.12.7+dfsg+really2.9.14-2.1+deb13u3 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-86143 | libxml2 | 2.12.7+dfsg+really2.9.14-2.1+deb13u3 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-86144 | libxml2 | 2.12.7+dfsg+really2.9.14-2.1+deb13u3 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-9538 | libperl5.40 | 5.40.1-6+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-9538 | perl | 5.40.1-6+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-9538 | perl-base | 5.40.1-6+deb13u1 | No vendor fix listed | HIGH | debian | api, db, migrate, worker |
| CVE-2026-9538 | perl-modules-5.40 | 5.40.1-6+deb13u1 | No vendor fix listed | HIGH | debian | db |
| CVE-2026-97031 | stdlib | v1.24.6 | 1.26.9, 1.27.2 | HIGH | gobinary | db |
