# O10 initial hosted result — false peak-RSS comparator, instrument correction

Date: 2026-10-24
Evidence status: **INITIAL MEMORY MEASUREMENTS INVALID / RETAINED AS NEGATIVE**, no product credit.
First exact-head O10 court: `87f43842672e8750b1a0bf591e60274c5d050019`, [run 40074088123](https://github.com/FCMO-AI/.CMPCT/actions/runs/40074088123), artifact `12552009170` (SHA-256 ZIP `7ba7cae67b737229b8baca69b9f7bded1929b9f9ec30cefb8743cdac32e189df`).

## Outcome of the original preregistered court

Both unchanged O7 eager-serial and O10 streamed readers reconstructed exact source files on four cohorts (4, 16, 32 MiB high-entropy output plus 512 structured members), with six repetitions per arm/cohort and a passing existing-symlink outside-canary refusal in O10. All four cohorts reported **exactly the same `ru_maxrss` for both arms and every repetition**: 46,572 KiB, 108,112 KiB, 190,016 KiB, 190,016 KiB (in cohort order). Recorded wall medians (eager vs stream): 3.2759 / 1.8741 ms at 4 MiB; 12.0096 / 5.7493 ms at 16 MiB; 24.2429 / 11.2372 ms at 32 MiB; 129.4719 / 113.5440 ms on 512 structured members.

**These are actual timings of two different test clients, not a native Reader speedup.** The identical and monotone RSS values across fresh binaries were initially incompatible with a meaningful memory decision.

## Independent process-accounting falsifier (before O10b)

A local Linux experiment compiled a tiny independent C program printing both `getrusage(RUSAGE_SELF).ru_maxrss` and `/proc/self/status:VmHWM`. An ordinary Python parent first launched it, then touched ~192 MiB of anonymous memory, then launched it again. The second **newly exec'd tiny C program** reported `ru_maxrss=291,724 KiB` while its own fresh `VmHWM=644 KiB` (prior run `VmHWM=640 KiB`). Thus Linux getrusage maxrss can carry the Python spawning process's high-water mark across fork/exec, whereas post-exec `VmHWM` represents the C process memory mapping.

This is a **harness accounting failure**: the first O10 run is scientifically valid for exact output and timing, but it **cannot decide the claimed bounded-memory advantage**. Do not state an RSS win or loss from those numbers. It is not a CMPCT product bug.

## Corrected independent route O10b

The test-only forced include `tests/native_pack_process_rss_o10.h` replaces only the two C process evidence clients' final `getrusage` observation with the Linux post-exec `/proc/self/status:VmHWM`. It fails closed if the kernel value is unavailable. Both C programs, data, native Reader and ordinary timing semantics otherwise remain the same. The original O7 code stays source-identical; the instrumentation is applied by identical compiler flags. The existing O10 prospective question, source archives, ABBA corpus and hash checks remain unchanged.

This is an explicit **post-result measurement repair**; the O10 original preregistration and original raw result are preserved, not silently rewritten. O10b must run on its own exact head; no promotion is authorized before that result, and even a successful positive would establish only Linux evidence-client economics, not shipping full-tree semantics.

## Transferable prospective lesson
A child process launched from a memory-intensive Python benchmark driver can inherit a Linux `getrusage` high-water mark despite `exec`. A benchmarking protocol should compare **post-exec per-process mm-specific peak memory** (or use an independently isolated measurement process), not trust raw `ru_maxrss` emitted by an exec'd child without verifying its accounting provenance. This can be checked cheaply before the first expensive benchmark.

No change to quality thresholds, benchmark semantics, canonical product code, format, frozen science or Discovery Engine policy is justified by this single process-measurement failure.
