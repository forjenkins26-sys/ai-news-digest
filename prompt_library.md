# Prompt Library — every prompt the daily email has sent

## 2026-11-26

### 1. AI Trust Calibration: 4 Advanced Prompt Engineering Tactics That Actually Work — dev.to #promptengineering
https://dev.to/473185670/ai-trust-calibration-4-advanced-prompt-engineering-tactics-that-actually-work-p36

```
Prompt 1: "Write a Python function to parse a CSV file and return a list of dictionaries."
Prompt 2: "Review this function for edge cases: empty CSV, missing columns, malformed data. List issues."
Prompt 3: "Fix the issues you identified. Handle empty CSV gracefully, validate columns, add error handling."
Prompt 4: "Refactor for readability. Add docstring, type hints, and a usage example."
```

**Why:** Iterative edge-case analysis is essential for QA engineers moving into LLM agent validation. It teaches systematic boundary testing for code generation.

**Your version:** Analyze my Playwright test suite execution log file at `./logs/test-results.json` for all test runs from the last 14 days with > 2 failures. Generate a Markdown table summarizing the failed test name, failure reason, missing edge case, and proposed fix. Save the output into `./reports/flaky_tests_analysis.md`. Do not refactor the original test files directly or execute any code.

**Drill:** Run this prompt in Claude Code against your recent Playwright execution logs to immediately generate a prioritized list of flaky test refactoring tasks.

### 2. Setup and Bootstrap a Flutter Development Environment — prompts.chat
https://prompts.chat/?q=Setup%20and%20Bootstrap%20a%20Flutter%20Development%20Environment

```
are an autonomous senior DevOps, Flutter, and Mobile Platform engineer.

Mission:
Provision a complete Flutter development environment AND bootstrap a new production-ready Flutter project.

Assumptions:
- Administrator/sudo privileges are available.
- Terminal access and internet connectivity exist.
- No prior development tools can be assumed.
- This is a local development machine, not a container.

Global Rules:
- Follow ONLY official documentation.
- Use stable versions only.
- Prefer reproducibility and clarity over cleverness.
- Do not ask questions unless progress is blocked.
- Log all actions and commands.

=== PHASE 1: SYSTEM SETUP ===

1. Detect operating system and system architecture.

2. Install Git using the official method.
   - Verify with `git --version`.

3. Install required system dependencies for Flutter.

4. Download and install Flutter SDK (stable channel).
   - Add Flutter to PATH persistently.
   - Verify with `flutter --version`.

5. Install platform tooling:
   - Android:
     - Android SDK and platform tools.
     - Accept all required licenses automatically.
   - iOS (macOS only):
     - Xcode and command line tools.
     - CocoaPods.

6. Run `flutter doctor`.
   - Automatically resolve all fixable issues.
   - Re-run until no blocking issues remain.

=== PHASE 2: PROJECT BOOTSTRAP ===

7. Create a new Flutter project:
   - Use `flutter create`.
   - Project name: `flutter_app`
   - Organization: `com.example`
   - Platforms: android, ios (if supported by OS)

8. Initialize a Git repository in the project root.
   - Create a `.gitignore` if missing.
   - Make an initial commit.

=== PHASE 3: PROJECT STRUCTURE & STANDARDS ===

9. Configure Flutter flavors:
   - dev
   - staging
   - prod
   - Set up separate app IDs / bundle identifiers per flavor.

10. Add linting and code quality:
    - Enable `flutter_lints`.
    - Add an `analysis_options.yaml` with recommended rules.

11. Project hygiene:
    - Enforce `flutter format`.
    - Run `flutter analyze` and fix issues if possible.

=== PHASE 4: CI FOUNDATION ===

12. Set up GitHub Actions:
    - Create `.github/workflows/flutter_ci.yaml`.
    - Steps:
      - Checkout code
      - Install Flutter (stable)
      - Run `flutter pub get`
      - Run `flutter analyze`
      - Run `flutter test`

=== PHASE 5: FINAL VERIFICATION ===

13. Build verification:
    - `flutter build apk` (Android)
    - `flutter build ios --no-codesign` (macOS only)

14. Final report:
    - Summarize installed tools and versions.
    - Confirm project structure.
    - Confirm CI configuration exists.

Termination Condition:
- Stop only when the environment is ready AND the Flutter project is fully bootstrapped.
- If a non-recoverable error occurs, explain it clearly and stop.
```

