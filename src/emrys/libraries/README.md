# Internal libraries

Libraries contain neutral mechanics proven across named consumers; owner
arguments, check rosters, transactions, scientific policy, and evidence meaning
remain local. Approved consumers and dependency direction are fixed in
[`SOURCE_TOPOLOGY.md`](../contracts/SOURCE_TOPOLOGY.md).

The package includes validation publication, BAM/BED/STAR/orientation parsers,
evidence and quality parsers, reference-contig admission, source/artifact-root
authority, controlled child environments and GATK invocation, installed-package
identity, application logging, and shared R input mechanics. A helper's
presence does not authorize a new consumer or turn it into a generic utility.

Keep the first use local. Extract a shared seam only after equivalent behavior
is demonstrated across consumers and protected by its own API and tests.

## Shell publication cleanup

`file_checks.sh::cleanup_no_clobber_outputs` owns the equivalent rollback,
staging cleanup, and lock release for RSeQC, BAM QC, and duplicate marking.
Each caller supplies its fixed output labels and staging/final path pairs;
it arms publication before the first link, then clears that state only after
all successful-publication anchors are removed. Native execution and output
validation stay with the producer.

On failed publication, cleanup checks every output pair, including the link
whose helper did not return successfully. It removes only finals proved to
share their staging inode. A missing or replaced final retains all staging
anchors and the owned lock; provably owned sibling finals can still be removed.
After resolved rollback, staging cleanup attempts every unlink; a failed
unlink retains the remaining residue and lock, without masking the original
exit status. Staging-unlink diagnostics share one label/path format.

Earlier per-output flags were set after the link helper returned. Local
production-script probes showed that TERM after linking, or replacement before
the helper's inode check, could leave the final while deleting staging and the
lock. The new cleanup removes those flags across all three applicable owners.
The real second-link disappearance regression protects the multi-output case;
other ownership and tool-failure checks remain in the existing suites.

Canonical BAM and split-N-cigar retain distinct scratch/commit cleanup;
scientific context additionally owns backups, directory syncing, and a
different lock record. They are not equivalent consumers of this cleanup.
The lower-level publication and inode-ownership helpers are unchanged.
