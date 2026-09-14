# GitHub Actions workflows

[`ci.yml`](ci.yml) runs ordinary checks on pull requests. Scheduled and manually
selected lanes add longer synthetic and scheduler checks. The
[test baseline](../../docs/design/TEST_BASELINE.md#validation-lanes) defines each
lane; a green workflow supports only the claims covered by those checks.