**Why:** Demonstrates structured step-by-step execution rules and strict environment setup logic, key for building resilient multi-step AI agents. It enforces defensive engineering principles.

**Your version:** Scan my local trading bot codebase at `./src/trading/` for all Python modules modified in the last 7 days. Create a setup checklist and dependency audit report in JSON format mapping each script to its required PyPI packages and env variables. Output the JSON to `./config/env_audit.json`. Do not install any packages, execute trading scripts, or modify shell config files.

**Drill:** Paste this into Claude Code while in your Python trading bot repo to verify your local environment configuration in under 5 minutes.

### 3. Machine Learning Experiment taste — prompts.chat
https://prompts.chat/?q=Machine%20Learning%20Experiment%20taste

```
# Machine Learning Experiment taste of an applied ML engineer
- Write the evaluation metric and a dumb baseline before training any real model. Confidence: 0.95
- Split data by time or by entity when leakage is possible, never with a random split by default. Confidence: 0.90
- Freeze the test set early and look at it only for final decisions, using a separate validation set for tuning. Confidence: 0.95
- Track every run with MLflow or Weights & Biases, logging config, metrics, code version and dataset version. Confidence: 0.90
- Keep experiment config in versioned YAML files loaded with Hydra or Pydantic, not in hardcoded constants. Confidence: 0.80
- Set and log random seeds for Python, NumPy and the framework, and report variance across several seeds. Confidence: 0.85
- Version datasets with DVC or immutable object storage paths so any result can be reproduced. Confidence: 0.80
- Prototype in notebooks but move reusable code into a tested Python package as soon as it is used twice. Confidence: 0.85
- Pin dependencies with a lock file and record the CUDA and driver versions with each run. Confidence: 0.75
- Inspect raw samples and label errors by hand before trusting any aggregate metric. Confidence: 0.90
- Prefer gradient boosted trees for tabular data and reach for deep learning only when they clearly fall short. Confidence: 0.80
- Use PyTorch with a thin training loop or Lightning instead of large custom frameworks. Confidence: 0.70
- Report metrics per slice such as region, device or class, not only a single global number. Confidence: 0.90
- Calibrate predicted probabilities when downstream code makes threshold decisions. Confidence: 0.75
- Tune hyperparameters with Optuna or a simple random search under a fixed compute budget. Confidence: 0.75
- Write unit tests for feature transforms and data loaders, and assert expected shapes and dtypes. Confidence: 0.85
- Validate input data with schema checks such as Pandera or Great Expectations before training. Confidence: 0.80
- Save the model together with its preprocessing pipeline as one artifact so training and serving cannot drift. Confidence: 0.90
- Compare a new model to the production model offline and then with a shadow or A/B rollout. Confidence: 0.85
- Monitor feature drift and prediction distributions after launch and alert on large shifts. Confidence: 0.80
- Write a short experiment note for every significant run with the hypothesis, the result and the next step. Confidence: 0.85
- Delete or archive failed branches of work instead of leaving dozens of half-finished notebooks. Confidence: 0.65
```

**Why:** Provides concrete evaluation and data-handling rules necessary for applied ML and trading bot development. It instills production-level ML discipline around tracking and data leakage.

**Your version:** Evaluate my trading strategy backtest logs in `./data/backtest_results.csv` filtering for all strategy runs executed over the last 30 days with a drawdown greater than 15%. Create a Markdown report detailing data leakage risk, evaluation metrics, and random seed stability recommendations. Save the file to `./docs/ml_eval_audit.md`. Do not re-run backtests, alter hyperparameter values, or modify historical data files.

**Drill:** Feed a recent backtest CSV from your trading scripts into Claude Code with this prompt to audit your model evaluation hygiene.

## 2026-11-27

### 1. Claude pushed and moved on. guard 0.4.21 can tell it the push broke CI. — dev.to #claude
https://dev.to/boxdawn/claude-pushed-and-moved-on-guard-0421-can-tell-it-the-push-broke-ci-29em

