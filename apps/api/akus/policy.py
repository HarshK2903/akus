"""Source-approved summaries; no domain policy decisions are executed in Phase 1."""

from akus.schemas import PolicyHelp

HELP = [
    PolicyHelp(
        id="A01-A04",
        title="Who participates and who reviews",
        status="CONFIRMED",
        summary="Faculty and DRC Head participate. Ordinary Faculty review goes DRC → HoD; a DRC Head's own application goes directly to HoD. HoD and Principal are exempt. DRC and HoD cannot overlap. Principal oversight is read-only by default.",
    ),
    PolicyHelp(
        id="V2.4",
        title="One approved primary topic",
        status="CONFIRMED",
        summary="The current department HoD approves one primary charging topic per canonical course. Provider categories remain visible. Applicants cannot choose another topic to find capacity.",
    ),
    PolicyHelp(
        id="A05-A08",
        title="Annual shared quota",
        status="CONFIRMED",
        summary="A published pool is shared by department, canonical topic and July–June academic year. Initial reservation uses the scheduled exam year. Missing mapping or published quota allows only draft/intake; successful submission must reserve atomically.",
    ),
    PolicyHelp(
        id="V2.3",
        title="Official cross-year rescheduling",
        status="CONFIRMED",
        summary="Verified rescheduling attempts an atomic transfer to a published destination-year pool with capacity. Failure retains the current counted seat and flags reconciliation. Original submission history is immutable.",
    ),
    PolicyHelp(
        id="Q35-Q38",
        title="Annual completion and subject Silver",
        status="CONFIRMED",
        summary="Actual verified exam date determines annual credit. One qualifying course of at least eight weeks or two distinct four-week courses in the same academic year may qualify with valid certificates. Subject Silver is a separate obligation.",
    ),
    PolicyHelp(
        id="P-NEW-11",
        title="Mapping changes and existing seats",
        status="POLICY_PENDING",
        summary="The effect of a revised primary topic on already counted applications is undecided. Do not move old reservations across topics or rewrite their snapshots.",
    ),
    PolicyHelp(
        id="P-51",
        title="One Silver certificate across subjects",
        status="POLICY_PENDING",
        summary="Second or subsequent subject credit from one certificate awaits an institutional decision. No automatic multi-subject credit is authorized.",
    ),
    PolicyHelp(
        id="P-NEW-04",
        title="Principal emerging-technology authority",
        status="POLICY_PENDING",
        summary="Special emerging-technology final approval authority remains unresolved. Oversight does not grant academic write permission.",
    ),
    PolicyHelp(
        id="P-NEW-05/06",
        title="Active cases during office transitions",
        status="POLICY_PENDING",
        summary="Preserve existing cases and history when Faculty moves to HoD or returns. Do not invent withdrawal, waiver or resumed obligation rules.",
    ),
    PolicyHelp(
        id="P-NEW-10",
        title="Permanently blocked quota transfers",
        status="POLICY_PENDING",
        summary="The final remedy and priority for indefinitely blocked transfers are undecided. Keep the current seat counted; do not promise priority or force cancellation.",
    ),
    PolicyHelp(
        id="P-63",
        title="External provider evidence",
        status="POLICY_PENDING",
        summary="AKUS approval does not enroll anyone on NPTEL. Course preview metadata cannot verify individual enrollment, examination attendance or certificate authenticity. This local environment has no provider connection.",
    ),
]