```
Boxdawn guard: CI newly failed on the commit you just pushed (boxdawn/ci-notice-demo main @ 6f089da). Workflow 'CI': its previous run passed.
- test → Run tests
 test_calc.py:9 test_total assert 3.6 == 4.0 + where 3.6 = total([1.5, 2.5])
Check whether your change caused it: gh run view 45972956440 --repo boxdawn/ci-notice-demo --log-failed (it may also be unrelated to the change).
```

**Why:** It uses CLI integration to fetch raw test execution data and isolates failures with precision. It demonstrates how to orchestrate AI agents for automated CI/CD test triage.

**Your version:** Fetch the logs for the last 5 failed CI pipeline runs in my Playwright JS repository using `gh run list --limit 5` and `gh run view <id> --log-failed`. Extract the failed test file names, error stack traces, and associated Jira issue keys from recent commits into a Markdown table with columns: Run ID, Test File, Error Summary, Jira Ticket, and Root Cause Hypothesis. Output the result to stdout. Do not rerun the pipeline, comment on Jira, or edit any code.

**Drill:** Open Claude Code in your Playwright repository and run this prompt to instantly summarize your team's top CI test failures from the past week.

### 2. Find packages that depend on apps — prompts.chat
https://prompts.chat/?q=Find%20packages%20that%20depend%20on%20apps

```
Audit the monorepo for shared packages (under packages/) that depend on an app or service, either directly or transitively.

1. For every package.json under packages/, list the workspace dependencies that point to apps/*, services, or other non-package workspaces.
2. Search source for imports of app modules. Use `git grep` with a pathspec rather than recursive grep. Search for both package-name imports and relative paths that escape the package.
3. For each hit, record the importing file, the imported symbol, and whether it is used as a type or at runtime.
4. Group the hits by root cause:
    - a schema or generated types
    - test support
    - constants or headers
    - real logic
5. Rank the groups by how many consumers they unblock and how much build-graph weight they remove.

Measure the improvement by comparing `turbo run build --dry=json --filter=<pkg>` before and after. Count tasks and dependency edges. Report numbers, not estimates. Do not change any code.
```

**Why:** It demonstrates programmatic codebase auditing using exact CLI commands (`git grep`) and strict numeric metric validation. This teaches AI engineers how to enforce rigid structural limits on agent code modifications.

**Your version:** Audit my Python trading-bot repository for strategy modules under `strategies/` that import order-execution modules. Use `git grep` to find imports, group findings into 4 categories (types, backtest mocks, risk params, execution logic), and count the total dependency edges. Output a Markdown table with columns: Strategy File, Imported Module, Category, Consumer Count, Impact Rank. Print the table to terminal and do not modify any Python files.

**Drill:** Execute this prompt in Claude Code against your trading bot repo to measure structural coupling before building your next automated strategy.

### 3. Find convenience re-exports — prompts.chat
https://prompts.chat/?q=Find%20convenience%20re-exports

```
Find convenience re-exports in <package>: `export * from` and `export { X } from` statements that forward symbols owned by another workspace package.

For each re-export:

- Name the owning package. Say whether the re-export forces consumers to install or build that package when they would not otherwise need it.
- Count consumers with `git grep` and note which ones already depend on the owning package.
- Classify it:
  (a) Type-only. Usually keep it, because it has no runtime cost.
  (b) A runtime value with few consumers. Remove it and point consumers at the owner.
  (c) Real code that only looks like a re-export. Keep it.
  (d) Many consumers. Defer it to its own PR.

Produce a table with these columns: symbol, owner, consumers, classification, recommended action. Do not edit any files yet.
```

**Why:** It forces the AI to use shell tools (`git grep`) and enforce a rigid tabular schema while strictly prohibiting file mutations. It models how top AI engineers write static-analysis inspection prompts.

**Your version:** Scan my Playwright test framework for utility files under `utils/` that re-export methods from core libraries. Use `git grep` across the last 30 test specs to count consumers for each re-export, classify them into 4 types (Type-only, Low-usage runtime, Native wrapper, High-usage core), and produce a 5-column Markdown table with columns: Method, Source File, Consumer Count, Classification, Action. Output to stdout and do not edit any files.

**Drill:** Run this prompt in your QA test repo using Claude Code to pinpoint dead utility wrappers that slow down test script maintenance.
